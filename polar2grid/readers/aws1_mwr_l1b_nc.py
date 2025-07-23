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
"""The AWS-1 MWR reader is for reading L1B files for the MWR instrument.

These files are NetCDF4 files. The reader can be specified with
the ``polar2grid.sh`` command using the ``aws1_mwr_l1b_nc`` reader name.

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--weight-delta-max`` option is set to 100 and
``--weight-distance-max`` is set to 1.

The MWR reader provides the following products:

+--------------------+--------------------------------------------+
| Product Name       | Description                                |
+====================+============================================+
| bt01               | Band 1 (50.3GHz) Brightness Temperature    |
+--------------------+--------------------------------------------+
| bt02               | Band 2 (52.8GHz) Brightness Temperature    |
+--------------------+--------------------------------------------+
| bt03               | Band 3 (53.2GHz) Brightness Temperature    |
+--------------------+--------------------------------------------+
| bt04               | Band 4 (53.6GHz) Brightness Temperature    |
+--------------------+--------------------------------------------+
| bt05               | Band 5 (54.4GHz) Brightness Temperature    |
+--------------------+--------------------------------------------+
| bt06               | Band 6 (54.9GHz) Brightness Temperature    |
+--------------------+--------------------------------------------+
| bt07               | Band 7 (55.5GHz) Brightness Temperature    |
+--------------------+--------------------------------------------+
| bt08               | Band 8 (57.3GHz) Brightness Temperature    |
+--------------------+--------------------------------------------+
| bt09               | Band 9 (89.0GHz) Brightness Temperature    |
+--------------------+--------------------------------------------+
| bt10               | Band 10 (165.5GHz) Brightness Temperature  |
+--------------------+--------------------------------------------+
| bt11               | Band 11 (176.3GHz) Brightness Temperature  |
+--------------------+--------------------------------------------+
| bt12               | Band 12 (178.8GHz) Brightness Temperature  |
+--------------------+--------------------------------------------+
| bt13               | Band 13 (180.3GHz) Brightness Temperature  |
+--------------------+--------------------------------------------+
| bt14               | Band 14 (181.5GHz) Brightness Temperature  |
+--------------------+--------------------------------------------+
| bt15               | Band 15 (182.3GHz) Brightness Temperature  |
+--------------------+--------------------------------------------+
| bt16               | Band 16 (325.2GHz) Brightness Temperature  |
+--------------------+--------------------------------------------+
| bt17               | Band 17 (325.2GHz) Brightness Temperature  |
+--------------------+--------------------------------------------+
| bt18               | Band 18 (325.2GHz) Brightness Temperature  |
+--------------------+--------------------------------------------+
| bt19               | Band 19 (325.2GHz) Brightness Temperature  |
+--------------------+--------------------------------------------+

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
import logging
from typing import Optional

from satpy import DataQuery, Scene

from ._base import ReaderProxyBase

logger = logging.getLogger(__name__)

FILTERS = {}

PRODUCT_ALIASES = {f"bt{band_num:02d}": DataQuery(name=str(band_num)) for band_num in range(1, 20)}
BT_BANDS = sorted(PRODUCT_ALIASES.keys())


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return BT_BANDS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return BT_BANDS

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
        group = parser.add_argument_group(title="AWS1 MWR L1b Reader")
    return group, None
