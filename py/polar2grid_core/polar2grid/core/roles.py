#!/usr/bin/env python
# encoding: utf-8
"""Abstract Base Classes for polar2grid components

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

from .constants import *
from .time_utils import utc_now
from .fbf import data_type_to_fbf_type

import os
import sys
import logging
from abc import ABCMeta,abstractmethod,abstractproperty

try:
    # try getting setuptools/distribute's version of resource retrieval first
    import pkg_resources
    get_resource_string = pkg_resources.resource_string
except ImportError:
    import pkgutil
    get_resource_string = pkgutil.get_data

log = logging.getLogger(__name__)

class RescalerRole(object):
    __metaclass__ = ABCMeta

    # Fill values in the input and to set in the output
    DEFAULT_FILL_IN  = DEFAULT_FILL_VALUE
    DEFAULT_FILL_OUT = DEFAULT_FILL_VALUE

    # Dictionary mapping of data identifier to rescaling function and its
    # arguments
    config = {}

    @abstractproperty
    def default_config_dir(self):
        """Return the default search path to find a configuration file if
        the configuration file provided is not an absolute path and the
        configuration filename was not found in the current working
        directory.

        This does not work in subclasses since they will be called the
        function that 'lives' in this file.  Copying and pasting this
        function is the simplest solution until pkg_resources.
        """
        return os.path.split(os.path.realpath(__file__))[0]

    @abstractproperty
    def known_rescale_kinds(self):
        """Return a dictionary mapping data_kind constants to scaling
        function.  This will be used by the configuration file parser
        to decide what scaling function goes with each data_kind.

        The dictionary should at least have a key for each data_kind constant,
        but it may also have some common data_kind equivalents that may appear
        in a configuration file.  For instance, brightness temperatures may be
        written in the configuration file as 'btemp', 'brightness temperature',
        'btemperature', etc.  So the dictionary could have one key for each of
        these variations as well as the constant DKIND_BTEMP, all mapping to
        the same scaling function.

        A good strategy is to define the dictionary outside this
        function/property and return a pointer to that class attribute.
        This way the dictionary isn't created everytime it is accessed, but
        the property is still read only.
        """
        return {}

    # Define the dictionary once so it doesn't have to be
    # allocated/instantiated every time it's used
    _known_data_kinds = {
                            'brightnesstemperature': DKIND_BTEMP,
                        }

    @property
    def known_data_kinds(self):
        # Used in configuration reader
        return self._known_data_kinds

    def __init__(self, config=None, fill_in=None, fill_out=None):
        """Load the initial configuration file and any other information
        needed for later rescaling.
        """
        if config is not None:
            self.load_config(config)

        self.fill_in = fill_in or self.DEFAULT_FILL_IN
        self.fill_out = fill_out or self.DEFAULT_FILL_OUT

    def _create_config_id(self, sat, instrument, kind, band, data_kind):
        return "_".join([sat.lower(), instrument.lower(), kind.lower(), (band or "").lower(), data_kind.lower()])

    def load_config_str(self, config_str):
        """Just in case I want to have a config file stored as a string in
        the future.

        """
        # Get rid of trailing new lines and commas
        config_lines = [ line.strip(",\n") for line in config_str.split("\n") ]
        # Get rid of comment lines and blank lines
        config_lines = [ line for line in config_lines if line and not line.startswith("#") and not line.startswith("\n") ]
        # Check if we have any useful lines
        if not config_lines:
            log.warning("No non-comment lines were found in rescaling configuration")
            return False

        try:
            # Parse config lines
            for line in config_lines:
                parts = [ part.strip() for part in line.split(",") ]
                if len(parts) < 6:
                    log.error("Rescale config line needs at least 6 columns : '%s'" % (line))
                    raise ValueError("Rescale config line needs at least 6 columns : '%s'" % (line))

                # Verify that each identifying portion is valid
                for i in range(6):
                    assert parts[i],"Field %d can not be empty" % i
                    # polar2grid demands lowercase fields
                    parts[i] = parts[i].lower()

                # Convert band if none
                if parts[3] == '' or parts[3] == "none":
                    parts[3] = NOT_APPLICABLE
                # Make sure we know the data_kind
                if parts[4] not in SET_DKINDS:
                    if parts[4] in self.known_data_kinds:
                        parts[4] = self.known_data_kinds[parts[4]]
                    else:
                        log.warning("Rescaling doesn't know the data kind '%s'" % parts[4])

                # Make sure we know the scale kind
                if parts[5] not in self.known_rescale_kinds:
                    log.error("Rescaling doesn't know the rescaling kind '%s'" % parts[5])
                    raise ValueError("Rescaling doesn't know the rescaling kind '%s'" % parts[5])
                parts[5] = self.known_rescale_kinds[parts[5]]
                # TODO: Check argument lengths and maybe values per rescale kind 

                # Enter the information into the configs dict
                line_id = self._create_config_id(*parts[:5])
                config_entry = (parts[5], tuple(float(x) for x in parts[6:]))
                self.config[line_id] = config_entry
        except StandardError:
            # Clear out the bad config
            log.warning("Rescaling configuration file could be in a corrupt state")
            raise

        return True

    def load_config(self, config_filename):
        """
        Load a rescaling configuration file for later use by the `__call__`
        function.

        If the config isn't an absolute path, it checks the current directory,
        and if the config can't be found there it is assumed to be relative to
        the package structure. So entering just the filename will look in the
        default rescaling configuration location (the package root) for the
        filename provided.
        """
        if not os.path.isabs(config_filename):
            # Its not an absolute path, lets see if its relative path
            cwd_config = os.path.join(os.path.curdir, config_filename)
            if os.path.exists(cwd_config):
                config_filename = cwd_config
            else:
                # they have specified a package provided file
                log.info("Loading package provided rescale config: '%s'" % (config_filename,))
                try:
                    config_str = get_resource_string(self.__module__, config_filename)
                except StandardError:
                    log.error("Rescale config '%s' was not found" % (config_filename,))
                    raise
                return self.load_config_str(config_str)

        config = os.path.realpath(config_filename)

        log.debug("Using rescaling configuration '%s'" % (config,))

        config_file = open(config, 'r')
        config_str = config_file.read()
        return self.load_config_str(config_str)

    @abstractmethod
    def __call__(self, sat, instrument, kind, band, data_kind, data):
        raise NotImplementedError("This function has not been implemented")

class BackendRole(object):
    __metaclass__ = ABCMeta

    def create_output_filename(self, pattern, sat, instrument, kind, band,
            data_kind, **kwargs):
        """Helper function that will take common meta data and put it into
        the output filename pattern provided.  The ``*args`` arguments are
        the same as for `create_product`. If either of the keyword arguments
        ``start_time`` or ``end_time`` are not specified the other is used
        in its place.  If neither are specified the current time in UTC is
        taken.

        Some arguments are handled in special ways:
            - start_time : start_time converted into 5 different strings
                that can each be individually specified in the pattern:
                    * start_time     : YYYYMMDD_HHMMSS
                    * start_YYYYMMDD : YYYYMMDD
                    * start_YYMMDD   : YYMMDD
                    * start_HHMMSS   : HHMMSS
                    * start_HHMM     : HHMM
            - end_time   : Same as start_time

        If a keyword is provided that is not recognized it will be provided
        to the pattern after running through a `str` filter.

        Possible pattern keywords (\*created internally in this function):
            - sat             : identifier for the instrument's satellite
            - instrument      : name of the instrument
            - kind            : band kind
            - band            : band identifier or number
            - data_kind       : kind of data (brightness temperature, radiance, reflectance, etc.)
            - data_type       : data type name of data in-memory, numpy naming(ex. uint8, int32, real32)
            - fbf_dtype\*      : data type name of data on-disk, fbf naming (ex. uint1, int4, real4)
            - grid_name       : name of the grid the data was mapped to
            - cols            : number of columns in the data
            - rows            : number of rows in the data
            - start_time      : start time of the first scan (YYYYMMDD_HHMMSS)
            - start_YYYYMMDD\* : start date of the first scan
            - start_YYMMDD\*   : start date of the first scan
            - start_HHMMSS\*   : start time of the first scan
            - start_HHMM\*     : start time of the first scan
            - end_time        : end time of the first scan. Same keywords as start_time.

        >>> from datetime import datetime
        >>> pattern = "%(sat)s_%(instrument)s_%(kind)s_%(band)s_%(data_kind)s_%(grid_name)s_%(start_time)s.%(data_type)s.%(cols)s.%(rows)s"
        >>> class FakeBackend(BackendRole):
        ...     def create_product(self, *args): pass
        ...     def can_handle_inputs(self, *args): pass
        >>> backend = FakeBackend()
        >>> filename = backend.create_output_filename(pattern,
        ...     "npp",
        ...     "viirs",
        ...     "i",
        ...     "04",
        ...     "btemp",
        ...     grid_name = "wgs84_fit",
        ...     data_type = "uint8",
        ...     cols = 2500, rows=3000, start_time=datetime(2012, 11, 10, 9, 8, 7))
        >>> print filename
        npp_viirs_i_04_btemp_wgs84_fit_20121110_090807.uint8.2500.3000

        """
        # Keyword arguments
        data_type      = kwargs.pop("data_type", None)
        grid_name      = str(kwargs.pop("grid_name", None))
        cols           = kwargs.pop("cols", None)
        rows           = kwargs.pop("rows", None)
        start_time_dt  = kwargs.pop("start_time", None)
        end_time_dt    = kwargs.pop("end_time", None)

        # Convert FBF data type
        try:
            fbf_dtype  = data_type_to_fbf_type(data_type) if data_type is not None else data_type
        except ValueError:
            fbf_dtype  = None

        # Convert start time and end time
        if start_time_dt is None and end_time_dt is None:
            start_time_dt = end_time_dt = utc_now()
        elif start_time_dt is None:
            start_time_dt = end_time_dt
        elif end_time_dt is None:
            end_time_dt   = start_time_dt

        start_time     = start_time_dt.strftime("%Y%m%d_%H%M%S")
        start_YYYYMMDD = start_time_dt.strftime("%Y%m%d")
        start_YYMMDD   = start_time_dt.strftime("%y%m%d")
        start_HHMMSS   = start_time_dt.strftime("%H%M%S")
        start_HHMM     = start_time_dt.strftime("%H%M")
        end_time       = end_time_dt.strftime("%Y%m%d_%H%M%S")
        end_YYYYMMDD   = end_time_dt.strftime("%Y%m%d")
        end_YYMMDD     = end_time_dt.strftime("%y%m%d")
        end_HHMMSS     = end_time_dt.strftime("%H%M%S")
        end_HHMM       = end_time_dt.strftime("%H%M")

        try:
            output_filename = pattern % dict(
                    sat            = sat,
                    instrument     = instrument,
                    kind           = kind,
                    band           = band,
                    data_kind      = data_kind,
                    data_type      = data_type,
                    fbf_dtype       = fbf_dtype,
                    grid_name      = grid_name,
                    cols           = cols,
                    rows           = rows,
                    start_time     = start_time,
                    start_YYYYMMDD = start_YYYYMMDD,
                    start_YYMMDD   = start_YYMMDD,
                    start_HHMMSS   = start_HHMMSS,
                    start_HHMM     = start_HHMM,
                    end_time       = end_time,
                    end_YYYYMMDD   = end_YYYYMMDD,
                    end_YYMMDD     = end_YYMMDD,
                    end_HHMMSS     = end_HHMMSS,
                    end_HHMM       = end_HHMM,
                    **kwargs
                    )
        except KeyError as e:
            log.error("Unknown output pattern key: '%s'" % (e.message,))
            raise

        return output_filename

    @abstractmethod
    def can_handle_inputs(self, sat, instrument, kind, band, data_kind):
        """Function that returns the grids that it will be able to handle
        for the data described by the arguments passed.  It returns either
        a list of grid names (that must be defined in grids.conf) or it
        returns a constant defined in `polar2grid.core.constants` for grids.
        Possible constants are:

            - GRIDS_ANY: Any gpd or proj4 grid
            - GRIDS_ANY_GPD: Any gpd grid
            - GRIDS_ANY_PROJ4: Any proj4 grid

        """
        return []

    @abstractmethod
    def create_product(self, sat, instrument, kind, band, data_kind,
            start_time=None, end_time=None, grid_name=None,
            output_filename=None):
        raise NotImplementedError("This function has not been implemented")

class FrontendRole(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def make_swaths(self, filepaths, **kwargs):
        raise NotImplementedError("This function has not been implemented")

def main():
    """Run some tests on the interfaces/roles
    """
    # TODO
    import doctest
    print "Running doctests"
    return doctest.testmod()

if __name__ == "__main__":
    sys.exit(main())

