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

"""
__docformat__ = "restructuredtext en"

import sys

import logging
import os
from ConfigParser import NoSectionError, NoOptionError

from polar2grid.core import roles

LOG = logging.getLogger(__name__)

# Default search directory for NCML files
script_dir = os.path.split(os.path.realpath(__file__))[0]
DEFAULT_NCML_DIR = os.path.join(script_dir, "ncml")

# Get configuration file locations
CONFIG_FILE = os.environ.get("AWIPS_CONFIG_FILE", "polar2grid.awips:awips_backend.ini")
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
        LOG.error("File '%s' could not be found" % (filename,))
        raise ValueError("File '%s' could not be found" % (filename,))

    return filename


class AWIPS2ConfigReader(roles.SimpleINIConfigReader):
    SECTION_PREFIX = "awips:"
    SOURCE_SECTION = SECTION_PREFIX + "source"
    PRODUCT_SECTION_PREFIX = SECTION_PREFIX + "product:"
    GRID_SECTION_PREFIX = SECTION_PREFIX + "grid:"
    SAT_SECTION_PREFIX = SECTION_PREFIX + "satellite:"

    def __init__(self, *config_files, **kwargs):
        super(AWIPS2ConfigReader, self).__init__(*config_files, **kwargs)

    @property
    def known_grids(self):
        return [x.split(":")[-1] for x in self.config_parser.sections() if x.startswith(self.GRID_SECTION_PREFIX)]

    def get_filename_format(self, default=None):
        try:
            return self.config_parser.get(self.SOURCE_SECTION, "filename_scheme")
        except (NoOptionError, NoSectionError):
            return default

    def get_source_name(self, default='SSEC'):
        try:
            return self.config_parser.get(self.SOURCE_SECTION, "source_name")
        except (NoOptionError, NoSectionError):
            return default

    def get_grid_info(self, grid_def):
        info = {}
        section = self.GRID_SECTION_PREFIX + grid_def["grid_name"]
        info["depictor_name"] = self.config_parser.get(section, "depictor_name")
        for opt in self.config_parser.options(section):
            LOG.debug("Parsing '%s' from AWIPS configuration file", opt)
            if opt in ["depictor_name", "projname"]:
                info[opt] = self.config_parser.get(section, opt)
            elif opt in ["projindex"]:
                info[opt] = self.config_parser.getint(section, opt)
            else:
                info[opt] = self.config_parser.getfloat(section, opt)

        return info

    def get_product_info(self, product_definition):
        info = {}
        product_section = self.PRODUCT_SECTION_PREFIX + product_definition["product_name"]
        sat_section = self.SAT_SECTION_PREFIX + product_definition["satellite"] + ":" + product_definition["instrument"]
        info["channel"] = self.config_parser.get(product_section, "channel")
        try:
            info["satellite_name"] = self.config_parser.get(sat_section, "satellite_name")
        except NoSectionError:
            # default if the configuration file isn't set
            info["satellite_name"] = product_definition["instrument"].upper()
        info["source_name"] = self.get_source_name()
        return info


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
        LOG.debug("Loading AWIPS configuration files:\n\t%s", "\n\t".join(config_files))
        super(AWIPSConfigReader, self).__init__(*config_files, **kwargs)

    @property
    def known_grids(self):
        sections = (x[-1] for x in self.config)
        return list(set(self.config_parser.get(section_name, "grid_name") for section_name in sections))

    def get_product_options(self, gridded_product):
        all_meta = gridded_product["grid_definition"].copy(as_dict=True)
        all_meta.update(**gridded_product)
        kwargs = dict((k, all_meta.get(k, None)) for k in self.id_fields)
        try:
            awips_info = self.get_config_options(allow_default=False, **kwargs)
            awips_info = dict((k, awips_info[k]) for k in self.info_fields)
            awips_info["ncml_template"] = _rel_to_abs(awips_info["ncml_template"], NCML_DIR)
        except StandardError:
            LOG.error("Could not find an AWIPS configuration section for '%s'" % (all_meta["product_name"],))
            LOG.debug("Configuration Error: ", exc_info=True)
            raise RuntimeError("Could not find an AWIPS configuration section for '%s'" % (all_meta["product_name"],))
        return awips_info

if __name__ == "__main__":
    sys.exit(0)
