import os
import sys
import logging
import satpy
import string
import re
import pkg_resources
import h5py
from functools import lru_cache
from itertools import groupby
from satpy.writers import Writer
from satpy.utils import debug_on
from trollsift import Parser
from satpy import find_files_and_readers, Scene
from pyresample.geometry import SwathDefinition
from datetime import datetime as datetime
from pyproj import CRS
from util.legacy_compat import convert_p2g_pattern_to_satpy, legacy_proj
LOG = logging.getLogger(__name__)

debug_on()


def dist_is_editable(dist):
    """Is distribution an editable install?"""
    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.project_name + '.egg-link')
        if os.path.isfile(egg_link):
            return True
    return False

# TODO:  Remove me if not used
def all_equal(iterable):
    "Returns True if all the elements are equal to each other"
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def create_subgroup_dataset(filename, parent, hdf_subgroup, dataset_id,
                            **kwargs):
    """Write dask array to hdf5 file."""

    ds_attrs = dataset_id.attrs

    dask_args = {}

    for key in ["append", "compute", "compression", "shuffle"]:
        if key in kwargs:
            dask_args[key] = kwargs.pop(key)

    if hdf_subgroup in parent:
        LOG.warning("Product %s already in hdf5 group,"
                    "will delete existing dataset", hdf_subgroup)
        del parent[hdf_subgroup]


    try:
        dset = parent.create_dataset(hdf_subgroup, shape=dataset_id.shape,
                                     dtype=dataset_id.dtype, **kwargs)
    except ValueError:
        if os.path.isfile(filename):
            os.remove(filename)
        raise

    dset.attrs["satellite"] = ds_attrs["platform_name"]
    dset.attrs["instrument"] = ds_attrs["sensor"]
    dset.attrs["begin_time"] = ds_attrs["start_time"].isoformat()
    dset.attrs["end_time"] = ds_attrs["end_time"].isoformat()
    dataset_id.data.to_hdf5(filename, hdf_subgroup, **dask_args)

    
class hdf5writer(Writer):
    """Writer for hdf5 files."""
    def __init__(self, dtype=None, **kwargs):
        """Init the writer."""
        super(hdf5writer, self).__init__(default_config_filename="/writers/hdf5.yaml",
                                         **kwargs)
        self.dtype = self.info.get("dtype") if dtype is None else dtype
        #TODO:  Recheck that yaml sets default file name not that tags are commented out.
        """self.tags = self.info.get("tags", None) if tags is None else tags
        if self.tags is None:
            self.tags = {}
        elif not isinstance(self.tags, dict):
            # if it's coming from a config file
            self.tags = dict(tuple(x.split("=")) for x in self.tags.split(","))"""

    def _output_file_kwargs(self, dataset):
        """Get file keywords from data for output_pattern."""
        if isinstance(dataset, list):
            dataset=dataset[0]
            area = dataset[0].attrs['area']
        else:
            area = dataset.attrs['area']

        args = dataset.attrs
        args['grid_name'] = 'native' \
            if isinstance(area, SwathDefinition) else area.area_id
        args['rows'], args['columns'] = area.shape
        args['data_type'] = self.dtype

        return args

    def get_filename(self, **kwargs):
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

    def create_hdf5_file(self, output_filename, append=True):
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

        h5_group = h5py.File(output_filename, mode)
        return h5_group

    @staticmethod
    def create_group_from_data(dataset, parent, compression,
                               add_geolocation=False, **kwargs):
       data_arr = dataset[0]
       LOG.debug(data_arr.attrs["name"])
       projection_name = (data_arr.attrs["area"].name).replace(" ","_")
       # if top group alrady made, return.
       if projection_name in parent:
           return projection_name

       # create top group for first time
       group = parent.create_group(projection_name)
       # add attributes from grid_defintion.
       area_def = data_arr.attrs["area"]
       for a in ["height", "width", "origin_x", "origin_y"]:
           ds_attr = getattr(area_def, a, None)
           if ds_attr is None:
               pass
           else:
               group.attrs[a] = ds_attr
       group.attrs["proj4_string"] = area_def.proj_str
       group.attrs["cell_height"] = area_def.pixel_size_y
       group.attrs["cell_width"] = area_def.pixel_size_x

       if add_geolocation:
           msg=("Adding geolocation 'longitude' and "
                "'latitude' datasets for grid %s", projection_name)
           LOG.info(msg)
           lon_data, lat_data = data_arr.attrs["area"].get_lonlats()
           group.create_dataset("longitude", shape=data_arr.shape,
                                dtype=lon_data.dtype, data=lon_data,
                                compression=compression)
           group.create_dataset("latitude", shape=data_arr.shape,
                                dtype=lat_data.dtype, data=lat_data,
                                compression=compression)

       return projection_name


    def save_datasets(self, dataset, filename=None, dtype=None,
                      fill_value=None, **kwargs):
        """Save hdf5 datasets.
        arguments compression, append, add_geolocation"""
        # don't need config_files key anymore
        _config_files = kwargs.pop("config_files")
        compute = kwargs.pop("compute")
        kwargs["compression"] = kwargs.get("compression", None)
        if kwargs["compression"] == "none":
            kwargs["compression"] = None

        append = kwargs.get("append", True)

        if "add_geolocation" in kwargs:
            add_geolocation = kwargs.pop("add_geolocation")

        for dataset_id in dataset:
            args = self._output_file_kwargs(dataset_id)
            out_filename = filename or self.get_filename(**args)
            # open hdf5 file handle, check if group already exists.
            # TODO:  check on overwrite existing in self. (Check that this works)
            hdf5_fh = self.create_hdf5_file(out_filename, append=append)
            hdf_group = self.create_group_from_data(dataset, hdf5_fh, **kwargs)

            hdf_subgroup = '{}/{}'.format(hdf_group, dataset_id.attrs["name"])
            #TODO:  Create your own dataset, 
            create_subgroup_dataset(out_filename, hdf5_fh, hdf_subgroup,
                                    dataset_id,
                                    **kwargs)

            hdf5_fh.close()

if __name__ == "__main__":
    from satpy import Scene
    from satpy.writers import compute_writer_results
    from dask.diagnostics import ProgressBar
    from polar2grid.core.script_utils import (
        setup_logging, rename_log_file, create_exc_handler)
    import argparse

    dist = pkg_resources.get_distribution('polar2grid')
    if dist_is_editable(dist):
        p2g_etc = os.path.join(dist.module_path, 'etc')
    else:
        p2g_etc = os.path.join(sys.prefix, 'etc', 'polar2grid')
    config_path = satpy.config.get('config_path')
    if p2g_etc not in config_path:
        satpy.config.set(config_path=config_path + [p2g_etc])

    USE_POLAR2GRID_DEFAULTS = bool(int(os.environ.setdefault("USE_POLAR2GRID_DEFAULTS", "1")))

    basedir="/Users/joleenf/data/mirs/"
    f = find_files_and_readers(base_dir=basedir, start_time=datetime(2020,12,20,7,00),
                               end_time=datetime(2020,12,20,18,30), reader="mirs")
    a = Scene(f)
    a.load(["TPW", "RR"])
    new = a.resample('northamerica')
    new.save_datasets(filename="{sensor}_{start_time_YYMMDD}.h5",
                      writer="hdf5", base_dir=basedir, add_geolocation=True,
                      append=True, compression=True)
