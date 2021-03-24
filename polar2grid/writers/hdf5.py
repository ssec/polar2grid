import os
import sys
import logging
import satpy
import string
import re
import pkg_resources
from functools import lru_cache
from satpy.writers import Writer
from trollsift import Parser
from satpy import find_files_and_readers, Scene
from pyresample.geometry import SwathDefinition
from datetime import datetime as datetime
LOG = logging.getLogger(__name__)


def dist_is_editable(dist):
    """Is distribution an editable install?"""
    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.project_name + '.egg-link')
        if os.path.isfile(egg_link):
            return True
    return False

def convert_old_p2g_date_frmts(frmt):
    """convert old user p2g date formats"""
    dt_frmts = {"_YYYYMMDD": ":%Y%m%d",
                  "_YYMMDD": ":%y%m%d",
                  "_HHMMSS": ":%H%M%S",
                  "_HHMM": ":%H%M"
                  }
    for old_frmt, new_frmt in dt_frmts.items():
        old_start="start_time{}".format(old_frmt)
        new_start="start_time{}".format(new_frmt)
        frmt = frmt.replace(old_start, new_start)

        old_begin="begin_time{}".format(old_frmt)
        frmt = frmt.replace(old_begin, new_start)

        old_end="end_time{}".format(old_frmt)
        new_end = "end_time{}".format(new_frmt)
        frmt = frmt.replace(old_end, new_end)

    return frmt

def convert_p2g_pattern_to_satpy(output_pattern):
    """convert p2g string patterns to satpy"""

    fmt=output_pattern.replace("begin_time", "")
    replacements = {"satellite": "platform_name",
                    "instrument": "sensor",
                    "product_name": "dataset_id",
                    "begin_time": "start_time",
                    }
    for p2g_kw, satpy_kw in replacements.items():
        fmt = fmt.replace(p2g_kw, satpy_kw)
    fmt = convert_old_p2g_date_frmts(fmt)

    return fmt


class hdf5writer(Writer):
    """Writer for hdf5 files."""
    def __init__(self, dtype=None, tags=None, **kwargs):
        """Init the writer."""
        super(hdf5writer, self).__init__(default_config_filename="/writers/hdf5.yaml",
                                         **kwargs)
        self.dtype = self.info.get("dtype") if dtype is None else dtype
        self.tags = self.info.get("tags", None) if tags is None else tags
        if self.tags is None:
            self.tags = {}
        elif not isinstance(self.tags, dict):
            # if it's coming from a config file
            self.tags = dict(tuple(x.split("=")) for x in self.tags.split(","))

    def _output_file_kwargs(self, dataset):
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

    def save_datasets(self, dataset, filename=None, dtype=None, fill_value=None, **kwargs):
        for dataset_id in dataset:
            args = self._output_file_kwargs(dataset_id)
            filename = filename or self.get_filename(**args)
            dataset_name = '{}/{}'.format(args['grid_name'], dataset_id.attrs['name'])
            dataset_id.data.to_hdf5(filename, dataset_name)
        pass

if __name__ == "__main__":
    import satpy
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
    #new.save_datasets(filename="{sensor}_{start_time:%Y%m%d_%H%M%S}_2.h5", writer="hdf5", base_dir=basedir)
    new.save_datasets(filename="{sensor}_{start_time_YYMMDD}.h5", writer="hdf5", base_dir=basedir)
    #new.save_datasets(datasets=["RR"], base_dir=basedir)