from __future__ import annotations
from typing import TextIO

import os
import sys
import logging

import satpy
import h5py
import numpy as np
import xarray as xr
import dask.array as da

from itertools import groupby
from datetime import datetime as datetime
from satpy.dataset import DataID
from satpy.writers import ImageWriter

from trollsift import Parser

from pyresample.geometry import SwathDefinition
from polar2grid.utils.legacy_compat import convert_p2g_pattern_to_satpy
from polar2grid.writers.geotiff import NUMPY_DTYPE_STRS, NumpyDtypeList, str_to_dtype, int_or_float

from polar2grid.core.script_utils import setup_logging, rename_log_file, create_exc_handler

USE_POLAR2GRID_DEFAULTS = bool(int(os.environ.setdefault("USE_POLAR2GRID_DEFAULTS", "1")))

LOG = logging.getLogger(__name__)

# reader_name -> filename
DEFAULT_OUTPUT_FILENAMES = {None: "{platform_name}_{sensor}_{start_time:%Y%m%d_%H%M%S}.h5"}


def all_equal(iterable: list[str]) -> bool:
    "Returns True if all the elements are equal to each other"
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


class FakeHDF5:
    def __init__(self, fh : TextIO[IO[AnyStr]], output_filename: str, var_name: str, compression: bool):
        self.fh = fh
        self.output_filename = output_filename
        self.var_name = var_name
        self.compression = compression

    def check_variable(self, data: da.array, dtype: np.dtype, append: bool):
        if append:
            if self.var_name in self.fh:
                LOG.warning("Product %s already exists in hdf5 group, will delete existing dataset", self.var_name)
                del self.fh[self.var_name]
        self.fh.create_dataset(self.var_name, shape=data.shape, dtype=dtype, compression=self.compression)

    def __setitem__(self, write_slice, data):
        self.fh[self.var_name][write_slice] = data


