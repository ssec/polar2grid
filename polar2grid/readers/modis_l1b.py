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
"""The MODIS Reader operates on HDF4 Level 1B files from the Moderate Resolution
Imaging Spectroradiometer (MODIS) instruments on the Aqua and Terra
satellites. The reader is designed to work with files created by the IMAPP
direct broadcast processing system (file naming conventions such as
a1.17006.1855.1000m.hdf), but can support other types of L1B files, including
the NASA archived files (file naming conventions such as
MOD021KM.A2017004.1732.005.2017023210017.hdf).  The
reader can be specified to the ``polar2grid.sh`` script by using the reader
name ``modis`` or ``modis_l1b``.

This reader’s default remapping algorithm is ewa for Elliptical Weighted
Averaging resampling. The ``--weight-delta-max`` parameter set to 10
and the ``--weight-distance-max`` parameter set to 1.

It provides the following products:

    +--------------------+-----------------------------------------------------+
    | Product Name       | Description                                         |
    +====================+=====================================================+
    | vis01              | Visible 1 Band                                      |
    +--------------------+-----------------------------------------------------+
    | vis02              | Visible 2 Band                                      |
    +--------------------+-----------------------------------------------------+
    | vis03              | Visible 3 Band                                      |
    +--------------------+-----------------------------------------------------+
    | vis04              | Visible 4 Band                                      |
    +--------------------+-----------------------------------------------------+
    | vis05              | Visible 5 Band                                      |
    +--------------------+-----------------------------------------------------+
    | vis06              | Visible 6 Band                                      |
    +--------------------+-----------------------------------------------------+
    | vis07              | Visible 7 Band                                      |
    +--------------------+-----------------------------------------------------+
    | vis26              | Visible 26 Band                                     |
    +--------------------+-----------------------------------------------------+
    | bt20               | Brightness Temperature Band 20                      |
    +--------------------+-----------------------------------------------------+
    | bt21               | Brightness Temperature Band 21                      |
    +--------------------+-----------------------------------------------------+
    | bt22               | Brightness Temperature Band 22                      |
    +--------------------+-----------------------------------------------------+
    | bt23               | Brightness Temperature Band 23                      |
    +--------------------+-----------------------------------------------------+
    | bt24               | Brightness Temperature Band 24                      |
    +--------------------+-----------------------------------------------------+
    | bt25               | Brightness Temperature Band 25                      |
    +--------------------+-----------------------------------------------------+
    | bt27               | Brightness Temperature Band 27                      |
    +--------------------+-----------------------------------------------------+
    | bt28               | Brightness Temperature Band 28                      |
    +--------------------+-----------------------------------------------------+
    | bt29               | Brightness Temperature Band 29                      |
    +--------------------+-----------------------------------------------------+
    | bt30               | Brightness Temperature Band 30                      |
    +--------------------+-----------------------------------------------------+
    | bt31               | Brightness Temperature Band 31                      |
    +--------------------+-----------------------------------------------------+
    | bt32               | Brightness Temperature Band 32                      |
    +--------------------+-----------------------------------------------------+
    | bt33               | Brightness Temperature Band 33                      |
    +--------------------+-----------------------------------------------------+
    | bt34               | Brightness Temperature Band 34                      |
    +--------------------+-----------------------------------------------------+
    | bt35               | Brightness Temperature Band 35                      |
    +--------------------+-----------------------------------------------------+
    | bt36               | Brightness Temperature Band 36                      |
    +--------------------+-----------------------------------------------------+
    | ir20               | Radiance Band 20                                    |
    +--------------------+-----------------------------------------------------+
    | ir21               | Radiance Band 21                                    |
    +--------------------+-----------------------------------------------------+
    | ir22               | Radiance Band 22                                    |
    +--------------------+-----------------------------------------------------+
    | ir23               | Radiance Band 23                                    |
    +--------------------+-----------------------------------------------------+
    | ir24               | Radiance Band 24                                    |
    +--------------------+-----------------------------------------------------+
    | ir25               | Radiance Band 25                                    |
    +--------------------+-----------------------------------------------------+
    | ir27               | Radiance Band 27                                    |
    +--------------------+-----------------------------------------------------+
    | ir28               | Radiance Band 28                                    |
    +--------------------+-----------------------------------------------------+
    | ir29               | Radiance Band 29                                    |
    +--------------------+-----------------------------------------------------+
    | ir30               | Radiance Band 30                                    |
    +--------------------+-----------------------------------------------------+
    | ir31               | Radiance Band 31                                    |
    +--------------------+-----------------------------------------------------+
    | ir32               | Radiance Band 32                                    |
    +--------------------+-----------------------------------------------------+
    | ir33               | Radiance Band 33                                    |
    +--------------------+-----------------------------------------------------+
    | ir34               | Radiance Band 34                                    |
    +--------------------+-----------------------------------------------------+
    | ir35               | Radiance Band 35                                    |
    +--------------------+-----------------------------------------------------+
    | ir36               | Radiance Band 36                                    |
    +--------------------+-----------------------------------------------------+
    | fog                | Temperature Difference between BT31                 |
    |                    | and BT20                                            |
    +--------------------+-----------------------------------------------------+
    | true_color         | Ratio sharpened rayleigh corrected true color       |
    +--------------------+-----------------------------------------------------+
    | false_color        | Ratio sharpened rayleigh corrected false color      |
    +--------------------+-----------------------------------------------------+

For reflectance/visible products a check is done to make sure that at least
10% of the swath is day time. Data is considered day time where solar zenith
angle is less than 90 degrees.

"""

