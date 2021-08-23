#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2021 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
#     input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
"""The AVHRR reader is for reading AAPP L1B files for the AVHRR instrument.
These files are a custom binary format. The reader can be specified with
the ``polar2grid.sh`` command using the ``avhrr`` or ``avhrr_l1b_aapp`` reader
name.

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--fornav-D`` option is set to 10 and
``--fornav-d`` is set to 1.

The AVHRR reader provides the following products:

+--------------------+--------------------------------------------+
| Product Name       | Description                                |
+====================+============================================+
| band1_vis          | Band 1 Visible                             |
+--------------------+--------------------------------------------+
| band2_vis          | Band 2 Visible                             |
+--------------------+--------------------------------------------+
| band3a_vis         | Band 3A Visible                            |
+--------------------+--------------------------------------------+
| band3b_bt          | Band 3B Brightness Temperature             |
+--------------------+--------------------------------------------+
| band4_vis          | Band 4 Brightness Temperature              |
+--------------------+--------------------------------------------+
| band5_vis          | Band 5 Brightness Temperature              |
+--------------------+--------------------------------------------+

"""
from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from ._base import ReaderProxyBase

from satpy import DataQuery


DEFAULT_PRODUCTS = []

FILTERS = {
    "day_only": {
        "standard_name": [
            "toa_bidirectional_reflectance",
            "corrected_reflectance",
        ],
    },
}

VIS_PRODUCTS = [
    "band1_vis",
    "band2_vis",
    "band3a_vis",
]

IR_PRODUCTS = [
    "band3b_bt",
    "band4_bt",
    "band5_bt",
]

PRODUCT_ALIASES = {
    "band1_vis": DataQuery("1", calibration="reflectance"),
    "band2_vis": DataQuery("2", calibration="reflectance"),
    "band3a_vis": DataQuery("3a", calibration="reflectance"),
    "band3b_bt": DataQuery("3b", calibration="brightness_temperature"),
    "band4_bt": DataQuery("4", calibration="brightness_temperature"),
    "band5_bt": DataQuery("5", calibration="brightness_temperature"),
}


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULT_PRODUCTS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return VIS_PRODUCTS + IR_PRODUCTS

    @property
    def _aliases(self) -> dict[DataQuery]:
        return PRODUCT_ALIASES


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="AVHRR L1b AAPP Reader")
    return group, None
