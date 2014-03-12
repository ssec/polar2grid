#!/usr/bin/env python
# encoding: utf-8
"""Functions to read configuration files for the AWIPS backend.

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

from xml.etree import cElementTree
from polar2grid.nc import ncml_tag
from polar2grid.core.constants import NOT_APPLICABLE
from polar2grid.core import roles

import os
import sys
import logging

log = logging.getLogger(__name__)

script_dir = os.path.split(os.path.realpath(__file__))[0]
# Default config file if none is specified
DEFAULT_CONFIG_NAME = "awips_grids.conf"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_NAME
# Default search directory for any awips configuration files
DEFAULT_CONFIG_DIR = script_dir
# Default search directory for NCML files
DEFAULT_NCML_DIR = os.path.join(script_dir, "ncml")

# Get configuration file locations
CONFIG_FILE = os.environ.get("AWIPS_CONFIG_FILE", DEFAULT_CONFIG_FILE)
CONFIG_DIR  = os.environ.get("AWIPS_CONFIG_DIR", DEFAULT_CONFIG_DIR)
NCML_DIR    = os.environ.get("AWIPS_NCML_DIR", DEFAULT_NCML_DIR)

def _create_config_id(sat, instrument, nav_set_uid, kind, band, data_kind, grid_name=None):
    if grid_name is None:
        # This is used for searching the configs
        return "_".join([sat, instrument, nav_set_uid or "", kind, band or "", data_kind])
    else:
        # This is used for adding to the configs
        return "_".join([sat, instrument, nav_set_uid or "", kind, band or "", data_kind, grid_name])

def _rel_to_abs(filename, default_base_path):
    """Function that checks if a filename provided is not an absolute
    path.  If it is not, then it checks if the file exists in the current
    working directory.  If it does not exist in the cwd, then the default
    base path is used.  If that file does not exist an exception is raised.
    """
    if not os.path.isabs(filename):
        cwd_filepath = os.path.join(os.path.curdir, filename)
        if os.path.exists(cwd_filepath):
            filename = cwd_filepath
        else:
            filename = os.path.join(default_base_path, filename)
    filename = os.path.realpath(filename)

    if not os.path.exists(filename):
        log.error("File '%s' could not be found" % (filename,))
        raise ValueError("File '%s' could not be found" % (filename,))

    return filename

def load_config_str(config_dict, config_str):
    # Get rid of trailing new lines and commas
    config_lines = [ line.strip(",\n") for line in config_str.split("\n") ]
    # Get rid of comment lines and blank lines
    config_lines = [ line for line in config_lines if line and not line.startswith("#") and not line.startswith("\n") ]
    # Check if we have any useful lines
    if not config_lines:
        log.warning("No non-comment lines were found in AWIPS config")
        return False

    try:
        # Parse config lines
        for line in config_lines:
            parts = [ part.strip() for part in line.split(",") ]
            if len(parts) != 13:
                log.error("AWIPS config line needs exactly 12 columns : '%s'" % (line,))
                raise ValueError("AWIPS config line needs exactly 12 columns : '%s'" % (line,))

            # Verify that each identifying portion is valid
            for i in range(7):
                assert parts[i],"Field %d can not be empty" % i
                # polar2grid demands lowercase fields
                parts[i] = parts[i].lower()

            # Convert nav_set_uid if none
            if parts[2] == '' or parts[2] == "none":
                parts[2] = NOT_APPLICABLE

            # Convert band if none
            if parts[4] == '' or parts[4] == "none":
                parts[4] = NOT_APPLICABLE

            line_id = _create_config_id(*parts[:7])
            if line_id in config_dict:
                log.error("AWIPS config has 2 entries for %s" % (line_id,))
                raise ValueError("AWIPS config has 2 entries for %s" % (line_id,))

            # Parse out the awips specific elements
            product_id = parts[7]
            awips2_channel = parts[8]
            awips2_source = parts[9]
            awips2_satellitename = parts[10]
            ncml_template = _rel_to_abs(parts[11], NCML_DIR)
            nc_format = parts[12]
            config_entry = {
                    "grid_name" : parts[6],
                    "product_id" : product_id,
                    "awips2_channel" : awips2_channel,
                    "awips2_source" : awips2_source,
                    "awips2_satellitename" : awips2_satellitename,
                    "ncml_template" : ncml_template,
                    "nc_format" : nc_format
                    }
            config_dict[line_id] = config_entry
    except StandardError:
        # Clear out the bad config
        raise

    return True

def load_config(config_dict, config_filepath):
    # Load a configuration file, even if it's in the package
    full_config_filepath = os.path.realpath(os.path.expanduser(config_filepath))
    config_str = None
    if not os.path.exists(full_config_filepath):
        try:
            config_str = get_resource_string(__name__, config_filepath)
            log.debug("Using package provided AWIPS configuration '%s'" % (config_filepath,))
        except StandardError:
            log.error("AWIPS file '%s' could not be found" % (config_filepath,))
            raise ValueError("AWIPS file '%s' could not be found" % (config_filepath,))

    if config_str is not None:
        return load_config_str(config_dict, config_str)
    else:
        log.debug("Using AWIPS configuration '%s'" % (config_filepath,))
        config_file = open(config_filepath, 'r')
        config_str = config_file.read()
        return load_config_str(config_dict, config_str)

def can_handle_inputs(config_dict, sat, instrument, nav_set_uid, kind, band, data_kind):
    """Search through the configuration files and return all the grids for
    this band and data_kind
    """
    band_id = _create_config_id(sat, instrument, nav_set_uid, kind, band, data_kind)
    log.debug("Searching AWIPS configs for '%s'" % (band_id,))
    grids = []
    for k in config_dict.keys():
        if k.startswith(band_id):
            grids.append(config_dict[k]["grid_name"])
    return grids

def get_awips_info(config_dict, sat, instrument, nav_set_uid, kind, band, data_kind, grid_name):
    config_id = _create_config_id(sat, instrument, nav_set_uid, kind, band, data_kind, grid_name)
    if config_id not in config_dict:
        log.error("'%s' could not be found in the loaded configuration, available '%r'" % (config_id,config_dict.keys()))
        raise ValueError("'%s' could not be found in the loaded configuration" % (config_id,))

    return config_dict[config_id]

class AWIPSConfigReader(roles.CSVConfigReader):
    """Read an AWIPS Backend Configuration file

    Example:
    npp,viirs,i_nav,i,01,reflectance,211w,55779608,0.64 um,SSEC,NPP-VIIRS,grid211w.ncml,SSEC_AWIPS_VIIRS-WCONUS_1KM_SVI01_%Y%m%d_%H%M.55779608
    """
    NUM_ID_ELEMENTS = 6

    def parse_entry_parts(self, entry_parts):
        # Parse out the awips specific elements
        grid_name = entry_parts[0]
        product_id = entry_parts[1]
        awips2_channel = entry_parts[2]
        awips2_source = entry_parts[3]
        awips2_satellitename = entry_parts[4]
        ncml_template = _rel_to_abs(entry_parts[5], NCML_DIR)
        nc_format = entry_parts[6]
        config_entry = {
                "grid_name" : grid_name,
                "product_id" : product_id,
                "awips2_channel" : awips2_channel,
                "awips2_source" : awips2_source,
                "awips2_satellitename" : awips2_satellitename,
                "ncml_template" : ncml_template,
                "nc_format" : nc_format
                }
        return config_entry

    def get_config_entry(self, *args, **kwargs):
        if len(args) == self.NUM_ID_ELEMENTS:
            try:
                return super(AWIPSConfigReader, self).get_config_entry(*args, **kwargs)
            except ValueError:
                log.error("'%s' could not be found in the loaded configuration" % (args,))
                raise ValueError("'%s' could not be found in the loaded configuration" % (args,))
        else:
            for config_info in self.get_all_matching_entries(*args[:-1]):
                if config_info["grid_name"] == args[-1]:
                    return config_info
            log.error("'%s' could not be found in the loaded configuration" % (args,))
            raise ValueError("'%s' could not be found in the loaded configuration" % (args,))

if __name__ == "__main__":
    sys.exit(0)
