#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    December 2014
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""Abstract Base Classes for polar2grid components

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

from polar2grid.core.dtype import dtype_to_str

import os
import sys
import logging
import re
from datetime import datetime
from io import StringIO
from configparser import ConfigParser, Error as ConfigParserError
from abc import ABCMeta, abstractmethod

try:
    # try getting setuptools/distribute's version of resource retrieval first
    from pkg_resources import resource_string as get_resource_string
except ImportError:
    from pkgutil import get_data as get_resource_string

LOG = logging.getLogger(__name__)


class abstractclassmethod(classmethod):
    """A decorator indicating abstract classmethods.

    Similar to abstractmethod.

    Usage:

        class C(metaclass=ABCMeta):
            @abstractclassmethod
            def my_abstract_classmethod(cls, ...):

    ### Copied and modified from patch to allow abstractclassmethods in Python 2.7 ###
    ### URL: http://bugs.python.org/issue5867 ###
    """
    __isabstractmethod__ = True

    def __init__(self, callable_):
        callable_.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable_)


class abstractstaticmethod(staticmethod):
    """A decorator indicating abstract staticmethods.

    Similar to abstractmethod.

    Usage:

        class C(metaclass=ABCMeta):
            @abstractstaticmethod
            def my_abstract_staticmethod(...):

    ### Copied and modified from patch to allow abstractclassmethods in Python 2.7 ###
    ### URL: http://bugs.python.org/issue5867 ###
    """
    __isabstractmethod__ = True

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
        super(abstractstaticmethod, self).__init__(callable)


class SimpleINIConfigReader(object):
    """Simple object for reading .ini files.

    Main purpose is to make it easier to read multiple config files including those that
    may be included from inside a package.

    Access config reader object directly via the `config_parser` attribute.
    """
    def __init__(self, *config_files, **kwargs):
        self.config_files = config_files
        # Not commonly used by config readers, but we don't want to pass these to the config parser
        self.overwrite_existing = kwargs.pop("overwrite_existing", False)
        self.keep_intermediate = kwargs.pop("keep_intermediate", False)
        self.exit_on_error = kwargs.pop("exit_on_error", True)

        file_objs = set([f for f in self.config_files if not isinstance(f, str)])
        filepaths = set([f for f in self.config_files if isinstance(f, str)])

        self.config_parser = ConfigParser(kwargs, allow_no_value=True)

        if file_objs:
            for fp in file_objs:
                self.config_parser.read_file(fp)
        else:
            for fp in filepaths:
                fo = self.open_config_file(fp)
                try:
                    self.config_parser.read_file(fo, fp)
                except ConfigParserError:
                    LOG.warning("Could not parse config file: %s", fp)

    def open_config_file(self, config_file):
        """Load one configuration file into internal storage.

        If the config_file is a relative path string and can't be found it
        will be loaded from a package relative location. If it can't be found
        in the package an exception is raised.
        """
        # If we were provided a string filepath then open the file
        if isinstance(config_file, str):
            if not os.path.isabs(config_file):
                # Its not an absolute path, lets see if its relative path
                cwd_config = os.path.join(os.path.curdir, config_file)
                if os.path.exists(cwd_config):
                    config_file = cwd_config
                    config_file = open(config_file, 'r')
                else:
                    # they have specified a package provided file
                    LOG.debug("Loading package provided configuration file: '%s'" % (config_file,))
                    try:
                        parts = config_file.split(":")
                        mod_part, file_part = parts if len(parts) == 2 else ("", parts[0])
                        mod_part = mod_part or self.__module__
                        config_str = get_resource_string(mod_part, file_part).decode()
                    except ValueError:
                        LOG.error("Configuration file '%s' was not found" % (config_file,))
                        raise
                    config_file = StringIO(config_str)
            else:
                config_file = open(config_file, 'r')
        return config_file


