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
"""The FY-3D MERSI2 Level 1B reader operates on Level 1B (L1B) HDF5 files.

The files come in four varieties; band data and geolocation data, both at 250m
and 1000m resolution. Files usually have the following naming scheme:

    tf{start_time:%Y%j%H%M%S}.FY3D-X_MERSI_1000M_L1B.{ext}

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--weight-delta-max`` parameter is set to 40 and the
``--weight-distance-max`` parameter is set to 1.

The frontend can be specified with the ``polar2grid.sh`` command using
the ``mersi2_l1b`` frontend name. The MERSI2 frontend provides the following products:

+---------------------------+-----------------------------------------------------+-------------------------+
| **Product Name**          | **Description**                                     | Central Wavelength (um) |
+===========================+=====================================================+=========================+
| 1                         | Channel 1 Reflectance Band                          | 0.47                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 2                         | Channel 2 Reflectance Band                          | 0.55                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 3                         | Channel 3 Reflectance Band                          | 0.65                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 4                         | Channel 4 Reflectance Band                          | 0.865                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 5                         | Channel 5 Reflectance Band                          | 1.38                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 6                         | Channel 6 Reflectance Band                          | 1.64                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 7                         | Channel 7 Reflectance Band                          | 2.13                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 8                         | Channel 8 Reflectance Band                          | 0.412                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 9                         | Channel 9 Reflectance Band                          | 0.443                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 10                        | Channel 10 Reflectance Band                         | 0.490                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 11                        | Channel 11 Reflectance Band                         | 0.555                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 12                        | Channel 12 Reflectance Band                         | 0.670                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 13                        | Channel 13 Reflectance Band                         | 0.709                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 14                        | Channel 14 Reflectance Band                         | 0.746                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 15                        | Channel 15 Reflectance Band                         | 0.865                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 16                        | Channel 16 Reflectance Band                         | 0.905                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 17                        | Channel 17 Reflectance Band                         | 0.936                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 18                        | Channel 18 Reflectance Band                         | 0.940                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 19                        | Channel 19 Reflectance Band                         | 1.24                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 20                        | Channel 20 Brightness Temperature Band              | 3.80                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 21                        | Channel 21 Brightness Temperature Band              | 4.05                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 22                        | Channel 22 Brightness Temperature Band              | 7.20                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 23                        | Channel 23 Brightness Temperature Band              | 8.55                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 24                        | Channel 24 Brightness Temperature Band              | 10.8                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 25                        | Channel 25 Brightness Temperature Band              | 12.0                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| true_color                | Rayleigh corrected true color RGB                   | N/A                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| false_color               | False color RGB (bands 7, 4, 3)                     | N/A                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| natural_color             | Natural color RGB (bands 6, 4, 3)                   | N/A                     |
+---------------------------+-----------------------------------------------------+-------------------------+
"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
import logging
from typing import Optional

from satpy import Scene, DataQuery

from ._base import ReaderProxyBase
from ..core.script_utils import ExtendConstAction

logger = logging.getLogger(__name__)

ALL_BANDS = [str(x) for x in range(1, 26)]
ALL_ANGLES = ["solar_zenith_angle", "solar_azimuth_angle", "sensor_zenith_angle", "sensor_azimuth_angle"]
ALL_COMPS = ["true_color", "false_color"]

DEFAULT_PRODUCTS = ALL_BANDS + ALL_COMPS

PRODUCT_ALIASES = {}

FILTERS = {
    "day_only": {
        "standard_name": [
            "toa_bidirectional_reflectance",
            "true_color",
            "false_color",
            "natural_color",
        ],
    },
}


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def __init__(self, scn: Scene, user_products: list[str]):
        self._modified_aliases = PRODUCT_ALIASES.copy()

        try:
            # they specified --normalized-radiances
            user_products.remove("normalized_radiances")
            apply_sunz = False
        except ValueError:
            apply_sunz = True

        modifiers = ("sunz_corrected",) if apply_sunz else ()
        for chan_num in range(1, 20):
            if modifiers:
                logger.debug(f"Using visible channel modifiers: {modifiers}")
            self._modified_aliases[f"{chan_num}"] = DataQuery(name=f"{chan_num}", modifiers=modifiers)
        super().__init__(scn, user_products)

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULT_PRODUCTS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return ALL_BANDS + ALL_COMPS + ALL_ANGLES

    @property
    def _aliases(self) -> dict:
        return self._modified_aliases


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser."""
    if group is None:
        group = parser.add_argument_group(title="MERSI-2 L1B Reader")
    group.add_argument(
        "--normalized-radiances",
        dest="products",
        action=ExtendConstAction,
        const=["normalized_radiances"],
        help="Do not apply '/ cos(SZA)' when loading visible bands.",
    )
    return group, None
