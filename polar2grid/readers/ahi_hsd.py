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
"""The AHI HSD Reader operates on standard files from the Japan
Meteorological Agency (JMA) Himawari-8 Advanced Himawari Imager (AHI) 
instrument. The AHI HSD reader works off of the input filenames
to determine if a file is supported by Geo2Grid. Files usually 
have the following naming scheme:

    HS_H08_20181022_0300_B09_FLDK_R20_S1010.DAT

These are the mission compliant radiance file naming conventions
used by JMA. The AHI HSD reader supports all instrument spectral bands, 
identified in Geo2Grid as the products shown in the table below. The
AHI HSD reader can be provided to the main geo2grid.sh script
using the ``-r`` option and the reader name ``ahi_hsd``.

The list of supported products includes true and natural color imagery.
These are created by means of a python based atmospheric Rayleigh
scattering correction algorithm that is executed as part of the |project| AHI 
HSD reader, along with sharpening to the highest spatial resolution. For
more information on the creation of RGBs, please see the
:ref:`RGB section <getting_started_rgb>`.

+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| B01                       | Channel 1 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B02                       | Channel 2 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B03                       | Channel 3 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B04                       | Channel 4 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B05                       | Channel 5 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B06                       | Channel 6 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B07                       | Channel 7 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| B08                       | Channel 8 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| B09                       | Channel 9 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| B10                       | Channel 10 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B11                       | Channel 11 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B12                       | Channel 12 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B13                       | Channel 13 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B14                       | Channel 14 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B15                       | Channel 15 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B16                       | Channel 16 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |
+---------------------------+-----------------------------------------------------+
| natural_color             | Ratio sharpened rayleigh corrected natural color    |
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

from satpy import DataQuery

READER_PRODUCTS = ["B{:02d}".format(x) for x in range(1, 17)]
COMPOSITE_PRODUCTS = [
    "true_color",
    "natural_color",
    "airmass",
    "ash",
    "dust",
    "fog",
    "night_microphysics",
]
DEFAULT_PRODUCTS = READER_PRODUCTS + COMPOSITE_PRODUCTS[:2]


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
        group = parser.add_argument_group(title="AHI HSD Reader")
    return group, None
