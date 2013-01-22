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

import os
import sys
import logging

try:
    # try getting setuptools/distribute's version of resource retrieval first
    import pkg_resources
    get_resource_string = pkg_resources.resource_string
except ImportError:
    import pkgutil
    get_resource_string = pkgutil.get_data

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

# This isn't used anymore, but its a handy function to hold on to
# This was replaced by the grids/grids.py API which requires grid size to be
# in the grids.conf file
def get_shape_from_ncml(fn, var_name):
    """Returns (rows,cols) of the variable with name
    `var_name` in the ncml file with filename `fn`.
    """
    xml_parser = cElementTree.parse(fn)
    all_vars = xml_parser.findall(ncml_tag("variable"))
    important_var = [ elem for elem in all_vars if elem.get("name") == var_name]
    if len(important_var) != 1:
        log.error("Couldn't find a variable with name %s in the ncml file %s" % (var_name,fn))
        raise ValueError("Couldn't find a variable with name %s in the ncml file %s" % (var_name,fn))
    important_var = important_var[0]

    # Get the shape out
    shape = important_var.get("shape")
    if shape is None:
        log.error("NCML variable %s does not have the required shape attribute" % (var_name,))
        raise ValueError("NCML variable %s does not have the required shape attribute" % (var_name,))

    # Get dimension names from shape attribute
    shape_dims = shape.split(" ")
    if len(shape_dims) != 2:
        log.error("2 dimensions are required for variable %s" % (var_name,))
        raise ValueError("2 dimensions are required for variable %s" % (var_name,))
    rows_name,cols_name = shape_dims

    # Get the dimensions by their names
    all_dims = xml_parser.findall(ncml_tag("dimension"))
    important_dims = [ elem for elem in all_dims if elem.get("name") == rows_name or elem.get("name") == cols_name ]
    if len(important_dims) != 2:
        log.error("Corrupt NCML file %s, can't find both of %s's dimensions" % (fn, var_name))
        raise ValueError("Corrupt NCML file %s, can't find both of %s's dimensions" % (fn, var_name))

    if important_dims[0].get("name") == rows_name:
        rows = int(important_dims[0].get("length"))
        cols = int(important_dims[1].get("length"))
    else:
        rows = int(important_dims[1].get("length"))
        cols = int(important_dims[0].get("length"))
    return rows,cols

def _create_config_id(sat, instrument, kind, band, data_kind, grid_name=None):
    if grid_name is None:
        # This is used for searching the configs
        return "_".join([sat, instrument, kind, band or "", data_kind])
    else:
        # This is used for adding to the configs
        return "_".join([sat, instrument, kind, band or "", data_kind, grid_name])

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
            if len(parts) != 12:
                log.error("AWIPS config line needs exactly 12 columns : '%s'" % (line,))
                raise ValueError("AWIPS config line needs exactly 12 columns : '%s'" % (line,))

            # Verify that each identifying portion is valid
            for i in range(6):
                assert parts[i],"Field %d can not be empty" % i
                # polar2grid demands lowercase fields
                parts[i] = parts[i].lower()

            # Convert band if none
            if parts[3] == '' or parts[3] == "none":
                parts[3] = NOT_APPLICABLE

            line_id = _create_config_id(*parts[:6])
            if line_id in config_dict:
                log.error("AWIPS config has 2 entries for %s" % (line_id,))
                raise ValueError("AWIPS config has 2 entries for %s" % (line_id,))

            # Parse out the awips specific elements
            product_id = parts[6]
            awips2_channel = parts[7]
            awips2_source = parts[8]
            awips2_satellitename = parts[9]
            ncml_template = _rel_to_abs(parts[10], NCML_DIR)
            nc_format = parts[11]
            config_entry = {
                    "grid_name" : parts[5],
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

def load_config(config_dict, config_filepath=None):
    if config_filepath is None:
        config_filepath = CONFIG_FILE

    # Load a configuration file, even if it's in the package
    full_config_filepath = os.path.realpath(os.path.expanduser(config_filepath))
    if not os.path.exists(full_config_filepath):
        try:
            config_str = get_resource_string(__name__, config_filepath)
            log.debug("Using package provided AWIPS configuration '%s'" % (config_filepath,))
            return load_config_str(config_dict, config_str)
        except StandardError:
            log.error("AWIPS file '%s' could not be found" % (config_filepath,))
            raise ValueError("AWIPS file '%s' could not be found" % (config_filepath,))

    log.debug("Using AWIPS configuration '%s'" % (config_filepath,))

    config_file = open(config_filepath, 'r')
    config_str = config_file.read()
    return load_config_str(config_dict, config_str)

def can_handle_inputs(config_dict, sat, instrument, kind, band, data_kind):
    """Search through the configuration files and return all the grids for
    this band and data_kind
    """
    band_id = _create_config_id(sat, instrument, kind, band, data_kind)
    log.debug("Searching AWIPS configs for '%s'" % (band_id,))
    grids = []
    for k in config_dict.keys():
        if k.startswith(band_id):
            grids.append(config_dict[k]["grid_name"])
    return grids

def get_awips_info(config_dict, sat, instrument, kind, band, data_kind, grid_name):
    config_id = _create_config_id(sat, instrument, kind, band, data_kind, grid_name)
    if config_id not in config_dict:
        log.error("'%s' could not be found in the loaded configuration, available '%r'" % (config_id,config_dict.keys()))
        raise ValueError("'%s' could not be found in the loaded configuration" % (config_id,))

    return config_dict[config_id]

if __name__ == "__main__":
    sys.exit(0)
