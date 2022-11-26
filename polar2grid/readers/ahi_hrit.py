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
"""The AHI High Rate Information Transmission (HRIT) Reader operates on
standard Japan Meteorological Agency (JMA) Himawari-8 and Himawari-9
Advanced Himawari Imager (AHI) HRIT Digital Video Broadcast (DVB)
HimawariCast files.  This broadcast consists of a subset of 14 bands
at reduced spatial resolution.  The AHI HRIT reader works off of
the input filenames to determine if a file is supported by Geo2Grid.
Files usually have the following naming scheme:

    IMG_DK01B04_201809100300

These are the mission compliant radiance file naming conventions
used by JMA. The AHI HRIT reader supports a subset of instrument spectral bands,
identified in Geo2Grid as the products shown in the table below. The
AHI HRIT reader can be provided to the main geo2grid.sh script
using the ``-r`` option and the reader name ``ahi_hrit``.

The list of supported products includes natural color imagery.
This is created by means of a python based atmospheric Rayleigh
scattering correction algorithm that is executed as part of the |project| AHI
HRIT reader, along with sharpening to the highest spatial resolution.

Please note that true color image RGB creation is not supported for
HimawariCast because AHI Band 1 (Blue) and Band 2 (Green) are not
included.

For more information on the creation of RGBs, please see the
:ref:`RGB section <getting_started_rgb>`.

+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| B03                       | Channel 3 (0.64um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| B04                       | Channel 4 (0.86um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| B05                       | Channel 5 (1.6um) Reflectance Band                  |
+---------------------------+-----------------------------------------------------+
| B06                       | Channel 6 (2.3um) Reflectance Band                  |
+---------------------------+-----------------------------------------------------+
| B07                       | Channel 7 (3.9um) Brightness Temperature Band       |
+---------------------------+-----------------------------------------------------+
| B08                       | Channel 8 (6.2um) Brightness Temperature Band       |
+---------------------------+-----------------------------------------------------+
| B09                       | Channel 9 (6.9um) Brightness Temperature Band       |
+---------------------------+-----------------------------------------------------+
| B10                       | Channel 10 (7.3um) Brightness Temperature Band      |
+---------------------------+-----------------------------------------------------+
| B11                       | Channel 11 (8.6um) Brightness Temperature Band      |
+---------------------------+-----------------------------------------------------+
| B12                       | Channel 12 (9.6um) Brightness Temperature Band      |
+---------------------------+-----------------------------------------------------+
| B13                       | Channel 13 (10.4um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| B14                       | Channel 14 (11.2um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| B15                       | Channel 15 (12.4um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| B16                       | Channel 16 (13.3um) Brightness Temperature Band     |
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

READER_PRODUCTS = ["B{:02d}".format(x) for x in range(3, 17)]
COMPOSITE_PRODUCTS = [
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
        return READER_PRODUCTS + COMPOSITE_PRODUCTS[:1]

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
        group = parser.add_argument_group(title="AHI HRIT Reader")
    return group, None
