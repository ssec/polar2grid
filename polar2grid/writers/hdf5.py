from __future__ import annotations

import os
import sys
import logging

import pkg_resources
import satpy
import h5py
import numpy as np
import xarray as xr
import dask.array as da

from itertools import groupby
from datetime import datetime as datetime
from satpy.dataset import DataID
from satpy.writers import ImageWriter
from satpy.readers.yaml_reader import FileYAMLReader
from satpy.writers import compute_writer_results

from trollsift import Parser

from pyresample.geometry import SwathDefinition
from polar2grid.utils.legacy_compat import convert_p2g_pattern_to_satpy
from polar2grid.writers.geotiff import NUMPY_DTYPE_STRS, NumpyDtypeList, str_to_dtype, int_or_float

from polar2grid.core.script_utils import setup_logging, rename_log_file, create_exc_handler

USE_POLAR2GRID_DEFAULTS = bool(int(os.environ.setdefault("USE_POLAR2GRID_DEFAULTS", "1")))

LOG = logging.getLogger(__name__)

# reader_name -> filename
DEFAULT_OUTPUT_FILENAMES = {None: "{platform_name}_{sensor}_{start_time:%Y%m%d_%H%M%S}.h5"}


def dist_is_editable(dist) -> bool:
    """Is distribution an editable install?"""
    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.project_name + ".egg-link")
        if os.path.isfile(egg_link):
            return True
    return False


dist = pkg_resources.get_distribution("polar2grid")
if dist_is_editable(dist):
    p2g_etc = os.path.join(dist.module_path, "etc")
else:
    p2g_etc = os.path.join(sys.prefix, "etc", "polar2grid")

config_path = satpy.config.get("config_path")
if p2g_etc not in config_path:
    satpy.config.set(config_path=config_path + [p2g_etc])


def all_equal(iterable: list[str]) -> bool:
    "Returns True if all the elements are equal to each other"
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


class FakeHDF5:
    def __init__(self, fh, output_filename: str, var_name: str, data, compression: bool):
        self.fh = fh
        self.output_filename = output_filename
        self.var_name = var_name
        self.compression = compression
        self.data = self.data(data)

    def data(self, data):
        if isinstance(data, np.ndarray):
            return da.from_array(data)
        elif isinstance(data, xr.DataArray):
            return data.data
        return data

    def __setitem__(self, write_slice, data):
        x = self.data
        dset = self.fh.require_dataset(self.var_name, shape=x.shape, dtype=x.dtype, compression=self.compression)
        self.fh[self.var_name][write_slice] = data


