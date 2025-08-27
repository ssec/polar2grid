#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2018 Space Science and Engineering Center (SSEC),
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
"""The ABI Level 1B Reader operates on NOAA Level 1B (L1B) NetCDF files
from the GOES-16 (GOES-East) and GOES-17/18 (GOES-West) Advanced Baseline
Imager (ABI) instrument. The ABI L1B reader works off of the input filenames
to determine if a file is supported by Geo2Grid. Files usually have the
following naming scheme::

    OR_ABI-L1b-RadF-M6C02_G18_s20223191830206_e20223191839514_c20223191839547.nc

These are the mission compliant radiance file naming conventions
used by the NOAA Comprehensive Large Array-data Stewardship
System (CLASS) archive and the CSPP GOES Rebroadcast (GRB) software.
The ABI L1B reader supports all instrument spectral bands, identified in
Geo2Grid as the products shown in the table below. The
ABI L1B reader can be provided to the main geo2grid.sh script
using the ``-r`` option and the reader name ``abi_l1b``.

The list of supported products includes true and natural color imagery.
These are created by means of a python based atmospheric Rayleigh
scattering correction algorithm that is executed as part of the |project| ABI
L1B reader, along with sharpening to the highest spatial resolution. For
more information on the creation of RGBs, please see the
:ref:`RGB section <getting_started_rgb>`.


+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| C01                       | Channel 1 (0.47um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| C02                       | Channel 2 (0.64um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| C03                       | Channel 3 (0.86um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| C04                       | Channel 4 (1.37um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| C05                       | Channel 5 (1.6um) Reflectance Band                  |
+---------------------------+-----------------------------------------------------+
| C06                       | Channel 6 (2.2um) Reflectance Band                  |
+---------------------------+-----------------------------------------------------+
| C07                       | Channel 7 (3.9um) Brightness Temperature Band       |
+---------------------------+-----------------------------------------------------+
| C08                       | Channel 8 (6.2um) Brightness Temperature Band       |
+---------------------------+-----------------------------------------------------+
| C09                       | Channel 9 (6.9um) Brightness Temperature Band       |
+---------------------------+-----------------------------------------------------+
| C10                       | Channel 10 (7.3um) Brightness Temperature Band      |
+---------------------------+-----------------------------------------------------+
| C11                       | Channel 11 (8.4um) Brightness Temperature Band      |
+---------------------------+-----------------------------------------------------+
| C12                       | Channel 12 (9.6um) Brightness Temperature Band      |
+---------------------------+-----------------------------------------------------+
| C13                       | Channel 13 (10.3um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| C14                       | Channel 14 (11.2um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| C15                       | Channel 15 (12.3um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| C16                       | Channel 16 (13.3um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |
+---------------------------+-----------------------------------------------------+
| natural_color             | Ratio sharpened corrected natural color             |
+---------------------------+-----------------------------------------------------+
| airmass                   | Air mass RGB                                        |
+---------------------------+-----------------------------------------------------+
| ash                       | Ash RGB                                             |
+---------------------------+-----------------------------------------------------+
| dust                      | Dust RGB                                            |
+---------------------------+-----------------------------------------------------+
| fog                       | Fog RGB                                             |
+---------------------------+-----------------------------------------------------+
| night_microphysics        | Night Microphysics RGB                              |
+---------------------------+-----------------------------------------------------+
| day_cloud_type            | Day Cloud Type RGB                                  |
+---------------------------+-----------------------------------------------------+
| day_severe_storms         | Day Severe Storms RGB (aka. Day Convection)         |
+---------------------------+-----------------------------------------------------+
| volcanic_emissions        | Volcanic Emissions (SO2 and Ash) (aka. SO2)         |
+---------------------------+-----------------------------------------------------+
| day_blowing_snow          | Day Blowing Snow RGB                                |
+---------------------------+-----------------------------------------------------+

"""

from __future__ import annotations

from argparse import ArgumentParser, BooleanOptionalAction, _ArgumentGroup
from typing import Optional

from ._base import ReaderProxyBase

PREFERRED_CHUNK_SIZE: int = 1356

READER_PRODUCTS = ["C{:02d}".format(x) for x in range(1, 17)]
COMPOSITE_PRODUCTS = [
    "true_color",
    "natural_color",  # <-- considered legacy RGB Workshop 2025
    "airmass",
    "ash",  # <-- deprecated name as of RGB Workshop 2025 (preferred: 24h_microphysics_ash)
    "dust",  # <-- deprecated name as of RGB Workshop 2025 (preferred: 24h_microphysics_dust)
    "fog",  # <-- deprecated name as of RGB Workshop 2025 (preferred: night_microphysics)?
    "night_microphysics",
    # 2025 new
    "day_cloud_type",
    "day_severe_storms",
    "volcanic_emissions",  # old name: so2
    "day_blowing_snow",
    # "day_cloud_type_distinction",  # aka: day cloud phase distinction
    # "cira_fire_temperature",
    # "snow_fog",  # day snow fog - considered legacy RGB Workshop 2025
    # "land_cloud",  # day land cloud - considered legacy RGB Workshop 2025
    # "water_vapors2",  # differential water vapor - considered legacy RGB Workshop 2025
    # "simple_water_vapor",  # aka: water_vapors1 (deprecated in Satpy)
]


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_geo2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return READER_PRODUCTS + COMPOSITE_PRODUCTS[:2]

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return READER_PRODUCTS + COMPOSITE_PRODUCTS


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="ABI L1b Reader")
    group.add_argument(
        "--clip-negative-radiances",
        action=BooleanOptionalAction,
        default=True,
        help="Clip negative radiances for IR bands. Default is to perform the clipping.",
    )
    return group, None
