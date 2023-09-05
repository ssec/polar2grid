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
"""The ABI Level 2 Reader operates on NOAA Level 2 (L2) NetCDF files
from the GOES-16 (GOES-East) and GOES-17 (GOES-West) Advanced Baseline
Imager (ABI) instrument. The ABI L2 NetCDF reader works off of the input
filenames to determine if a file is supported by Geo2Grid. Files usually have
the following naming scheme::

    OR_ABI-L2-{PROD}F-M3_G16_s20182531700311_e20182531711090_c20182531711149.nc

and::

    CG_ABI-L2-{PROD}F-M6_G17_s20223271830316_e20223271839394_c20223271842100.nc

These are the mission compliant radiance file naming conventions
used by the NOAA Comprehensive Large Array-data Stewardship
System (CLASS) archive and the CSPP Geo AIT Framework Level 2 software.
The ABI L2 NetCDF reader supports most L2 products, but Geo2Grid is tested with
a limited subset of these. See the table below for more information.
The ABI L2 NetCDF reader can be provided to the main geo2grid.sh script
using the ``-r`` option and the reader name ``abi_l2_nc``.


+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| AOD                       | Aerosol Optical Depth                               |
+---------------------------+-----------------------------------------------------+
| LST                       | Land Surface Temperature                            |
+---------------------------+-----------------------------------------------------+
| HT                        | Cloud Top Height                                    |
+---------------------------+-----------------------------------------------------+
| TEMP                      | Cloud Top Temperature                               |
+---------------------------+-----------------------------------------------------+
| Fog_Depth                 | Fog Depth                                           |
+---------------------------+-----------------------------------------------------+
| IFR_Fog_Prob              | Instrument Flight Rules Probability                 |
+---------------------------+-----------------------------------------------------+
| LIFR_Fog_Prob             | Low Instrument Flight Rules Probability             |
+---------------------------+-----------------------------------------------------+
| MVFR_Fog_Prob             | Marginal Visible Flight Rules Probability           |
+---------------------------+-----------------------------------------------------+

More information on the flight rules products can be found at:

https://www.experimentalaircraft.info/wx/colors-metar-taf.php

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from ._base import ReaderProxyBase

PREFERRED_CHUNK_SIZE: int = 1356

READER_PRODUCTS = [
    "AOD",
    "HT",
    "LST",
    "TEMP",
    "Fog_Depth",
    "IFR_Fog_Prob",
    "LIFR_Fog_Prob",
    "MVFR_Fog_Prob",
]
COMPOSITE_PRODUCTS = []


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_geo2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return READER_PRODUCTS + COMPOSITE_PRODUCTS

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
        group = parser.add_argument_group(title="ABI L2 Reader")
    return group, None