class INIConfigReader(SimpleINIConfigReader):
    """Base class for INI configuration file readers.

    Basic .ini file format, but certain fields are identifying fields that identify the product being configured.

    Class attribute `id_fields` is used to read in certain section options as identifying fields. The values should be
    a conversion function to go from the read-in string to the proper type.
    """
    id_fields = None
    sep_char = ":"

    def __init__(self, *config_files, **kwargs):
        if self.id_fields is None:
            LOG.error("INIConfigReader not properly setup. Class attribute `id_fields` must be initialized")
            raise RuntimeError("INIConfigReader not properly setup. Class attribute `id_fields` must be initialized")

        self.section_prefix = kwargs.pop("section_prefix", None)
        self.empty_ok = kwargs.pop("empty_ok", False)
        self.config = []

        # defaults to string (meaning nothing happens)
        # this only affects non-ID fields
        # self.keyword_types = defaultdict(kwargs.pop("default_keyword_type", str))
        self.float_kwargs = kwargs.pop("float_kwargs", [])
        self.int_kwargs = kwargs.pop("int_kwargs", [])
        self.boolean_kwargs = kwargs.pop("boolean_kwargs", [])

        # Need to have defaults for id fields
        for k in self.id_fields:
            kwargs.setdefault(k, None)

        super(INIConfigReader, self).__init__(*config_files, **kwargs)

        self.load_config()
        if not self.config and not self.empty_ok:
            LOG.error("No valid configuration sections found with prefix '%s'", self.section_prefix)
            raise ValueError("No valid configuration sections found")

    def load_config(self):
        # Organize rescaling configuration sections
        for section in self.config_parser.sections():
            if self.section_prefix and not section.startswith(self.section_prefix):
                continue

            id_values = [self.config_parser.get(section, id_field) for id_field in self.id_fields]
            num_wildcards = 0
            id_regexes = []
            first_non_empty_idx = len(id_values)
            for idx, v in enumerate(id_values):
                if not v or v.lower() == "none":
                    num_wildcards += 1
                    id_regexes.append(".*")
                else:
                    id_regexes.append(v)
                    first_non_empty_idx = idx
            id_regex = "^" + self.sep_char.join(id_regexes) + "$"

            try:
                this_regex_obj = re.compile(id_regex)
            except re.error:
                LOG.error("Invalid configuration identifying information (not a valid regular expression): '%s'" % (str(id_regex),))
                raise ValueError("Invalid configuration identifying information (not a valid regular expression): '%s'" % (str(id_regex),))

            # Just need to know what section I should look in
            config_key = (num_wildcards, first_non_empty_idx, this_regex_obj, section)
            self.config.append(config_key)
        # If 2 or more entries have the same number of wildcards they may not be sorted optimally
        # (i.e. specific first field highest)
        self.config.sort(key=lambda x: (x[0], next(re.finditer(r'[^\^:.*].*', x[2].pattern)).start(), x[3]))

    def get_config_section(self, **kwargs):
        if len(kwargs) != len(self.id_fields):
            LOG.error("Incorrect number of identifying arguments, expected %d, got %d" % (len(self.id_fields), len(kwargs)))
            LOG.debug("Got %r; Expected %r", kwargs, self.id_fields)
            raise ValueError("Incorrect number of identifying arguments, expected %d, got %d" % (len(self.id_fields), len(kwargs)))

        id_key = self.sep_char.join(str(kwargs.get(k, None)) for k in self.id_fields)
        for num_wildcards, first_valid_idx, regex_obj, section in self.config:
            if regex_obj.match(id_key):
                LOG.debug("Key '%s' matched config regular expression '%s'", id_key, regex_obj.pattern)
                return section
        LOG.debug("No match found in config for key: %s", id_key)
        return None

    def get_config_options(self, **kwargs):
        allow_default = kwargs.pop("allow_default", True)
        section = self.get_config_section(**kwargs)
        if section is not None:
            LOG.debug("Using configuration section: %s", section)
            section_options = dict((k, self.config_parser.get(section, k)) for k in self.config_parser.options(section))
            # gotta get the defaults too
            for k, v in self.config_parser.defaults().items():
                if k not in section_options:
                    section_options[k] = v
        elif allow_default:
            LOG.debug("Using default configuration section")
            section_options = self.config_parser.defaults().copy()
        else:
            LOG.error("No configuration section found")
            raise RuntimeError("No configuration section found")

        # Convert values
        for k, v in section_options.items():
            if k in self.float_kwargs:
                section_options[k] = float(v)
                continue
            if k in self.int_kwargs:
                section_options[k] = int(v)
                continue
            if k in self.boolean_kwargs:
                section_options[k] = v == "True"
                continue

        for k, v in kwargs.items():
            # overwrite any wildcards with what we were provided
            section_options[k] = v

        return section_options


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

        If the config_file is a relative path string and can't be found it
        will be loaded from a package relative location. If it can't be found
        in the package an exception is raised.
        """
        # If we were provided a string filepath then open the file
        if isinstance(config_file, str):
            if not os.path.isabs(config_file):
                # Its not an absolute path, lets see if its relative path
                cwd_config = os.path.join(os.path.curdir, config_file)
                if os.path.exists(cwd_config):
                    config_file = cwd_config
                    config_file = open(config_file, 'r')
                else:
                    # they have specified a package provided file
                    LOG.debug("Loading package provided rescale config: '%s'" % (config_file,))
                    try:
                        config_str = get_resource_string(self.__module__, config_file).decode()
                    except ValueError:
                        LOG.error("Rescale config '%s' was not found" % (config_file,))
                        raise
                    config_file = StringIO(config_str)
            else:
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
            LOG.error("Line does not have correct number of elements: '%s'" % (str(parts),))
            if self.ignore_bad_lines: return
            raise ValueError("Line does not have correct number of elements: '%s'" % (str(parts),))

        # Separate the parts into identifying vs configuration parts
        id_parts = parts[:self.NUM_ID_ELEMENTS]
        entry_parts = parts[self.NUM_ID_ELEMENTS:]

        # Handle each part separately
        try:
            id_regex_obj = self.parse_id_parts(id_parts)
            entry_info = self.parse_entry_parts(entry_parts)
        except ValueError:
            if self.ignore_bad_lines: return
            LOG.error("Bad configuration line: '%s'" % (str(parts),))
            raise

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
            LOG.error("Invalid configuration identifying information (not valid regular expression): '%s'" % (str(id_parts),))
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
        It is best practice to copy any information that is being provided
        so it can't be changed by the user.

        This is where a user could convert a tuple to a dictionary with
        specific key names.
        """
        if hasattr(entry_info, "copy"):
            return entry_info.copy()
        elif isinstance(entry_info, list) or isinstance(entry_info, tuple):
            return entry_info[:]
        else:
            return entry_info

    def get_config_entry(self, *args, **kwargs):
        """Retrieve configuration information.
        Passed arguments will be matched against loaded configuration
        entry identities, therefore there must be the same number of elements
        as ``NUM_ID_ELEMENTS``.
        """
        if len(args) != self.NUM_ID_ELEMENTS:
            LOG.error("Incorrect number of identifying elements when searching configuration")
            raise ValueError("Incorrect number of identifying elements when searching configuration")

        search_id = "_".join([(x is not None and x) or "" for x in args])
        for regex_pattern, entry_info in self.config_storage:
            m = regex_pattern.match(search_id)
            if m is None:
                continue

            entry_info = self.prepare_config_entry(entry_info, args)
            return entry_info

        raise ValueError("No config entry found matching: '%s'" % (search_id,))

    def get_all_matching_entries(self, *args, **kwargs):
        """Retrieve configuration information.
        Passed arguments will be matched against loaded configuration
        entry identities, therefore there must be the same number of elements
        as ``NUM_ID_ELEMENTS``.
        """
        if len(args) != self.NUM_ID_ELEMENTS:
            LOG.error("Incorrect number of identifying elements when searching configuration")
            raise ValueError("Incorrect number of identifying elements when searching configuration")

        search_id = "_".join([(x is not None and x) or "" for x in args])
        matching_entries = []
        for regex_pattern, entry_info in self.config_storage:
            m = regex_pattern.match(search_id)
            if m is None:
                continue

            matching_entries.append(self.prepare_config_entry(entry_info, args))

        if len(matching_entries) != 0:
            return matching_entries
        else:
            raise ValueError("No config entry found matching: '%s'" % (search_id,))


