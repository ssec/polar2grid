#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2019 Space Science and Engineering Center (SSEC),
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
"""
The VIIRS EDR FLOOD reader operates on HDF4 files.
Files usually have the following naming scheme:

    WATER_VIIRS_Prj_SVI_{platform_shortname}_d{start_time:%Y%m%d_t%H%M%S%f}_e{end_time:%H%M%S%f}_b{orbit:5d}_{source:8s}_{dim0}_{dim1}_01.hdf
    or
    WATER_VIIRS_Prj_SVI_{platform_shortname}_d{start_time:%Y%m%d_t%H%M%S%f}_e{end_time:%H%M%S%f}_b{orbit:5d}_{source:8s}_{aoi:3s}_{dim0}_{dim1}_01.hdf

This reader's default resampling algorithm is ``nearest`` for Nearest Neighbor resampling.
The ``--remap_method`` parameter is set to ``nearest``.

+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| WaterDetection            | Channel 1 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
"""
from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from satpy import DataQuery

from ._base import ReaderProxyBase

DEFAULT_DATASETS = ["WaterDetection"]


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULT_DATASETS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return DEFAULT_DATASETS

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
        group = parser.add_argument_group(title="VIIRS EDR Active Fires Reader")
    return group, None
