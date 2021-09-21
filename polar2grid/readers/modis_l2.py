#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2021 Space Science and Engineering Center (SSEC),
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
"""The MODIS L2 Reader operates on HDF4 Level 2 files from the Moderate Resolution
Imaging Spectroradiometer (MODIS) instruments on the Aqua and Terra
satellites. The reader is designed to work with files created by the IMAPP
direct broadcast processing system (file naming conventions such as
a1.17006.1855.1000m.hdf), but can support other types of L2 files, including
the NASA archived files (file naming conventions such as
MOD021KM.A2017004.1732.005.2017023210017.hdf).  The
reader can be specified to the ``polar2grid.sh`` script by using the reader
name ``modis_l2``.

It provides the following products:

    +--------------------+--------------------------------------------+
    | Product Name       | Description                                |
    +====================+============================================+
    | cloud_mask         | Cloud Mask                                 |
    +--------------------+--------------------------------------------+
    | land_sea_mask      | Land Sea Mask                              |
    +--------------------+--------------------------------------------+
    | snow_ice_mask      | Snow Ice Mask                              |
    +--------------------+--------------------------------------------+
    | sst                | Sea Surface Temperature                    |
    +--------------------+--------------------------------------------+
    | lst                | Land Surface Temperature                   |
    +--------------------+--------------------------------------------+
    | ndvi               | Normalized Difference Vegetation Index     |
    +--------------------+--------------------------------------------+
    | ist                | Ice Surface Temperature                    |
    +--------------------+--------------------------------------------+
    | inversion_strength | Inversion Strength                         |
    +--------------------+--------------------------------------------+
    | inversion_depth    | Inversion Depth                            |
    +--------------------+--------------------------------------------+
    | ice_concentration  | Ice Concentration                          |
    +--------------------+--------------------------------------------+
    | ctt                | Cloud Top Temperature                      |
    +--------------------+--------------------------------------------+
    | tpw                | Total Precipitable Water                   |
    +--------------------+--------------------------------------------+

For reflectance/visible products a check is done to make sure that at least
10% of the swath is day time. Data is considered day time where solar zenith
angle is less than 90 degrees.

"""
from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from satpy import DataQuery

from ._base import ReaderProxyBase

PRODUCTS = [
    "cloud_mask",
    "land_sea_mask",
    "snow_ice_mask",
    "sst",
    "lst",
    "ndvi",
    "ist",
    "inversion_strength",
    "inversion_depth",
    "ice_concentration",
    "ctt",
    "tpw",
]

PRODUCT_ALIASES = {
    "ist": DataQuery(name="ice_surface_temperature"),
    "sst": DataQuery(name="sea_surface_temperature"),
    "ctt": DataQuery(name="cloud_top_temperature"),
    "tpw": DataQuery(name="water_vapor"),
}


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return PRODUCTS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return PRODUCTS

    @property
    def _aliases(self) -> dict[str, DataQuery]:
        return PRODUCT_ALIASES


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="MODIS L1B Reader")
    return group, None