class BackendRole(object):
    """Polar2Grid base class for Backends.

    Backends are responsible for taking image data mapped to a uniform grid, rescaling it, and then writing it
    to a file format on disk.
    """
    __metaclass__ = ABCMeta

    def __init__(self, overwrite_existing=False, keep_intermediate=False, exit_on_error=True, **kwargs):
        self.overwrite_existing = overwrite_existing
        self.keep_intermediate = keep_intermediate
        self.exit_on_error = exit_on_error

    @property
    @abstractmethod
    def known_grids(self):
        """Provide a list of known grids that this backend knows how to handle. For all grids use `None`.
        """
        return None

    def create_output_filename(self, pattern, satellite, instrument, product_name, grid_name, **kwargs):
        """Helper function that will take common meta data and put it into
        the output filename pattern provided. If either of the keyword arguments
        ``begin_time`` or ``end_time`` are not specified the other is used
        in its place.  If neither are specified the current time in UTC is
        taken.

        Some arguments are handled in special ways:
            - begin_time : begin_time is converted into 5 different strings
                that can each be individually specified in the pattern:
                    * begin_time     : YYYYMMDD_HHMMSS
                    * begin_YYYYMMDD : YYYYMMDD
                    * begin_YYMMDD   : YYMMDD
                    * begin_HHMMSS   : HHMMSS
                    * begin_HHMM     : HHMM
            - end_time   : Same as begin_time

        If a keyword is provided that is not recognized it will be provided
        to the pattern after running through a `str` filter.

        Possible pattern keywords:
            - satellite       : identifier for the instrument's satellite
            - instrument      : name of the instrument
            - product_name    : name of the product in the output
            - data_kind       : kind of data (brightness temperature, radiance, reflectance, etc.)
            - data_type       : data type name of data in-memory (ex. uint1, int4, real4)
            - grid_name       : name of the grid the data was mapped to
            - columns         : number of columns in the data
            - rows            : number of rows in the data
            - begin_time      : begin time of the first scan (YYYYMMDD_HHMMSS)
            - begin_YYYYMMDD : begin date of the first scan
            - begin_YYMMDD   : begin date of the first scan
            - begin_HHMMSS   : begin time of the first scan
            - begin_HHMM     : begin time of the first scan
            - end_time        : end time of the first scan. Same keywords as start_time.

        >>> from datetime import datetime
        >>> pattern = "{satellite}_{instrument}_{product_name}_{data_kind}_{grid_name}_{start_time}.{data_type}.{columns}.{rows}"
        >>> class FakeBackend(BackendRole):
        ...     def create_output_from_product(self, gridded_product, **kwargs): pass
        ...     @property
        ...     def known_grids(self): return None
        >>> backend = FakeBackend()
        >>> filename = backend.create_output_filename(pattern,
        ...     "npp",
        ...     "viirs",
        ...     "i04",
        ...     data_kind="btemp",
        ...     grid_name="wgs84_fit",
        ...     data_type="uint1",
        ...     columns = 2500, rows=3000, begin_time=datetime(2012, 11, 10, 9, 8, 7))
        >>> print(filename)
        npp_viirs_i04_btemp_wgs84_fit_20121110_090807.uint1.2500.3000

        """
        # Keyword arguments
        data_type = kwargs.pop("data_type", None)
        data_kind = kwargs.pop("data_kind", None)
        columns = kwargs.pop("columns", None)
        rows = kwargs.pop("rows", None)
        begin_time_dt = kwargs.pop("begin_time", None)
        end_time_dt = kwargs.pop("end_time", None)

        if data_type and not isinstance(data_type, str):
            data_type = dtype_to_str(data_type)

        # Convert begin time and end time
        if begin_time_dt is None and end_time_dt is None:
            begin_time_dt = end_time_dt = datetime.utcnow()
        elif begin_time_dt is None:
            begin_time_dt = end_time_dt
        elif end_time_dt is None:
            end_time_dt = begin_time_dt

        begin_YYYYMMDD = begin_time_dt.strftime("%Y%m%d")
        begin_YYMMDD = begin_time_dt.strftime("%y%m%d")
        begin_HHMMSS = begin_time_dt.strftime("%H%M%S")
        begin_HHMM = begin_time_dt.strftime("%H%M")
        # backwards compatibility: if they didn't specify a format for the
        #
        if "begin_time:" not in pattern:
            begin_time = begin_time_dt.strftime("%Y%m%d_%H%M%S")
        else:
            begin_time = begin_time_dt
        end_YYYYMMDD = end_time_dt.strftime("%Y%m%d")
        end_YYMMDD = end_time_dt.strftime("%y%m%d")
        end_HHMMSS = end_time_dt.strftime("%H%M%S")
        end_HHMM = end_time_dt.strftime("%H%M")
        if "end_time:" not in pattern:
            end_time = end_time_dt.strftime("%Y%m%d_%H%M%S")
        else:
            end_time = end_time_dt

        try:
            output_filename = pattern.format(**dict(
                satellite=satellite,
                instrument=instrument,
                product_name=product_name,
                data_kind=data_kind,
                data_type=data_type,
                grid_name=grid_name,
                columns=columns,
                rows=rows,
                begin_time=begin_time,
                begin_YYYYMMDD=begin_YYYYMMDD,
                begin_YYMMDD=begin_YYMMDD,
                begin_HHMMSS=begin_HHMMSS,
                begin_HHMM=begin_HHMM,
                end_time=end_time,
                end_YYYYMMDD=end_YYYYMMDD,
                end_YYMMDD=end_YYMMDD,
                end_HHMMSS=end_HHMMSS,
                end_HHMM=end_HHMM,
                **kwargs
            ))
        except KeyError as e:
            LOG.error("Unknown output pattern key: '%s'" % (str(e),))
            raise

        return output_filename

    def create_output_filename_old(self, pattern, satellite, instrument, product_name, grid_name, **kwargs):
        """Helper function that will take common meta data and put it into
        the output filename pattern provided. If either of the keyword arguments
        ``begin_time`` or ``end_time`` are not specified the other is used
        in its place.  If neither are specified the current time in UTC is
        taken.

        Some arguments are handled in special ways:
            - begin_time : begin_time is converted into 5 different strings
                that can each be individually specified in the pattern:
                    * begin_time     : YYYYMMDD_HHMMSS
                    * begin_YYYYMMDD : YYYYMMDD
                    * begin_YYMMDD   : YYMMDD
                    * begin_HHMMSS   : HHMMSS
                    * begin_HHMM     : HHMM
            - end_time   : Same as begin_time

        If a keyword is provided that is not recognized it will be provided
        to the pattern after running through a `str` filter.

        Possible pattern keywords:
            - satellite       : identifier for the instrument's satellite
            - instrument      : name of the instrument
            - product_name    : name of the product in the output
            - data_kind       : kind of data (brightness temperature, radiance, reflectance, etc.)
            - data_type       : data type name of data in-memory (ex. uint1, int4, real4)
            - grid_name       : name of the grid the data was mapped to
            - columns         : number of columns in the data
            - rows            : number of rows in the data
            - begin_time      : begin time of the first scan (YYYYMMDD_HHMMSS)
            - begin_YYYYMMDD  : begin date of the first scan
            - begin_YYMMDD    : begin date of the first scan
            - begin_HHMMSS    : begin time of the first scan
            - begin_HHMM      : begin time of the first scan
            - end_time        : end time of the first scan. Same keywords as start_time.

        >>> from datetime import datetime
        >>> pattern = "%(satellite)s_%(instrument)s_%(product_name)s_%(data_kind)s_%(grid_name)s_%(start_time)s.%(data_type)s.%(columns)s.%(rows)s"
        >>> class FakeBackend(BackendRole):
        ...     def create_output_from_product(self, gridded_product, **kwargs): pass
        ...     @property
        ...     def known_grids(self): return None
        >>> backend = FakeBackend()
        >>> filename = backend.create_output_filename_old(pattern,
        ...     "npp",
        ...     "viirs",
        ...     "i04",
        ...     data_kind="btemp",
        ...     grid_name="wgs84_fit",
        ...     data_type="uint1",
        ...     columns = 2500, rows=3000, begin_time=datetime(2012, 11, 10, 9, 8, 7))
        >>> print(filename)
        npp_viirs_i04_btemp_wgs84_fit_20121110_090807.uint1.2500.3000

        """
        # Keyword arguments
        data_type = kwargs.pop("data_type", None)
        data_kind = kwargs.pop("data_kind", None)
        columns = kwargs.pop("columns", None)
        rows = kwargs.pop("rows", None)
        begin_time_dt = kwargs.pop("begin_time", None)
        end_time_dt = kwargs.pop("end_time", None)

        if data_type and not isinstance(data_type, str):
            data_type = dtype_to_str(data_type)

        # Convert begin time and end time
        if begin_time_dt is None and end_time_dt is None:
            begin_time_dt = end_time_dt = datetime.utcnow()
        elif begin_time_dt is None:
            begin_time_dt = end_time_dt
        elif end_time_dt is None:
            end_time_dt   = begin_time_dt

        begin_time = begin_time_dt.strftime("%Y%m%d_%H%M%S")
        begin_YYYYMMDD = begin_time_dt.strftime("%Y%m%d")
        begin_YYMMDD = begin_time_dt.strftime("%y%m%d")
        begin_HHMMSS = begin_time_dt.strftime("%H%M%S")
        begin_HHMM = begin_time_dt.strftime("%H%M")
        end_time = end_time_dt.strftime("%Y%m%d_%H%M%S")
        end_YYYYMMDD = end_time_dt.strftime("%Y%m%d")
        end_YYMMDD = end_time_dt.strftime("%y%m%d")
        end_HHMMSS = end_time_dt.strftime("%H%M%S")
        end_HHMM = end_time_dt.strftime("%H%M")

        try:
            output_filename = pattern % dict(
                satellite=satellite,
                instrument=instrument,
                product_name=product_name,
                data_kind=data_kind,
                data_type=data_type,
                grid_name=grid_name,
                columns=columns,
                rows=rows,
                begin_time=begin_time,
                begin_YYYYMMDD=begin_YYYYMMDD,
                begin_YYMMDD=begin_YYMMDD,
                begin_HHMMSS=begin_HHMMSS,
                begin_HHMM=begin_HHMM,
                end_time=end_time,
                end_YYYYMMDD=end_YYYYMMDD,
                end_YYMMDD=end_YYMMDD,
                end_HHMMSS=end_HHMMSS,
                end_HHMM=end_HHMM,
                **kwargs
            )
        except KeyError as e:
            LOG.error("Unknown output pattern key: '%s'" % (str(e),))
            raise

        return output_filename

    def create_output_from_scene(self, gridded_scene, **kwargs):
        """Create output files for each product in the scene.

        Default implementation is to call `create_output_from_product` for each product in the provided `gridded_scene`.

        :param gridded_scene: `GriddedScene` object to create output from
        :returns: list of created output files
        """
        output_filenames = []
        for product_name, gridded_product in gridded_scene.items():
            try:
                output_fn = self.create_output_from_product(gridded_product, **kwargs)
                output_filenames.append(output_fn)
            except (ValueError, KeyError, RuntimeError):
                LOG.error("Could not create output for '%s'", product_name)
                if self.exit_on_error:
                    raise
                LOG.debug("Backend exception: ", exc_info=True)
                continue
        return output_filenames

    @abstractmethod
    def create_output_from_product(self, gridded_product, **kwargs):
        """Create output file for the provided product.

        :param gridded_product: `GriddedProduct` object to create output from
        :returns: Created output filename
        """
        pass


