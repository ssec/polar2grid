#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2012-2015 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
#     input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    December 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu

"""
The HDF5 writer creates HDF5 files with data arrays from satpy.Scene.

All selected products are in one file.
Products are subgrouped together under a parent HDF5 data group
based on the data product projection/remapping (parent projection group).
Each parent projection group contains attributes describing the projection.
Product subgroups contain attributes of the data including timestamps,
sensor and platform information.
See the command line arguments for HDF5 compression options, the flag to include
longitude and latitude data in the file, instructions for output-filename
patterns, and product selection.
"""
from __future__ import annotations
from typing import TextIO

import os
import logging

import h5py
import numpy as np
import xarray as xr

from itertools import groupby
from satpy.writers import Writer
from satpy.writers import split_results, compute_writer_results

from pyresample.geometry import SwathDefinition
from polar2grid.utils.legacy_compat import convert_p2g_pattern_to_satpy
from polar2grid.writers.geotiff import NUMPY_DTYPE_STRS, NumpyDtypeList, str_to_dtype

LOG = logging.getLogger(__name__)

# reader_name -> filename
DEFAULT_OUTPUT_FILENAMES = {None: "{platform_name}_{sensor}_{start_time:%Y%m%d_%H%M%S}.h5"}


def all_equal(iterable: list[str]) -> bool:
    """Return True if all the elements are equal to each other."""
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


class FakeHDF5:
    """Use fake hdf class to create targets for da.store and delayed sources."""

    def __init__(self, output_filename: str, var_name: str):
        """Initialize filename target with appropriate var_name for the data."""
        self.output_filename = output_filename
        self.var_name = var_name

    def __setitem__(self, write_slice, data):
        """Write data arrays to HDF5 file either delayed or not."""
        with h5py.File(self.output_filename, mode="a") as fh:
            fh[self.var_name][write_slice] = data


