# Copyright (C) 2023 Space Science and Engineering Center (SSEC),
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
"""The OMPS EDR Reader operates on Environmental Data Record (EDR) NetCDF4 files
from the Suomi National Polar-orbiting Partnership's (NPP), the NOAA20, or the
NOAA-21 Ozone Mapping and Profiler Suite (OMPS) instrument. The OMPS
EDR reader requires filenames to match one of a couple different standard
filename schemes used for official products. EDR files are typically named
as below::

    V8TOZ-EDR_v4r3_j01_s202604071740387_e202604071741162_c202604071754380.nc

The OMPS EDR reader can be specified to the ``polar2grid.sh`` script
with the reader name ``viirs_edr``.

This reader's default remapping algorithm is ``nearest`` for nearest neighbor
resampling.

+---------------------------+-----------------------------------------------------+
| Product Name              | Description                                         |
+===========================+=====================================================+
| Reflectivity331           | Reflectivity at 331nm                               |
+---------------------------+-----------------------------------------------------+
| AerosolIndex              | Aerosol index                                       |
+---------------------------+-----------------------------------------------------+
| ColumnAmountO3            | Total Column of Ozone                               |
+---------------------------+-----------------------------------------------------+

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from satpy import DataQuery

from ._base import ReaderProxyBase
from ..core.script_utils import BooleanFilterAction

PREFERRED_CHUNK_SIZE: int = 6400

PRODUCT_ALIASES = {}

TO3_PRODUCTS = ["Reflectivity331", "AerosolIndex", "ColumnAmountO3"]
DEFAULT_PRODUCTS = TO3_PRODUCTS
P2G_PRODUCTS = TO3_PRODUCTS

FILTERS = {
    "day_only": {},
    "night_only": {},
}


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULT_PRODUCTS

    def get_all_products(self):
        """Get all polar2grid products that could be loaded."""
        return P2G_PRODUCTS

    @property
    def _aliases(self) -> dict[str, DataQuery | str]:
        return PRODUCT_ALIASES


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="OMPS EDR Reader")

    group.add_argument(
        "--filter-o3",
        action=BooleanFilterAction,
        dest="filter_by_error_flag",
        type=int,
        default=[],
        const=[0, 1],
        help="Filter total ozone products by the 'ErrorFlag' variable. "
        "When enabled valid pixels are those where "
        "'ErrorFlag' is 0 or 1. Defaults to off. Specify '--filter-o3' to "
        "enable filtering.",
    )

    return group, None


def _int_or_none(value: str) -> None | int:
    if value.lower() == "none":
        return None
    return int(value)
