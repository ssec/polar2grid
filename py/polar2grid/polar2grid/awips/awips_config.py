#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
#     input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    November 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Functions to read configuration files for the AWIPS backend.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2014
:license:      GNU GPLv3


"""
__docformat__ = "restructuredtext en"

from polar2grid.core import roles

import os
import sys
import logging

log = logging.getLogger(__name__)

script_dir = os.path.split(os.path.realpath(__file__))[0]
# Default config file if none is specified
DEFAULT_CONFIG_FILE = "awips_backend.ini"
# Default search directory for any awips configuration files
DEFAULT_CONFIG_DIR = script_dir
# Default search directory for NCML files
DEFAULT_NCML_DIR = os.path.join(script_dir, "ncml")

# Get configuration file locations
CONFIG_FILE = os.environ.get("AWIPS_CONFIG_FILE", DEFAULT_CONFIG_FILE)
CONFIG_DIR = os.environ.get("AWIPS_CONFIG_DIR", DEFAULT_CONFIG_DIR)
NCML_DIR = os.environ.get("AWIPS_NCML_DIR", DEFAULT_NCML_DIR)


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


class AWIPSConfigReader(roles.INIConfigReader):
    id_fields = (
        "product_name",
        "grid_name",
        "data_kind"
        "satellite",
        "instrument",
    )

    info_fields = (
        "grid_name",
        "product_id",
        "awips2_channel",
        "awips2_source",
        "awips2_satellite_name",
        "ncml_template",
        "filename_format",
    )

    def __init__(self, *config_files, **kwargs):
        kwargs["section_prefix"] = kwargs.get("section_prefix", "awips:")
        log.info("Loading AWIPS configuration files:\n\t%s", "\n\t".join(config_files))
        super(AWIPSConfigReader, self).__init__(*config_files, **kwargs)

    @property
    def known_grids(self):
        sections = (x[-1] for x in self.config)
        return list(set(self.config_parser.get(section_name, "grid_name") for section_name in sections))

    def get_product_options(self, gridded_product):
        all_meta = gridded_product["grid_definition"].copy()
        all_meta.update(**gridded_product)
        kwargs = dict((k, all_meta.get(k, None)) for k in self.id_fields)
        try:
            awips_info = self.get_config_options(allow_default=False, **kwargs)
            awips_info = dict((k, awips_info[k]) for k in self.info_fields)
            awips_info["ncml_template"] = _rel_to_abs(awips_info["ncml_template"], NCML_DIR)
        except StandardError:
            log.error("Could not find an AWIPS configuration section for '%s'" % (all_meta["product_name"],))
            log.debug("Configuration Error: ", exc_info=True)
            raise RuntimeError("Could not find an AWIPS configuration section for '%s'" % (all_meta["product_name"],))
        return awips_info

if __name__ == "__main__":
    sys.exit(0)