class HDF5Writer(Writer):
    """Writer for hdf5 files."""

    def __init__(self, **kwargs):
        """Init the writer."""
        super(HDF5Writer, self).__init__(**kwargs)

        if self.filename_parser is None:
            raise RuntimeError("No filename pattern or specific filename provided")

    def _output_file_kwargs(self, dataset, dtype):
        """Get file keywords from data for output_pattern."""
        if isinstance(dataset, list):
            dataset = dataset[0]
            area = dataset[0].attrs["area"]
            d_dtype = dataset[0].dtype
        else:
            area = dataset.attrs["area"]
            d_dtype = dataset.dtype

        dtype = d_dtype if dtype is None else dtype

        args = dataset.attrs
        args["grid_name"] = "native" if isinstance(area, SwathDefinition) else area.area_id
        args["rows"], args["columns"] = area.shape
        args["data_type"] = dtype

        return args

    def iter_by_area(self, datasets: list[xr.DataArray]):
        """Generate datasets grouped by Area.

        Args:
            datasets (list[xr.DataArray]):  A list of dataArray objects stored in Scene.
        Returns:
            dictionary:  a dictionary of {AreaDef:  list[xr.DataArray]}
        """
        datasets_by_area = {}
        for ds in datasets:
            a = ds.attrs.get("area")
            datasets_by_area.setdefault(a, []).append(ds)
        return datasets_by_area.items()

    @staticmethod
    def open_hdf5_filehandle(output_filename: str, append: bool = True):
        """Open a HDF5 file handle."""
        if os.path.isfile(output_filename):
            if append:
                LOG.info("Appending to existing file: %s", output_filename)
                mode = "a"
            else:
                LOG.warning("HDF5 file already exists, will overwrite/truncate: %s", output_filename)
                mode = "w"
        else:
            LOG.info("Creating HDF5 file: %s", output_filename)
            mode = "w"

        h5_fh = h5py.File(output_filename, mode)
        return h5_fh

    @staticmethod
    def create_proj_group(filename: str, parent: TextIO, area_def):
        """Create the top level group from projection information."""
        projection_name = (area_def.area_id).replace(" ", "_")
        # if top group alrady made, return.
        if projection_name in parent:
            return projection_name

        # create top group for first time
        group = parent.create_group(projection_name)
        # add attributes from grid_defintion.
        if isinstance(area_def, SwathDefinition):
            group.attrs["height"], group.attrs["width"] = area_def.shape
            group.attrs["description"] = "No projection: native format"
        else:
            for a in ["height", "width", "origin_x", "origin_y"]:
                ds_attr = getattr(area_def, a, None)
                if ds_attr is None:
                    pass
                else:
                    group.attrs[a] = ds_attr
            group.attrs["proj4_string"] = area_def.proj_str
            group.attrs["cell_height"] = area_def.pixel_size_y
            group.attrs["cell_width"] = area_def.pixel_size_x

        return projection_name

    def write_geolocation(
        self, fh, fname: str, parent: str, area_def, dtype: np.dtype, append: bool, compression, chunks: tuple[int, int]
    ) -> tuple[list, list[FakeHDF5]]:
        """Delayed Geolocation Data write."""
        msg = ("Adding geolocation 'longitude' and " "'latitude' datasets for grid %s", parent)
        LOG.info(msg)
        lon_data, lat_data = area_def.get_lonlats(chunks=chunks)

        dtype = lon_data.dtype if dtype is None else dtype
        data_shape = lon_data.shape

        lon_grp = "{}/longitude".format(parent)
        lat_grp = "{}/latitude".format(parent)

        if append:
            for var_name in [lon_grp, lat_grp]:
                if var_name in fh:
                    LOG.warning("Product %s already exists in hdf5 group, will delete existing dataset", var_name)
                    del fh[var_name]

        lon_dataset = FakeHDF5(fname, lon_grp)
        lat_dataset = FakeHDF5(fname, lat_grp)
        fh.create_dataset(lon_grp, shape=data_shape, dtype=dtype, compression=compression)
        fh.create_dataset(lat_grp, shape=data_shape, dtype=dtype, compression=compression)

        return [lon_data, lat_data], [lon_dataset, lat_dataset]

    @staticmethod
    def create_variable(
        filename: str, hdf_fh, hdf_subgroup: str, data_arr: xr.DataArray, dtype: np.dtype, compression: bool
    ):
        """Create a hdf5 data variable and attributes for the variable."""
        ds_attrs = data_arr.attrs

        d_dtype = data_arr.dtype if dtype is None else dtype

        if hdf_subgroup in hdf_fh:
            LOG.warning("Product %s already in hdf5 group," "will delete existing dataset", hdf_subgroup)
            del hdf_fh[hdf_subgroup]

        try:
            dset = hdf_fh.create_dataset(hdf_subgroup, shape=data_arr.shape, dtype=d_dtype, compression=compression)
        except ValueError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        dset.attrs["satellite"] = ds_attrs["platform_name"]
        dset.attrs["instrument"] = ds_attrs["sensor"]
        dset.attrs["begin_time"] = ds_attrs["start_time"].isoformat()
        dset.attrs["end_time"] = ds_attrs["end_time"].isoformat()

    def save_datasets(
        self,
        dataset: list[xr.DataArray],
        filename=None,
        dtype=None,
        append=True,
        compute=True,
        chunks=None,
        **kwargs,
    ):
        """Save hdf5 datasets."""
        compression = kwargs.pop("compression", None) if "compression" in kwargs else None
        if compression == "none":
            compression = None

        add_geolocation = kwargs.pop("add_geolocation") if "add_geolocation" in kwargs else False

        # will this be written to one or multiple files?
        output_names = []

        for dataset_id in dataset:
            file_attrs = self._output_file_kwargs(dataset_id, dtype)
            out_filename = filename or self.get_filename(**file_attrs)
            output_names.append(out_filename)

        filename = output_names[0]
        if not all_equal(output_names):
            LOG.warning("Writing to {}".format(filename))

        hdf5_fh = self.open_hdf5_filehandle(filename, append=append)

        datasets_by_area = self.iter_by_area(dataset)
        # Initialize source/targets at start of each new AREA grouping.
        dsets = []
        targets = []

        for area, data_arrs in datasets_by_area:
            # open hdf5 file handle, check if group already exists.
            parent_group = self.create_proj_group(filename, hdf5_fh, area)

            if add_geolocation:
                chunks = data_arrs[0].chunks
                geo_sets, fnames = self.write_geolocation(
                    hdf5_fh, filename, parent_group, area, dtype, append, compression, chunks
                )
                dsets.append(geo_sets)
                targets.append(fnames)

            for data_arr in data_arrs:
                hdf_subgroup = "{}/{}".format(parent_group, data_arr.attrs["name"])

                file_var = FakeHDF5(filename, hdf_subgroup)
                self.create_variable(filename, hdf5_fh, hdf_subgroup, data_arr, dtype, compression)

                dsets.append(data_arr.data)
                targets.append(file_var)

        results = (dsets, targets)
        if compute:
            LOG.info("Computing and writing results...")
            return compute_writer_results([results])

        targets, sources, delayeds = split_results([results])
        if delayeds:
            # This writer had only delayed writes
            return delayeds
        else:
            return targets, sources


def add_writer_argument_groups(parser, group=None):
    """Create writer argument groups."""
    if group is None:
        group = parser.add_argument_group(title="hdf5 Writer")
    group.add_argument(
        "--output-filename",
        dest="filename",
        type=convert_p2g_pattern_to_satpy,
        help="Custom file pattern to save dataset to",
    )
    group.add_argument(
        "--dtype",
        choices=NumpyDtypeList(NUMPY_DTYPE_STRS),
        type=str_to_dtype,
        help="Data type of the output file (8-bit unsigned " "integer by default - uint8)",
    )
    group.add_argument("--compress", default="LZW", help="File compression algorithm (DEFLATE, LZW, NONE, etc)")
    group.add_argument(
        "--add-geolocation",
        action="store_true",
        help="Add 'longitude' and 'latitude' datasets for each grid",
    )

    group.add_argument(
        "--no-append",
        dest="append",
        action="store_false",
        help="Don't append to the hdf5 file if it already exists (otherwise may overwrite data)",
    )

    return group, None
