#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2017-2021 Space Science and Engineering Center (SSEC),
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
"""The ACSPO reader is for reading files created by the NOAA Community
Satellite Processing Package (CSPP) Advanced Clear-Sky
Processor for Oceans (ACSPO) system software. The ACSPO reader supports
product files created from VIIRS, MODIS and AVHRR imaging sensors.
For more information on this product, please visit the CSPP LEO
website: `https://cimss.ssec.wisc.edu/cspp/`.

The ACSPO output product format is NetCDF4.  The frontend can be specified
with the ``polar2grid.sh`` command using the ``acspo`` frontend name.
The ACSPO frontend provides the following products:

+------------------------+--------------------------------------------+
| Product Name           | Description                                |
+========================+============================================+
| sst                    | Sea Surface Temperature                    |
+------------------------+--------------------------------------------+

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from satpy import DataQuery

from ._base import ReaderProxyBase
from ..core.script_utils import BooleanFilterAction

DEFAULT_PRODUCTS = ["sst"]
PREFERRED_CHUNK_SIZE = 2048


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULT_PRODUCTS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return DEFAULT_PRODUCTS

    @property
    def _aliases(self) -> dict[str, DataQuery]:
        return {}


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="ACSPO Reader")
    group.add_argument(
        "--cloud-clear",
        action=BooleanFilterAction,
        dest="filters",
        const="cloud_clear",
        default=["cloud_clear"],
        help="Enable or disable cloud clearing for the 'sst' product (default on).",
    )
    return group, None
