#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2019 Space Science and Engineering Center (SSEC),
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
#     Written by William Roberts and David Hoese    May 2019
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     wroberts4@wisc.edu and david.hoese@ssec.wisc.edu
"""The VIRR Level 1B reader operates on Level 1B (L1B) HDF5 files.

Files usually have the following naming scheme:

    tf2018343030324.FY3C-L_VIRRX_L1B.HDF or tf2018343092538.FY3B-L_VIRRX_L1B.HDF
    the numbers at the start are year julian-day hour minute seconds

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--fornav-D`` parameter is set to 40 and the
``--fornav-d`` parameter is set to 1.

+---------------------------+-----------------------------------------------------+-------------------------+
| **Product Name**          | **Description**                                     | Central Wavelength (um) |
+===========================+=====================================================+=========================+
| 1                         | Channel 1 Reflectance Band                          |0.63                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| 2                         | Channel 2 Reflectance Band                          |0.865                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 3                         | Channel 3 Emissive Band                             |3.74                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| 4                         | Channel 4 Emissive Band                             |10.8                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| 5                         | Channel 5 Emissive Band                             |12.0                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| 6                         | Channel 6 Reflectance Band                          |1.60                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| 7                         | Channel 7 Reflectance Band                          |0.455                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 8                         | Channel 8 Reflectance Band                          |0.505                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 9                         | Channel 9 Reflectance Band                          |0.555                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 10                        | Channel 10 Reflectance Band                         |1.36                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |N/A                      |
+---------------------------+-----------------------------------------------------+-------------------------+
"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from ._base import ReaderProxyBase

ALL_BANDS = [str(x) for x in range(1, 11)]
ALL_COMPS = ["true_color"]
ALL_ANGLES = ["solar_zenith_angle", "solar_azimuth_angle", "sensor_zenith_angle", "sensor_azimuth_angle"]

DEFAULT_PRODUCTS = ALL_BANDS + ALL_ANGLES + ALL_COMPS

PRODUCT_ALIASES = {}

FILTERS = {
    "day_only": {
        "standard_name": [
            "toa_bidirectional_reflectance",
            "true_color",
            "corrected_reflectance",
        ],
    },
}


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULT_PRODUCTS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return ALL_BANDS + ALL_ANGLES + ALL_COMPS

    @property
    def _aliases(self) -> dict:
        return PRODUCT_ALIASES


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser."""
    if group is None:
        group = parser.add_argument_group(title="VIRR L1b Reader")
    return group, None
