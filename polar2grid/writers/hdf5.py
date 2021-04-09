import os
import sys
import logging
import satpy
import pkg_resources
import h5py
from polar2grid.writers.geotiff import NUMPY_DTYPE_STRS, NumpyDtypeList,\
    str_to_dtype, int_or_float
from satpy.writers import Writer
from satpy.readers.yaml_reader import FileYAMLReader
from satpy.utils import debug_on
from trollsift import Parser

from pyresample.geometry import SwathDefinition
from datetime import datetime as datetime
from polar2grid.utils.legacy_compat import convert_p2g_pattern_to_satpy

from satpy.writers import compute_writer_results
from dask.diagnostics import ProgressBar
from polar2grid.core.script_utils import (
    setup_logging, rename_log_file, create_exc_handler)

USE_POLAR2GRID_DEFAULTS = bool(int(os.environ.setdefault("USE_POLAR2GRID_DEFAULTS", "1")))

LOG = logging.getLogger(__name__)

debug_on()


def dist_is_editable(dist):
    """Is distribution an editable install?"""
    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.project_name + '.egg-link')
        if os.path.isfile(egg_link):
            return True
    return False

dist = pkg_resources.get_distribution('polar2grid')
if dist_is_editable(dist):
    p2g_etc = os.path.join(dist.module_path, 'etc')
else:
    p2g_etc = os.path.join(sys.prefix, 'etc', 'polar2grid')

config_path = satpy.config.get('config_path')
if p2g_etc not in config_path:
    satpy.config.set(config_path=config_path + [p2g_etc])

def DEFAULT_FILE_PATTERN(config_files):
    a = hdf5writer("hdf5", config_files=config_files)
    return a.file_pattern

class hdf5writer(Writer):
    """Writer for hdf5 files."""
    def __init__(self, dtype=None, **kwargs):
        """Init the writer."""
        super(hdf5writer, self).__init__(default_config_filename="/writers/hdf5.yaml",
                                         **kwargs)
        self.dtype = self.info.get("dtype") if dtype is None else dtype

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

        add_geolocation = kwargs.pop("add_geolocation") \
            if "add_geolocation" in kwargs else False

        for dataset_id in dataset:
            args = self._output_file_kwargs(dataset_id)
            out_filename = filename or self.get_filename(**args)
            # open hdf5 file handle, check if group already exists.
            hdf5_fh = self.open_hdf5_filehandle(out_filename, append=append)
            hdf_group = self.create_group_from_data(filename, hdf5_fh,
                                                    dataset, add_geolocation,
                                                    **kwargs)

            hdf_subgroup = '{}/{}'.format(hdf_group, dataset_id.attrs["name"])
            create_subgroup_dataset(out_filename, hdf5_fh, hdf_subgroup,
                                    dataset_id, **kwargs)

            hdf5_fh.close()

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

    def open_hdf5_filehandle(self, output_filename, append=True):
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
    def create_group_from_data(filename, parent, dataset,
                               add_geolocation, **kwargs):
       dask_args = {}
       for key in ["append", "compute", "compression", "shuffle"]:
          if key in kwargs:
             dask_args[key] = kwargs.pop(key)

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

       if add_geolocation:
           msg=("Adding geolocation 'longitude' and "
                "'latitude' datasets for grid %s", projection_name)
           LOG.info(msg)
           lon_data, lat_data = data_arr.attrs["area"].get_lonlats()

           lon_subgroup = "{}/longitude".format(projection_name)
           lat_subgroup = "{}/latitude".format(projection_name)
           dataset_id.data.to_hdf5(filename, lon_subgroup, **dask_args)
           dataset_id.data.to_hdf5(filename, lat_subgroup, **dask_args)
           """group.create_dataset("longitude", shape=data_arr.shape,
                                dtype=lon_data.dtype, data=lon_data,
                                compression=compression)
           group.create_dataset("latitude", shape=data_arr.shape,
                                dtype=lat_data.dtype, data=lat_data,
                                compression=compression)"""

       return projection_name


    @staticmethod
    def create_subgroup_dataset(filename, parent, hdf_subgroup,
                                dataset_id, **kwargs):
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




class HDF5_YAMLreader(FileYAMLReader):
    """Custom file reader for reading writer's yaml file at runtime."""

    def __init__(self, config_files, **kwargs):
        """Initialize file reader and adjust geolocation preferences.

        Args:
            config_files (iterable): yaml config files passed to base class
        """
        super(HDF5_YAMLreader, self).__init__(config_files, **kwargs)
        pass

"""if __name__ == "__main__":
    
    from satpy import find_files_and_readers, Scene
    basedir="/Users/joleenf/data/mirs/"
    f = find_files_and_readers(base_dir=basedir, start_time=datetime(2020,12,20,7,00),
                               end_time=datetime(2020,12,20,18,30), reader="mirs")
    a = Scene(f)
    a.load(["TPW", "RR"])
    #new = a.resample('northamerica')
    a.save_datasets(
                      writer="hdf5", base_dir=basedir, add_geolocation=True,
                      append=True, compression=True)"""

def add_writer_argument_groups(parser, group=None):
    from argparse import SUPPRESS
    yaml = os.path.join(p2g_etc, "writers", "hdf5.yaml")
    if group is None:
        group = parser.add_argument_group(title='hdf5 Writer')
    group.add_argument('--output-filename', dest='filename',
                       default=DEFAULT_FILE_PATTERN([yaml]),
                       help='Custom file pattern to save dataset to')
    group.add_argument('--dtype', choices=NumpyDtypeList(NUMPY_DTYPE_STRS), type=str_to_dtype,
                       help='Data type of the output file (8-bit unsigned '
                            'integer by default - uint8)')
    group.add_argument('--fill-value', dest='fill_value', type=int_or_float,
                       help='Fill value for invalid data in this dataset.')
    group.add_argument('--compress', default='LZW',
                       help='File compression algorithm (DEFLATE, LZW, NONE, etc)')
    group.add_argument('--gdal-num-threads', dest='num_threads',
                       default=os.environ.get('DASK_NUM_WORKERS', 4),
                       help=SUPPRESS)  # don't show this option to the user
                       # help='Set number of threads used for compressing '
                       #      'geotiffs (default: Same as num-workers)')
    group.add_argument('--chunks', dest='chunks', type=tuple,
                       help="Chunked storage of dataset. "
                            "Default is chosen appropriate to dataset by h5py.")
    return group, None
