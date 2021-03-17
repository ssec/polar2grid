import os
import logging
from satpy.writers import Writer
from satpy import find_files_and_readers, Scene
from datetime import datetime as datetime

LOG = logging.getLogger(__name__)

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
# FIXME: Use package_resources?
PACKAGE_CONFIG_PATH = os.path.join(BASE_PATH, 'etc')

config_fn = os.path.join(PACKAGE_CONFIG_PATH, 'hdf5.yaml')


class hdf5writer(Writer):
    """Writer for hdf5 files."""

    # JMF NOTE:  figure out how to work with these, probably want to use some of these opts.
    # some of these are dask some of these are pandas args for h5py options and not all of them
    # make sense
    H5PY_OPTIONS = ("compute",
                    "lock",
                    "scheduler",
                    "key",
                    "mode",
                    "complevel",
                    "complib",
                    "append",
                    "format",
                    "errors",
                    "encoding",
                    "min_itemsize",
                    "data_columns"
                    )

    def __init__(self, dtype=None, **kwargs):
        """Init the writer."""
        super(hdf5writer, self).__init__(default_config_filename=config_fn,
                                            **kwargs)
        self.dtype = self.info.get("dtype") if dtype is None else dtype

        # h5py specific settings
        self.h5py_options = {}
        for k in self.H5PY_OPTIONS:
            if k in kwargs or k in self.info:
                self.h5py_options[k] = kwargs.get(k, self.info[k])

    @classmethod
    def separate_init_kwargs(cls, kwargs):
        """Separate the init keyword args."""
        # FUTURE: Don't pass Scene.save_datasets kwargs to init and here
        init_kwargs, kwargs = super(hdf5writer, cls).separate_init_kwargs(
            kwargs)
        for kw in ['dtype']:
            if kw in kwargs:
                init_kwargs[kw] = kwargs.pop(kw)

        return init_kwargs, kwargs

    def save_datasets(self, dataset, filename=None, dtype=None, fill_value=None, **kwargs):

        for dataset_id in dataset:
            print(dataset_id.attrs['name'])
            # use daskArray.to_hdf here.
        pass
if __name__ == "__main__":
    basedir="/Users/joleenf/data/mirs/"
    f = find_files_and_readers(base_dir=basedir, start_time=datetime(2020,12,20,7,00),
                               end_time=datetime(2020,12,20,18,30), reader="mirs")
    a = Scene(f)
    a.load(["TPW", "RR"])
    a.save_datasets(filename='test.h5', writer='hdf5',
                    base_dir=basedir, config_files=[config_fn])