class hdf5writer(ImageWriter):
    """Writer for hdf5 files."""

    def __init__(self, dtype=None, **kwargs):
        """Init the writer."""
        super(hdf5writer, self).__init__(default_config_filename="/writers/hdf5.yaml", **kwargs)
        self.dtype = self.info.get("dtype") if dtype is None else dtype

    def _output_file_kwargs(self, dataset):
        """Get file keywords from data for output_pattern."""
        if isinstance(dataset, list):
            dataset = dataset[0]
            area = dataset[0].attrs["area"]
        else:
            area = dataset.attrs["area"]

        args = dataset.attrs
        args["grid_name"] = "native" if isinstance(area, SwathDefinition) else area.area_id
        args["rows"], args["columns"] = area.shape
        args["data_type"] = self.dtype

        return args

    def iter_by_area(self, datasets):
        """Generate datasets grouped by Area.
        :return: generator of (area_obj, list of dataset objects)
        """
        datasets_by_area = {}
        for ds in datasets:
            a = ds.attrs.get("area")
            ds_name = ds.attrs["name"]
            datasets_by_area.setdefault(a, []).append((ds_name, ds))
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
    def open_hdf5_filehandle(output_filename: str, append=True):
        """Open a HDF5 file handle."""
        if os.path.isfile(output_filename):
            if append:
                LOG.info("Will append to existing file: %s", output_filename)
                mode = "a"
            elif not self.overwrite_existing:
                LOG.error("HDF5 file already exists: %s", output_filename)
                raise RuntimeError("HDF5 file already exists: %s" % (output_filename,))
            else:
                LOG.warning("HDF5 file already exists, will overwrite/truncate: %s", output_filename)
                mode = "w"
        else:
            LOG.info("Creating HDF5 file: %s", output_filename)
            mode = "w"

        h5_fh = h5py.File(output_filename, mode)
        return h5_fh

    @staticmethod
    def create_proj_group(filename: str, parent, area_def):
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
    def write_geolocation(fh, fname: str, parent, area_def, compression):
        """Delayed Geolocation Data write."""
        msg = ("Adding geolocation 'longitude' and " "'latitude' datasets for grid %s", parent)
        LOG.info(msg)
        lon_data, lat_data = area_def.get_lonlats()

        lon_grp = "{}/longitude".format(parent)
        lat_grp = "{}/latitude".format(parent)

        lon_dataset = FakeHDF5(fh, fname, lon_grp, lon_data, compression)
        lat_dataset = FakeHDF5(fh, fname, lat_grp, lat_data, compression)

        return [lon_dataset.data, lat_dataset.data], [lon_dataset, lat_dataset]

    @staticmethod
    def create_variable(filename: str, parent, hdf_subgroup: str, dataset_id, **kwargs):
        """Create a hdf5 subgroup and it's attributes."""

        ds_attrs = dataset_id.attrs

        if hdf_subgroup in parent:
            LOG.warning("Product %s already in hdf5 group," "will delete existing dataset", hdf_subgroup)
            del parent[hdf_subgroup]

        try:
            dset = parent.create_dataset(hdf_subgroup, shape=dataset_id.shape, dtype=dataset_id.dtype, **kwargs)
        except ValueError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        dset.attrs["satellite"] = ds_attrs["platform_name"]
        dset.attrs["instrument"] = ds_attrs["sensor"]
        dset.attrs["begin_time"] = ds_attrs["start_time"].isoformat()
        dset.attrs["end_time"] = ds_attrs["end_time"].isoformat()

        return

    def save_datasets(self, dataset, filename=None, dtype=None, fill_value=None, append=True, compute=True, **kwargs):
        """Save hdf5 datasets."""
        # don't need config_files key anymore
        _config_files = kwargs.pop("config_files")

        compression = kwargs.pop("compression", None) if "compression" in kwargs else None
        if compression == "none":
            compression = None

        add_geolocation = kwargs.pop("add_geolocation") if "add_geolocation" in kwargs else False

        dask_args = {"append": append}
        for key in ["compress", "shuffle"]:
            if key in kwargs:
                dask_args[key] = kwargs.pop(key)

        # will this be written to one or multiple files?
        output_names = []
        for dataset_id in dataset:
            args = self._output_file_kwargs(dataset_id)
            out_filename = filename or self.get_filename(**args)
            output_names.append(out_filename)
        one_file = all_equal(output_names)

        filename = output_names[0]
        if not all_equal(output_names):
            LOG.warning("Writing to {}".format(filename))

        delayed_write = []
        hdf5_fh = self.open_hdf5_filehandle(filename, append=append)

        datasets_by_area = self.iter_by_area(dataset)

        for area, data_names in datasets_by_area:
            # open hdf5 file handle, check if group already exists.
            parent_group = self.create_proj_group(filename, hdf5_fh, area)

            if add_geolocation:
                dsets, target_fh = self.write_geolocation(
                    hdf5_fh, filename, parent_group, area, compression=compression
                )
            else:
                dsets = list()
                target_fh = list()

            for (data_name, data_arr) in data_names:
                hdf_subgroup = "{}/{}".format(parent_group, data_name)

                file_var = FakeHDF5(hdf5_fh, filename, hdf_subgroup, data_arr.data, compression)
                dsets.append(data_arr.data)
                target_fh.append(file_var)

        return (dsets, target_fh)


def add_writer_argument_groups(parser, group=None):
    """Create writer argument groups."""
    from argparse import SUPPRESS

    yaml = os.path.join(p2g_etc, "writers", "hdf5.yaml")
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

    return group, None


if __name__ == "__main__":
    from satpy import find_files_and_readers, Scene

    basedir = "/Users/joleenf/data/mirs/"
    f = find_files_and_readers(
        base_dir=basedir,
        start_time=datetime(2020, 12, 20, 7, 00),
        end_time=datetime(2020, 12, 20, 18, 30),
        reader="mirs",
    )
    a = Scene(f)
    a.load(["TPW", "RR"])
    # new = a.resample('northamerica')
    a.save_datasets(
        filename=DEFAULT_OUTPUT_FILENAMES[None], writer="hdf5", base_dir=basedir, add_geolocation=True, compression=True
    )
