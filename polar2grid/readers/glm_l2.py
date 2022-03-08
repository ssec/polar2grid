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
"""The GLM Level 2 Reader operates on Gridded GLM Level 2 NetCDF files
from the GOES-16 (GOES-East) and GOES-17/18 (GOES-West) Geostationary
Lightning Mapper (GLM). The GLM L2 reader works off of the input filenames
to determine if a file is supported by Geo2Grid. Files usually have the
following naming scheme::

    OR_GLM-L2-GLMF-M3_G16_s20192701933000_e20192701934000_c20192701934330.nc

These files can be generated by the CSPP Gridded GLM software which depends
on the python ``glmtools`` library and GLM L2 LCFA inputs. The point data from
these inputs is gridded to the ABI full disk, CONUS, or mesoscale sectors.
The GLM L2 reader supports the products shown in the table below, but should
allow for other products available from the GLM files to be loaded.
The GLM L2 reader can be provided to the main geo2grid.sh script
using the ``-r`` option and the reader name ``glm_l2``.

+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| flash_extent_density      | Flash Extent Density                                |
+---------------------------+-----------------------------------------------------+
| group_extent_density      | Group Extent Density                                |
+---------------------------+-----------------------------------------------------+
| flash_centroid_density    | Flash Centroid Density                              |
+---------------------------+-----------------------------------------------------+
| group_centroid_density    | Group Centroid Density                              |
+---------------------------+-----------------------------------------------------+
| average_flash_area        | Average Flash Area                                  |
+---------------------------+-----------------------------------------------------+
| minimum_flash_area        | Minimum Flash Area                                  |
+---------------------------+-----------------------------------------------------+
| average_group_area        | Average Group Area                                  |
+---------------------------+-----------------------------------------------------+
| total_energy              | Total Energy                                        |
+---------------------------+-----------------------------------------------------+

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from ._base import ReaderProxyBase

READER_PRODUCTS = [
    "flash_extent_density",
    "group_extent_density",
    "flash_centroid_density",
    "group_centroid_density",
    "average_flash_area",
    "minimum_flash_area",
    "average_group_area",
    "total_energy",
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
        group = parser.add_argument_group(title="ABI L1b Reader")
    return group, None
