#!/usr/bin/env python
# encoding: utf-8
"""Functions to read configuration files for the ninjo backend.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

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

# Get configuration file locations
script_dir = os.path.split(os.path.realpath(__file__))[0]
# Default config file if none is specified
DEFAULT_GRID_CONFIG_NAME = "ninjo_grids.conf"
DEFAULT_GRID_CONFIG_FILE = DEFAULT_GRID_CONFIG_NAME
DEFAULT_BAND_CONFIG_NAME = "ninjo_bands.conf"
DEFAULT_BAND_CONFIG_FILE = DEFAULT_BAND_CONFIG_NAME

# Get configuration file locations
GRID_CONFIG_FILE = os.environ.get("NINJO_GRID_CONFIG_FILE", DEFAULT_GRID_CONFIG_FILE)
BAND_CONFIG_FILE = os.environ.get("NINJO_BAND_CONFIG_FILE", DEFAULT_BAND_CONFIG_FILE)

def _create_config_id(sat, instrument, kind, band, data_kind, grid_name=None):
    # copy-pastaed from awips config
    if grid_name is None:
        # This is used for searching the configs
        return "_".join([sat, instrument, kind, band or "", data_kind])
    else:
        # This is used for adding to the configs
        return "_".join([sat, instrument, kind, band or "", data_kind, grid_name])

def parse_parts_grid_config(config_dict, parts):
    """The function that analyzes the line parts of a NinJo grid configuration
    file.
    """
    if len(parts) < 4:
        print "ERROR: Need at 4 columns in ninjo_grids.conf (%s)" % (parts.join(","),)
        return False
    grid_number = parts[0]
    nproj = parts[1]
    xres = float(parts[2])
    yres = float(parts[3])

    val = (nproj,xres,yres)
    config_dict[grid_number] = val

    return True

def parse_parts_band_config(config_dict, parts):
    """The function that analyzes the line parts of a NinJo band configuration
    file.
    """
    if len(parts) < 9:
        print "ERROR: Need at 9 columns in ninjo_bands.conf (%s)" % (parts.join(","),)
        return False

    config_entry_id = _create_config_id(*parts[:5])
    sat_id = int(parts[5])
    band_id = int(parts[6])
    data_source = parts[7]
    data_cat = parts[8]

    config_dict[config_entry_id] = {
            "sat_id"      : sat_id,
            "band_id"     : band_id,
            "data_source" : data_source,
            "data_cat"   : data_cat
            }

    return True

def load_config_str(config_dict, config_str, parse_parts):
    # Get rid of trailing new lines and commas
    config_lines = [ line.strip(",\n") for line in config_str.split("\n") ]
    # Get rid of comment lines and blank lines
    config_lines = [ line for line in config_lines if line and not line.startswith("#") and not line.startswith("\n") ]
    # Check if we have any useful lines
    if not config_lines:
        log.warning("No non-comment lines were found in NinJo config")
        return False

    # grid -> (nproj name, xres, yres)
    for line in config_lines:
        # For comments
        if line.startswith("#") or line.startswith("\n"): continue
        parts = [ part.strip() for part in line.split(",") ]
        parse_parts(config_dict, parts)

    return True

def load_config(config_dict, parse_parts, config_filepath=None):
    # Load a configuration file, even if it's in the package
    full_config_filepath = os.path.realpath(os.path.expanduser(config_filepath))
    if not os.path.exists(full_config_filepath):
        try:
            config_str = get_resource_string(__name__, config_filepath)
            log.debug("Using package provided NinJo configuration '%s'" % (config_filepath,))
            return load_config_str(config_dict, config_str, parse_parts)
        except StandardError:
            log.error("NinJo file '%s' could not be found" % (config_filepath,))
            raise ValueError("NinJo file '%s' could not be found" % (config_filepath,))

    log.debug("Using NinJo configuration '%s'" % (config_filepath,))

    config_file = open(config_filepath, 'r')
    config_str = config_file.read()
    return load_config_str(config_dict, config_str, parse_parts)

def load_grid_config(config_dict, config_filepath=None):
    if config_filepath is None: config_filepath = GRID_CONFIG_FILE
    return load_config(config_dict, parse_parts_grid_config, config_filepath=config_filepath)

def load_band_config(config_dict, config_filepath=None):
    if config_filepath is None: config_filepath = BAND_CONFIG_FILE
    return load_config(config_dict, parse_parts_band_config, config_filepath=config_filepath)

if __name__ == "__main__":
    sys.exit(0)
