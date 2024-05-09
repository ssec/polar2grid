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
"""The VIIRS EDR Active Fires reader operates on CSPP NetCDF I-Band (AFIMG) Resolution or
M-Band Resolution (AFMOD) Environmental Data Record files.

Files supported usually have the following naming schemes:

   AFIMG_j01_d20221006_t2101052_e2102297_b25304_c20221006214545032016_cspp_dev.nc and/or,
   AFMOD_npp_d20221006_t2017005_e2018247_b56701_c20221006205259096916_cspp_dev.nc

For more information about the this CSPP product, please
visit the CSPP LEO website: `https://cimss.ssec.wisc.edu/cspp/`.

This reader's default resampling algorithm ``--method`` is
``nearest`` for Nearest Neighbor resampling. The frontend can
be specified with the ``polar2grid.sh`` command using the
``viirs_edr_active_fires`` frontend name. The VIIRS Active Fire
frontend provides the following products:

+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| confidence_cat            | Fire Confidence Category   (AFIMG Resolution Only)  |
+---------------------------+-----------------------------------------------------+
| T4                        | I-Band 4 Temperature       (AFIMG Resolution Only)  |
+---------------------------+-----------------------------------------------------+
| power                     | Fire Radiative Power                                |
+---------------------------+-----------------------------------------------------+
| confidence_pct            | Fire Confidence Percentage (AFMOD Resolution Only)  |
+---------------------------+-----------------------------------------------------+
| T13                       | M-Band 13 Temperature      (AFMOD Resolution Only)  |
+---------------------------+-----------------------------------------------------+
"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from satpy import DataQuery

from ._base import ReaderProxyBase

DEFAULT_DATASETS = ["T4", "T13", "confidence_cat", "confidence_pct", "power"]


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
