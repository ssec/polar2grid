# Copyright (C) 2023 Space Science and Engineering Center (SSEC),
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
"""The FY-3E MERSI-LL Level 1B reader operates on Level 1B (L1B) HDF5 files.

The files come in four varieties; band data and geolocation data, both at 250m
and 1000m resolution. Files usually have the following naming scheme:

    tf{start_time:%Y%j%H%M%S}.FY3E-X_MERSI_1000M_L1B.{ext}

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--weight-delta-max`` parameter is set to 40 and the
``--weight-distance-max`` parameter is set to 1.

The frontend can be specified with the ``polar2grid.sh`` command using
the ``mersi_ll_l1b`` frontend name. The MERSI-LL frontend provides the following products:

+---------------------------+-----------------------------------------------------+-------------------------+
| **Product Name**          | **Description**                                     | Central Wavelength (um) |
+===========================+=====================================================+=========================+
| 1                         | Channel 1 Day/Night Radiance Band                   | 0.709                   |
+---------------------------+-----------------------------------------------------+-------------------------+
| 2                         | Channel 2 Brightness Temperature Band               | 3.80                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 3                         | Channel 3 Brightness Temperature Band               | 4.05                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 4                         | Channel 4 Brightness Temperature Band               | 7.20                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 5                         | Channel 5 Brightness Temperature Band               | 8.55                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 6                         | Channel 6 Brightness Temperature Band               | 10.8                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 7                         | Channel 7 Brightness Temperature Band               | 12.0                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| histogram_dnb             | Histogram Equalized DNB Band                        | N/A                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| adaptive_dnb              | Adaptive Histogram Equalized DNB Band               | N/A                     |
+---------------------------+-----------------------------------------------------+-------------------------+

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from ._base import ReaderProxyBase

ALL_BANDS = [str(x) for x in range(1, 8)]
ALL_ANGLES = [
    "solar_zenith_angle",
    "solar_azimuth_angle",
    "sensor_zenith_angle",
    "sensor_azimuth_angle",
    "moon_zenith_angle",
    "moon_azimuth_angle",
]
ALL_COMPS = ["histogram_dnb", "adaptive_dnb"]

# band 1 (DNB) is not useful by itself, histogram_dnb is not a default
DEFAULT_PRODUCTS = ALL_BANDS[1:] + ALL_COMPS[1:]

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

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULT_PRODUCTS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return ALL_BANDS + ALL_COMPS + ALL_ANGLES

    @property
    def _aliases(self) -> dict:
        return PRODUCT_ALIASES


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser."""
    return None, None