class FrontendRole(object):
    """Polar2Grid base class for Frontends.

    Frontends are responsible for extracting data from data files and providing that data to other Polar2Grid components
    as a `SwathScene`.
    """
    __metaclass__ = ABCMeta
    FILE_EXTENSIONS = []

    def __init__(self, search_paths=None, overwrite_existing=False, keep_intermediate=False, exit_on_error=True,
                 **kwargs):
        self.overwrite_existing = overwrite_existing
        self.keep_intermediate = keep_intermediate
        self.exit_on_error = exit_on_error
        self.search_paths = search_paths
        if not self.search_paths:
            LOG.info("No files or paths provided as input, will search the current directory...")
            self.search_paths = ['.']

    @property
    @abstractmethod
    def begin_time(self):
        """Datetime object of first observed data point loaded by Frontend.
        """
        pass

    @property
    @abstractmethod
    def end_time(self):
        """Datetime object of last observed data point loaded by Frontend.
        """
        pass

    @property
    @abstractmethod
    def available_product_names(self):
        """Names of data products that can be created from the data loaded during initialization.
        """
        pass

    @property
    @abstractmethod
    def all_product_names(self):
        """All product names that this Frontend knows how to create (assuming the proper data is available).
        """
        pass

    @abstractmethod
    def create_scene(self, products=None, **kwargs):
        """Create a `SwathScene` object with the specified products in it (all raw products by default).

        :param products: List of product names to create
        :returns: `SwathScene` object
        """
        pass

    def find_files_with_extensions(self, extensions=None, search_paths=None, warn_invalid=True):
        """Generator that uses `self.search_paths` to yield any file with extensions from `FILE_EXTENSIONS`.

        Extensions must include the period at the beginning (ex: .hdf).
        """
        extensions = extensions if extensions is not None else self.FILE_EXTENSIONS
        search_paths = search_paths if search_paths is not None else self.search_paths
        for p in search_paths:
            if os.path.isdir(p):
                LOG.debug("Searching '%s' for useful files", p)
                for fn in os.listdir(p):
                    fp = os.path.join(p, fn)
                    ext = os.path.splitext(fp)[1]
                    if ext in extensions:
                        yield os.path.abspath(fp)
            elif os.path.isfile(p):
                ext = os.path.splitext(p)[1]
                print(p, ext, extensions)
                if ext in extensions:
                    yield os.path.abspath(p)
                elif warn_invalid:
                    LOG.warning("File is not a valid file for this frontend: %s", p)
            else:
                LOG.error("File or directory does not exist: %s", p)

    def loadable_products(self, desired_products):
        orig_products = set(desired_products)
        available_products = self.available_product_names
        all_products = self.all_product_names
        doable_products = orig_products & set(available_products)
        for p in (orig_products - doable_products):
            if p not in all_products:
                LOG.error("Unknown product name: %s", p)
                raise RuntimeError("Unknown product name: %s" % (p,))
            else:
                LOG.warning("Missing proper data files to create product: %s", p)
        products = list(doable_products)
        if not products:
            LOG.debug("Original Products:\n\t%r", orig_products)
            LOG.debug("Available Products:\n\t%r", available_products)
            LOG.debug("Doable (final) Products:\n\t%r", products)
            LOG.error("Can not create any of the requested products (missing required data files)")
            raise RuntimeError("Can not create any of the requested products (missing required data files)")
        return products