from __future__ import annotations

import argparse
from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from satpy import DataQuery

from polar2grid.core.script_utils import ExtendConstAction

from ._base import ReaderProxyBase

PREFERRED_CHUNK_SIZE: int = 1354 * 2  # roughly the number columns in a 500m dataset

FILTERS = {
    "day_only": {
        "standard_name": [
            "toa_bidirectional_reflectance",
            "corrected_reflectance",
            "true_color",
            "false_color",
            "natural_color",
        ],
    },
    "night_only": {
        "standard_name": ["temperature_difference"],
    },
}

PRODUCT_ALIASES = {}
DEFAULTS = []
VIS_PRODUCTS = []
for chan_num in list(range(1, 8)) + [26]:
    p2g_name = f"vis{chan_num:02d}"
    VIS_PRODUCTS.append(p2g_name)
    PRODUCT_ALIASES[p2g_name] = DataQuery(name=f"{chan_num}", calibration="reflectance")
    DEFAULTS.append(p2g_name)

BT_PRODUCTS = []
RAD_PRODUCTS = []
for chan_num in list(range(20, 26)) + list(range(27, 37)):
    p2g_name = f"bt{chan_num:02d}"
    BT_PRODUCTS.append(p2g_name)
    PRODUCT_ALIASES[p2g_name] = DataQuery(name=f"{chan_num}", calibration="brightness_temperature")
    DEFAULTS.append(p2g_name)

    p2g_name = f"ir{chan_num:02d}"
    RAD_PRODUCTS.append(p2g_name)
    PRODUCT_ALIASES[p2g_name] = DataQuery(name=f"{chan_num}", calibration="radiance")

COMPOSITES = [
    "true_color",
    "false_color",
    "fog",
]
DEFAULTS.extend(COMPOSITES)

_AWIPS_TRUE_COLOR = ["modis_crefl01_250m", "modis_crefl04_250m", "modis_crefl03_250m"]
_AWIPS_FALSE_COLOR = ["modis_crefl07_500m", "modis_crefl02_250m", "modis_crefl01_250m"]


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULTS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return VIS_PRODUCTS + BT_PRODUCTS + RAD_PRODUCTS + COMPOSITES

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
    group.add_argument(
        "--ir-products",
        dest="products",
        action=ExtendConstAction,
        const=RAD_PRODUCTS,
        help="Add IR products to list of products",
    )
    group.add_argument(
        "--bt-products",
        dest="products",
        action=ExtendConstAction,
        const=BT_PRODUCTS,
        help="Add BT products to list of products",
    )
    group.add_argument(
        "--vis-products",
        dest="products",
        action=ExtendConstAction,
        const=VIS_PRODUCTS,
        help="Add Visible products to list of products",
    )
    group.add_argument(
        "--awips-true-color",
        dest="products",
        action=ExtendConstAction,
        const=_AWIPS_TRUE_COLOR,
        help="Add individual CREFL corrected products to create " "the 'true_color' composite in AWIPS.",
    )
    group.add_argument(
        "--awips-false-color",
        dest="products",
        action=ExtendConstAction,
        const=_AWIPS_FALSE_COLOR,
        help="Add individual CREFL corrected products to create " "the 'false_color' composite in AWIPS.",
    )
    group.add_argument(
        "--mask-saturated",
        default=False,
        action="store_true",
        help=argparse.SUPPRESS,
        # help="Mask saturated band 2 pixels as invalid instead of clipping to max reflectance",
    )
    return group, None
