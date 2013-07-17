#!/usr/bin/env python
# encoding: utf-8
"""Abstract Base Classes for polar2grid components

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3

Copyright (C) 2013 Space Science and Engineering Center (SSEC),
 University of Wisconsin-Madison.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

This file is part of the polar2grid software package. Polar2grid takes
satellite observation data, remaps it, and writes it to a file format for
input into another program.
Documentation: http://www.ssec.wisc.edu/software/polar2grid/

    Written by David Hoese    January 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

from .constants import *
from .time_utils import utc_now
from .fbf import data_type_to_fbf_type

import os
import sys
import logging
import re
from abc import ABCMeta,abstractmethod,abstractproperty

try:
    # try getting setuptools/distribute's version of resource retrieval first
    import pkg_resources
    get_resource_string = pkg_resources.resource_string
except ImportError:
    import pkgutil
    get_resource_string = pkgutil.get_data

log = logging.getLogger(__name__)

### Copied and modified from patch to allow abstractclassmethods in Python 2.7 ###
### URL: http://bugs.python.org/issue5867 ###
class abstractclassmethod(classmethod):
    """A decorator indicating abstract classmethods.

    Similar to abstractmethod.

    Usage:

        class C(metaclass=ABCMeta):
            @abstractclassmethod
            def my_abstract_classmethod(cls, ...):

    """
    __isabstractmethod__ = True

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable)


class abstractstaticmethod(staticmethod):
    """A decorator indicating abstract staticmethods.

    Similar to abstractmethod.

    Usage:

        class C(metaclass=ABCMeta):
            @abstractstaticmethod
            def my_abstract_staticmethod(...):

    """
    __isabstractmethod__ = True

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
        super(abstractstaticmethod, self).__init__(callable)

### End of Copy ###

class CSVConfigReader(object):
    """Base class for CSV configuration file readers.
    The format of the file is 1 configuration entry per line. Where the first
    N elements 'identify' the line in the internal storage of this object.

    Configuration files can be passed into the ``__init__`` method. One or more
    configuration files can be passed at a time. Individual configuration
    files can be added via the ``load_config_file`` method. Provided
    configuration files can be filepaths as strings or a file-like object.

    Wildcard identifying entries are supported by the '*' character. When
    requesting an entry, the loaded configuration files are searched in the
    order they were entered and in top-down line order. It is recommended
    that wildcards go near the bottom of files to avoid conflict.

    Class attributes:
        NUM_ID_ELEMENTS (default 6): Number of elements (starting from the
            first) that 'identify' the configuration entry.
        COMMENT_CHARACTER (default '#'): First character in a line
            representing a comment. Inline comments are not supported.
    """
    __metaclass__ = ABCMeta
    NUM_ID_ELEMENTS = 6
    COMMENT_CHARACTER = '#'

    def __init__(self, *config_files, **kwargs):
        """Initialize configuration reader.
        Provided configuration files can be filepaths or file-like objects.

        :keyword ignore_bad_lines: Ignore bad configuration lines if encountered
        :keyword min_num_elements: Minimum number of elements allowed in a config line
        """
        self.config_storage = []
        self.ignore_bad_lines = kwargs.get("ignore_bad_lines", False)
        self.min_num_elements = kwargs.get("min_num_elements", self.NUM_ID_ELEMENTS)
        for config_file in config_files:
            self.load_config_file(config_file)

    def load_config_file(self, config_file):
        """Load one configuration file into internal storage.
        """
        # If we were provided a string filepath then open the file
        if isinstance(config_file, str):
            config_file = open(config_file, 'r')

        # Read in each line
        for line in config_file:
            # Clean the line
            line = line.strip()
            # Ignore comments and blank lines
            if line.startswith(self.COMMENT_CHARACTER) or line == "":
                continue
            # Get each element
            parts = tuple( x.strip() for x in line.split(",") )
            # Parse the line
            self.parse_config_parts(parts)

    def parse_config_parts(self, parts):
        if len(parts) < self.min_num_elements:
            log.error("Line does not have correct number of elements: '%s'" % (str(parts),))
            if self.ignore_bad_lines: return
            raise ValueError("Line does not have correct number of elements: '%s'" % (str(parts),))

        # Separate the parts into identifying vs configuration parts
        id_parts = parts[:self.NUM_ID_ELEMENTS]
        entry_parts = parts[self.NUM_ID_ELEMENTS:]

        # Handle each part separately
        try:
            id_regex_obj = self.parse_id_parts(id_parts)
            entry_info = self.parse_entry_parts(entry_parts)
        except StandardError:
            if self.ignore_bad_lines: return
            raise ValueError("Bad configuration line: '%s'" % (str(parts),))

        self.config_storage.append((id_regex_obj,entry_info))

    def parse_id_parts(self, id_parts):
        parsed_parts = []
        for part in id_parts:
            if part == "None" or part == "none" or part == "":
                part = ''
            # If there is a '*' anywhere in the entry, make it a wildcard
            part = part.replace("*", r'.*')
            parsed_parts.append(part)

        this_regex = "_".join(parsed_parts)

        try:
            this_regex_obj = re.compile(this_regex)
        except re.error:
            log.error("Invalid configuration identifying information (not valid regular expression): '%s'" % (str(id_parts),))
            raise ValueError("Invalid configuration identifying information (not valid regular expression): '%s'" % (str(id_parts),))

        return this_regex_obj

    def parse_entry_parts(self, entry_parts):
        """Method called when loading a configuration entry.
        The argument passed is a tuple of each configuration entries
        information loaded from the file.

        This is where a user could convert a tuple to a dictionary with
        specific key names.
        """
        return entry_parts

    def prepare_config_entry(self, entry_info, id_info):
        """Method called when retrieving a configuration entry to prepare
        configuration information for the use.
        The second argument is a tuple of the identifying elements provided
        during the search. The first argument is whatever object was returned
        by ``parse_entry_parts`` during configuration loading.
        
        This method is used during the retrieval process in
        case the structure of the entry is based on the specifics of the
        match. For example, if a wildcard is matched, the configuration
        information might take on a different meaning based on what matched.

        This is where a user could convert a tuple to a dictionary with
        specific key names.
        """
        return entry_info

    def get_config_entry(self, *args, **kwargs):
        """Retrieve configuration information.
        Passed arguments will be matched against loaded configuration
        entry identities, therefore there must be the same number of elements
        as ``NUM_ID_ELEMENTS``.
        """
        if len(args) != self.NUM_ID_ELEMENTS:
            log.error("Incorrect number of identifying elements when searching configuration")
            raise ValueError("Incorrect number of identifying elements when searching configuration")

        search_id = "_".join(args)
        for regex_pattern,entry_info in self.config_storage:
            m = regex_pattern.match(search_id)
            if m is None: continue

            return self.prepare_config_entry(entry_info, args)

        raise ValueError("No config entry found matching: '%s'" % (search_id,))

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

    def _create_config_id(self, sat, instrument, nav_set_uid, kind, band, data_kind):
        return "_".join([sat.lower(), instrument.lower(), (nav_set_uid or "").lower(), kind.lower(), (band or "").lower(), data_kind.lower()])

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
                if len(parts) < 7:
                    log.error("Rescale config line needs at least 6 columns : '%s'" % (line))
                    raise ValueError("Rescale config line needs at least 6 columns : '%s'" % (line))

                # Verify that each identifying portion is valid
                for i in range(7):
                    assert parts[i],"Field %d can not be empty" % i
                    # polar2grid demands lowercase fields
                    parts[i] = parts[i].lower()

                # Convert band if none
                if parts[2] == '' or parts[2] == "none":
                    parts[2] = NOT_APPLICABLE
                if parts[4] == '' or parts[4] == "none":
                    parts[4] = NOT_APPLICABLE
                # Make sure we know the data_kind
                if parts[5] not in SET_DKINDS:
                    if parts[5] in self.known_data_kinds:
                        parts[5] = self.known_data_kinds[parts[5]]
                    else:
                        log.warning("Rescaling doesn't know the data kind '%s'" % parts[5])

                # Make sure we know the scale kind
                if parts[6] not in self.known_rescale_kinds:
                    log.error("Rescaling doesn't know the rescaling kind '%s'" % parts[6])
                    raise ValueError("Rescaling doesn't know the rescaling kind '%s'" % parts[6])
                parts[6] = self.known_rescale_kinds[parts[6]]
                # TODO: Check argument lengths and maybe values per rescale kind 

                # Enter the information into the configs dict
                line_id = self._create_config_id(*parts[:6])
                config_entry = (parts[6], tuple(float(x) for x in parts[7:]))
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
    def __call__(self, sat, instrument, nav_set_uid, kind, band, data_kind, data):
        raise NotImplementedError("This function has not been implemented")

class BackendRole(object):
    __metaclass__ = ABCMeta

    # Glob patterns for files that a glue script should remove
    # default is none
    removable_file_patterns = []

    def create_output_filename(self, pattern, sat, instrument, nav_set_uid, kind, band,
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
            - nav_set_uid     : navigation set unique identifier
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
        ...     "i_nav",
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
                    nav_set_uid    = nav_set_uid,
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
    def can_handle_inputs(self, sat, instrument, nav_set_uid, kind, band, data_kind):
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
    def create_product(self, sat, instrument, nav_set_uid, kind, band, data_kind,
            start_time=None, end_time=None, grid_name=None,
            output_filename=None):
        raise NotImplementedError("This function has not been implemented")

class FrontendRole(object):
    """Polar2grid role for data providing frontends. When provided satellite
    observation data the frontend should create binary files for each of the
    bands to be processed and their corresponding navigation data.
    """
    __metaclass__ = ABCMeta

    @abstractclassmethod
    def parse_datetimes_from_filepaths(cls, filepaths):
        """Class method for providing datetimes for each of the input filepaths.

        This method is used by glue scripts to find the proper datetime to
        timestamp logs with (usually the earliest). It must ignore (without
        logging an error/warning) any file that it does not understand since
        some glue scripts allow an entire directories listing to go to the
        frontend.
        """
        raise NotImplementedError("This function has not been implemented")

    @abstractclassmethod
    def sort_files_by_nav_uid(cls, filepaths):
        """Class method for sorting input filepaths.

        This method is used by glue scripts to organize filepaths into
        navigation sets that can be used by the `make_swaths` method. It must
        ignore (without logging an error/warning) any file that it does not
        understand since some glue scripts
        allow an entire directories listing to go to the frontend.

        :param filepaths: Absolute paths to input satellite instrument names
        :type filepaths: list
        :returns: dictionary of dictionaries. First key is the `nav_set_uid`
            for that `navigation_set`. Second key is file identifier that
            can be any arbitrary string. Some frontends use a file pattern
            as the file identifier. Each file identifier maps to a list
            of filepaths. Sorted and uniqueness is not guaranteed and is
            up to the frontend.
        :rtype: dict( dict( list ) )
        """
        raise NotImplementedError("This function has not been implemented")

    @abstractmethod
    def make_swaths(self, nav_set_uid, filepaths_dict, **kwargs):
        """Given satellite instrument data files, create flat binary files
        for all image data and navigation data. This method should only be
        called once per navigation set. Navigation filepaths will be derived
        from the information in the data files and are expected to be in the
        same directory as the files.

        :param filepaths_dict:
            absolute paths to satellite instrument data files keyed by a file
            identifier, where the file identifier is provided by the
            `sort_files_by_nav_uid` class method of the same frontend.
        :type filepaths: dict( list )

        :returns:
            Information describing the data provided that will
            be used by other polar2grid components. See the
            :doc:`Developer's Guide <dev_guide/frontends>`
            for information on what the meta data dictionary
            should contain.
        :rtype: dict
        """
        raise NotImplementedError("This function has not been implemented")

class CartographerRole(object):
    """Polar2grid role for managing grids. Grid information such as
    the projection, the projection's parameters, pixel size, grid height,
    grid width, and grid origin are stored in the Cartographer and can be
    accessed via the ``CartographerRole.get_grid_info`` method.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_all_grid_info(self):
        """Return grid information for all grids (static and dynamic)
        as a python dictionary, mapping ``grid_name`` to a dictionary
        of grid information. Exact information returned depends on the
        type of the grid and whether that grid dynamically fits the data
        being mapped or is a static size, resolution, and location.
        """
        raise NotImplementedError("Child class must implement this method")

    @abstractmethod
    def get_static_grid_info(self):
        """Like ``CartographerRole.get_all_grid_info`` but only returns
        static grids.
        """
        raise NotImplementedError("Child class must implement this method")

    @abstractmethod
    def get_dynamic_grid_info(self):
        """Like ``CartographerRole.get_all_grid_info`` but only returns
        dynamic grids.
        """
        raise NotImplementedError("Child class must implement this method")

    @abstractmethod
    def get_grid_info(self, grid_name):
        """Return grid information as a python dictionary for the
        ``grid_name`` provided. Exact information returned depends on the
        type of the grid and whether that grid dynamically fits the data
        being mapped or is a static size, resolution, and location.

        :raises ValueError: if ``grid_name`` does not exist
        """
        raise NotImplementedError("Child class must implement this method")

    @abstractmethod
    def add_grid_config(self, grid_config_filename):
        """Add the grids and their information to this objects internal
        store of grid information. The format of the grid configuration
        ultimately depends on the Cartographer implementation. This method
        should not erase previously added configuration files, but it will
        overwrite a ``grid_name`` that was added earlier.
        """
        raise NotImplementedError("Child class must implement this method")

    @abstractmethod
    def remove_grid(self, grid_name):
        """Remove ``grid_name`` from the internal grid information storage
        of this object.
        """
        raise NotImplementedError("Child class must implement this method")

    @abstractmethod
    def remove_all(self):
        """Remove all grids from the internal grid information storage of
        this object.
        """
        raise NotImplementedError("Child class must implement this method")

def main():
    """Run some tests on the interfaces/roles
    """
    import doctest
    return doctest.testmod()

if __name__ == "__main__":
    sys.exit(main())

