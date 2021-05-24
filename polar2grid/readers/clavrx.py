#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2017 Space Science and Engineering Center (SSEC),
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
#     Written by David Hoese    June 2017
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""The CLAVR-x reader is for reading files created by the Community
Satellite Processing Package (CSPP) Clouds from AVHRR Extended
(CLAVR-x) processing system software. The CLAVR-x reader
supports CSPP CLAVR-x product files created from VIIRS, MODIS
and AVHRR imaging sensors in the native HDF4 format.
The reader can be specified with the ``polar2grid.sh``
command using the ``clavrx`` reader name.
The CLAVR-x reader provides the following products, which include
support for the VIIRS Day/Night Band Lunar Reflectance:

+------------------------+---------------------------------------------+
| Product Name           | Description                                 |
+========================+=============================================+
| cloud_type             | Cloud Type                                  |
+------------------------+---------------------------------------------+
| cld_height_acha        | Cloud Top Height (m)                        |
+------------------------+---------------------------------------------+
| cld_temp_acha          | Cloud Top Temperature (K)                   |
+------------------------+---------------------------------------------+
| cld_emiss_acha         | Cloud Emissivity                            |
+------------------------+---------------------------------------------+
| cld_opd_dcomp          | Cloud Optical Depth Daytime                 |
+------------------------+---------------------------------------------+
| cld_opd_nlcomp         | Cloud Optical Depth Nighttime               |
+------------------------+---------------------------------------------+
| cld_reff_dcomp         | Cloud Effective Radius Daytime (micron)     |
+------------------------+---------------------------------------------+
| cld_reff_nlomp         | Cloud Effective Radius Nighttime (micron)   |
+------------------------+---------------------------------------------+
| cloud_phase            | Cloud Phase  (5 categories)                 |
+------------------------+---------------------------------------------+
| rain_rate              | Rain Rate (mm/hr)                           |
+------------------------+---------------------------------------------+
| refl_lunar_dnb_nom     | Lunar Reflectance (VIIRS DNB nighttime only)|
+------------------------+---------------------------------------------+

"""
from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
import os
import sys
import logging
import numpy as np
from ._base import ReaderProxyBase
from polar2grid.readers import ReaderWrapper, main

LOG = logging.getLogger(__name__)

# Limit the number of products shown to Polar2Grid users
# if the user uses the environment variable they can display more
ADVERTISED_DATASETS = os.environ.get("CLAVRX_AD_DATASETS", None)
if ADVERTISED_DATASETS == "all":
    ADVERTISED_DATASETS = None
elif ADVERTISED_DATASETS:
    ADVERTISED_DATASETS = ADVERTISED_DATASETS.split(" ")
else:
    ADVERTISED_DATASETS = set(
        [
            "cloud_type",
            "cld_temp_acha",
            "cld_height_acha",
            "cloud_phase",
            "cld_opd_dcomp",
            "cld_opd_nlcomp",
            "cld_reff_dcomp",
            "cld_reff_nlcomp",
            "cld_emiss_acha",
            "refl_lunar_dnb_nom",
            "rain_rate",
        ]
    )

DAY_ONLY = ["cld_opd_dcomp", "cld_reff_dcomp"]
NIGHT_ONLY = ["cld_opd_nlcomp", "cld_reff_nlcomp", "refl_lunar_dnb_nom"]

FILE_EXTENSIONS = [".hdf"]
DEFAULT_READER_NAME = "clavrx"
DEFAULT_DATASETS = [
    "cloud_type" "cld_temp_acha",
    "cld_height_acha",
    "cloud_phase",
    "cld_opd_dcomp",
    "cld_opd_nlcomp",
    "cld_reff_dcomp",
    "cld_reff_nlcomp",
    "cld_emiss_acha",
    "refl_lunar_dnb_nom",
    "rain_rate",
]


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_geo2grid_reader = True
    is_polar2grid_reader = True

    def available_product_names(self) -> sorted(set(str)):
        return sorted(set(self.scn.available_dataset_names()))

    def available_product_names(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return set(ADVERTISED_DATASETS) & set(self.scn.all_dataset_names())

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return set(DEFAULT_DATASETS) & self.available_product_names()

    def filter(self, scn):
        self.filter_daynight_datasets(scn)

    def filter_daynight_datasets(self, scene):
        """Some products are only available at daytime or nighttime"""
        for k in DAY_ONLY + NIGHT_ONLY:
            if k in scene and scene[k].isnull().all():
                LOG.info("Removing dataset '{}' because it is completely empty".format(k))
                del scene[k]


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser."""
    return None, None