class CartographerRole(object):
    """Polar2grid role for managing grids. Grid information such as
    the projection, the projection's parameters, pixel size, grid height,
    grid width, and grid origin are stored in the Cartographer and can be
    accessed via the ``CartographerRole.get_grid_info`` method.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def add_grid_config(self, grid_config_filename):
        """Add the grids and their information to this objects internal
        store of grid information. The format of the grid configuration
        ultimately depends on the Cartographer implementation. This method
        should not erase previously added configuration files, but it will
        overwrite a ``grid_name`` that was added earlier.
        """
        raise NotImplementedError("Child class must implement this method")


class CompositorRole(object):
    __metaclass__ = ABCMeta

    def __init__(self, overwrite_existing=False, keep_intermediate=False, exit_on_error=True, **kwargs):
        self.overwrite_existing = overwrite_existing
        self.keep_intermediate = keep_intermediate
        self.exit_on_error = exit_on_error

    def _create_gridded_product(self, product_name, grid_data, base_product=None, **kwargs):
        from polar2grid.core.containers import GriddedProduct
        if base_product is None:
            base_product = kwargs
        else:
            base_product = base_product.copy(as_dict=True)
            base_product.update(kwargs)
        base_product["product_name"] = product_name
        base_product["grid_data"] = grid_data

        if base_product.get("grid_definition") is None:
            msg = "No grid definition provided to base composite on (use `base_product` or `grid_definition`)"
            LOG.error(msg)
            raise ValueError(msg)

        return GriddedProduct(**base_product)

    @abstractmethod
    def modify_scene(self, gridded_scene, fill_value=None, **kwargs):
        pass


def main():
    """Run some tests on the interfaces/roles
    """
    import doctest
    return doctest.testmod()

if __name__ == "__main__":
    sys.exit(main())
