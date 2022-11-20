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
"""The AGRI L1 Reader operates on Level 1 (L1) HDF5 files for the
Advanced Geostationary Radiation Imager (AGRI) instrument on board the
Feng-Yun - 4B (FY-4B) satellite. Geo2Grid determines if it supports files
based on the input filename. Files for AGRI supported by Geo2Grid usually
have the following naming scheme::

    FY4B-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20220117000000_20220117001459_0500M_V0001.HDF

The AGRI L1 reader supports all instrument spectral bands, identified in
Geo2Grid as the products shown in the table below. The
AGRI L1 reader for FY-4B can be provided to the main geo2grid.sh script
using the ``-r`` option and the reader name ``agri_fy4b_l1``.

The list of supported products includes true and natural color imagery.
These are created by means of a python based atmospheric Rayleigh
scattering correction algorithm that is executed as part of the |project| AGRI
L1 reader, along with sharpening to the highest spatial resolution. For
more information on the creation of RGBs, please see the
:ref:`RGB section <getting_started_rgb>`.

+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| C01                       | Channel 1 (0.47um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| C02                       | Channel 2 (0.65um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| C03                       | Channel 3 (0.83um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| C04                       | Channel 4 (1.37um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| C05                       | Channel 5 (1.61um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| C06                       | Channel 6 (2.25um) Reflectance Band                 |
+---------------------------+-----------------------------------------------------+
| C07                       | Channel 7 (3.75um) Brightness Temperature Band      |
+---------------------------+-----------------------------------------------------+
| C08                       | Channel 8 (3.75um) Brightness Temperature Band      |
+---------------------------+-----------------------------------------------------+
| C09                       | Channel 9 (6.25um) Brightness Temperature Band      |
+---------------------------+-----------------------------------------------------+
| C10                       | Channel 10 (6.95um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| C11                       | Channel 11 (7.42um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| C12                       | Channel 12 (8.5um) Brightness Temperature Band      |
+---------------------------+-----------------------------------------------------+
| C13                       | Channel 13 (10.8um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| C14                       | Channel 14 (12.0um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| C15                       | Channel 15 (13.5um) Brightness Temperature Band     |
+---------------------------+-----------------------------------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |
+---------------------------+-----------------------------------------------------+
| natural_color             | Ratio sharpened corrected natural color             |
+---------------------------+-----------------------------------------------------+
| ash                       | Ash RGB                                             |
+---------------------------+-----------------------------------------------------+
| dust                      | Dust RGB                                            |
+---------------------------+-----------------------------------------------------+
| fog                       | Fog RGB                                             |
+---------------------------+-----------------------------------------------------+


"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from ._base import ReaderProxyBase

PREFERRED_CHUNK_SIZE: int = 4096

READER_PRODUCTS = ["C{:02d}".format(x) for x in range(1, 16)]
COMPOSITE_PRODUCTS = [
    "true_color",
    "natural_color",
    "ash",
    "dust",
    "fog",
]


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_geo2grid_reader: bool = True

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
        group = parser.add_argument_group(title="AGRI FY-4B Level 1 Reader")
    return group, None
