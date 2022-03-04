#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2022 Space Science and Engineering Center (SSEC),
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
"""The AMI L1B Reader operates on Level 1B (L1B) NetCDF files for the
Advanced Meteorological Imager (AMI) instrument on board the Korean
Meteorological Administration (KMA) GEO-KOMPSAT-1 (GK-2A) and
GEO-KOMPSAT-2 (GK-2B) satellites. Geo2Grid determines if it supports files
based on the input filename. Files for AMI supported by Geo2Grid usually
have the following naming scheme::

    gk2a_ami_le1b_vi004_fd010ge_201909251200.nc

The AMI L1B reader supports all instrument spectral bands, identified in
Geo2Grid as the products shown in the table below. The
AMI L1B reader can be provided to the main geo2grid.sh script
using the ``-r`` option and the reader name ``ami_l1b``.

The list of supported products includes true and natural color imagery.
These are created by means of a python based atmospheric Rayleigh
scattering correction algorithm that is executed as part of the |project| AMI
L1B reader, along with sharpening to the highest spatial resolution. For
more information on the creation of RGBs, please see the
:ref:`RGB section <getting_started_rgb>`.


+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| VI004                     | 0.47um Reflectance Band                             |
+---------------------------+-----------------------------------------------------+
| VI005                       | Channel 2 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| VI006                       | Channel 3 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| VI008                       | Channel 4 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| NR013                       | Channel 5 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| NR016                       | Channel 6 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| SW038                       | Channel 7 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| WV063                       | Channel 8 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| WV069                       | Channel 9 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| WV073                       | Channel 10 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| IR087                       | Channel 11 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| IR096                       | Channel 12 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| IR105                       | Channel 13 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| IR112                       | Channel 14 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| IR123                       | Channel 15 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| IR133                       | Channel 16 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |
+---------------------------+-----------------------------------------------------+
| natural_color             | Ratio sharpened corrected natural color    |
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

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from ._base import ReaderProxyBase

READER_PRODUCTS = [
    "VI004",
    "VI005",
    "VI006",
    "VI008",
    "NR013",
    "NR016",
    "SW038",
    "WV063",
    "WV069",
    "WV073",
    "IR087",
    "IR096",
    "IR105",
    "IR112",
    "IR123",
    "IR133",
]
COMPOSITE_PRODUCTS = [
    "true_color",
    "natural_color",
    "airmass",
    "ash",
    "dust",
    "fog",
    "night_microphysics",
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
    return group, None