class hdf5writer(ImageWriter):
    """Writer for hdf5 files."""

    def __init__(self, **kwargs):
        """Init the writer."""
        super(hdf5writer, self).__init__(**kwargs)

    def _output_file_kwargs(self, dataset, dtype):
        """Get file keywords from data for output_pattern."""
        if isinstance(dataset, list):
            dataset = dataset[0]
            area = dataset[0].attrs["area"]
        else:
            area = dataset.attrs["area"]

        args = dataset.attrs
        args["grid_name"] = "native" if isinstance(area, SwathDefinition) else area.area_id
        args["rows"], args["columns"] = area.shape
        args["data_type"] = dtype

        return args

    def iter_by_area(self, datasets: list[xr.DataArray]):
        """Generate datasets grouped by Area.
        :return: list of (area_obj, list of dataset objects)
        """
        datasets_by_area = {}
        for ds in datasets:
            a = ds.attrs.get("area")
            datasets_by_area.setdefault(a, []).append(ds)
        return datasets_by_area.items()

    def get_filename(self, **kwargs) -> str:
        """Create a filename for saving output data.

        Args:
            kwargs (dict): Attributes and other metadata to use for formatting
                the previously provided `filename`.

        """
        if self.filename_parser is None:
            raise RuntimeError("No filename pattern or specific filename provided")
        self.filename_parser = Parser(convert_p2g_pattern_to_satpy(self.filename_parser.fmt))
        output_filename = self.filename_parser.compose(kwargs)
        dirname = os.path.dirname(output_filename)
        if dirname and not os.path.isdir(dirname):
            LOG.info("Creating output directory: {}".format(dirname))
            os.makedirs(dirname)
        return output_filename

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
    def create_proj_group(filename: str, parent : TextIO, area_def):
        """Create the top level group from projection information."""
        projection_name = (area_def.name).replace(" ", "_")
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

    @staticmethod
    def write_geolocation(
            fh, fname: str, parent: str, area_def, dtype: np.dtype, append: bool, compression, chunks: tuple[int, int]
    ) -> tuple[list, list[FakeHDF5]]:
        """Delayed Geolocation Data write."""
        msg = ("Adding geolocation 'longitude' and " "'latitude' datasets for grid %s", parent)
        LOG.info(msg)
        lon_data, lat_data = area_def.get_lonlats(chunks=chunks)

        dtype = lon_data.dtype if dtype is None else dtype

        lon_grp = "{}/longitude".format(parent)
        lat_grp = "{}/latitude".format(parent)

        lon_dataset = FakeHDF5(fh, fname, lon_grp, compression)
        lon_dataset.check_variable(lon_data, dtype, append)
        lat_dataset = FakeHDF5(fh, fname, lat_grp, compression)
        lat_dataset.check_variable(lat_data, dtype, append)

        return [lon_data, lat_data], [lon_dataset, lat_dataset]

    @staticmethod
    def create_variable(filename: str, parent, hdf_subgroup: str, dataset_id: xr.DataArray, dtype: np.dtype, **kwargs):
        """Create a hdf5 subgroup and it's attributes."""

        ds_attrs = dataset_id.attrs

        if hdf_subgroup in parent:
            LOG.warning("Product %s already in hdf5 group," "will delete existing dataset", hdf_subgroup)
            del parent[hdf_subgroup]

        try:
            dset = parent.create_dataset(hdf_subgroup, shape=dataset_id.shape, dtype=dtype, **kwargs)
        except ValueError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        dset.attrs["satellite"] = ds_attrs["platform_name"]
        dset.attrs["instrument"] = ds_attrs["sensor"]
        dset.attrs["begin_time"] = ds_attrs["start_time"].isoformat()
        dset.attrs["end_time"] = ds_attrs["end_time"].isoformat()

        return

    def save_datasets(self, dataset: list[xr.DataArray], filename=None, dtype=None, fill_value=None, append=True,
                      compute=True, **kwargs):
        """Save hdf5 datasets."""

        compression = kwargs.pop("compression", None) if "compression" in kwargs else None
        if compression == "none":
            compression = None

        add_geolocation = kwargs.pop("add_geolocation") if "add_geolocation" in kwargs else False

        # will this be written to one or multiple files?
        output_names = []
        for dataset_id in dataset:
            args = self._output_file_kwargs(dataset_id, dtype)
            out_filename = filename or self.get_filename(**args)
            output_names.append(out_filename)
        one_file = all_equal(output_names)

        filename = output_names[0]
        if not all_equal(output_names):
            LOG.warning("Writing to {}".format(filename))

        delayed_write = []
        hdf5_fh = self.open_hdf5_filehandle(filename, append=append)

        datasets_by_area = self.iter_by_area(dataset)
        for area, data_arrs in datasets_by_area:

            # open hdf5 file handle, check if group already exists.
            parent_group = self.create_proj_group(filename, hdf5_fh, area)

            if add_geolocation:
                chunks = data_arrs[0].chunks
                dsets, target_fh = self.write_geolocation(
                    hdf5_fh, filename, parent_group, area, dtype, append, compression, chunks
                )
            else:
                dsets = list()
                target_fh = list()

            for data_arr in data_arrs:
                d_dtype = data_arr.dtype if dtype is None else dtype
                hdf_subgroup = "{}/{}".format(parent_group, data_arr.attrs["name"])

                file_var = FakeHDF5(hdf5_fh, filename, hdf_subgroup, compression)
                file_var.check_variable(data_arr.data, d_dtype, append)
                dsets.append(data_arr.data)
                target_fh.append(file_var)
        return (dsets, target_fh)


def add_writer_argument_groups(parser, group=None):
    """Create writer argument groups."""
    from argparse import SUPPRESS

    if group is None:
        group = parser.add_argument_group(title="hdf5 Writer")
    group.add_argument("--output-filename", dest="filename", help="Custom file pattern to save dataset to")
    group.add_argument(
        "--dtype",
        choices=NumpyDtypeList(NUMPY_DTYPE_STRS),
        type=str_to_dtype,
        help="Data type of the output file (8-bit unsigned " "integer by default - uint8)",
    )
    group.add_argument(
        "--fill-value", dest="fill_value", type=int_or_float, help="Fill value for invalid data in this dataset."
    )
    group.add_argument("--compress", default="LZW", help="File compression algorithm (DEFLATE, LZW, NONE, etc)")
    group.add_argument(
        "--chunks",
        dest="chunks",
        type=tuple,
        help="Chunked storage of dataset. " "Default is chosen appropriate to dataset by h5py.",
    )
    group.add_argument(
        "--add-geolocation",
        dest="add_geolocation",
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
