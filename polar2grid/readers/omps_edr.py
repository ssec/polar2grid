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
with the reader name ``omps_edr``.

This reader's default remapping algorithm is ``nearest`` for nearest neighbor
resampling.

The products below come from two groups of files. The "TO3" products are
read from the total column ozone (``V8TOZ``) files shown above. The "TOS"
products are read from the sulfur dioxide EDR files and use the ``s_``
name prefix. Some products are available from both files.

+-----------------------+-------------------------------------------------------------+
| Product Name          | Description                                                 |
+=======================+=============================================================+
| Reflectivity331       | Reflectivity at 331nm                                       |
+-----------------------+-------------------------------------------------------------+
| AerosolIndex          | Aerosol index                                               |
+-----------------------+-------------------------------------------------------------+
| ColumnAmountO3        | Total Column of Ozone                                       |
+-----------------------+-------------------------------------------------------------+
| s_ColumnamountSO2_PBL | Total SO2, planetary boundary layer                         |
+-----------------------+-------------------------------------------------------------+
| s_ColumnamountSO2_TRL | Total SO2, 0~5km layer                                      |
+-----------------------+-------------------------------------------------------------+
| s_ColumnamountSO2_TRM | Total SO2, 5~10km layer                                     |
+-----------------------+-------------------------------------------------------------+
| s_ColumnamountSO2_STL | Total SO2, 15-19km layer                                    |
+-----------------------+-------------------------------------------------------------+
| s_TRLO3               | Corrected total O3 by assuming SO2 located in 0~5km layer   |
+-----------------------+-------------------------------------------------------------+
| s_TRMO3               | Corrected total O3 by assuming SO2 located in 5~10km layer  |
+-----------------------+-------------------------------------------------------------+
| s_STLO3               | Corrected total O3 by assuming SO2 located in 15-19km layer |
+-----------------------+-------------------------------------------------------------+

By default, the products are filtered based on the quality recommendations of
the algorithm developers. Each filter can be turned off with the ``--no-``
form of its flag (see below).

The ``--filter-ozone-by-error-flag`` flag removes pixels from the ozone
products (``ColumnAmountO3``, ``AerosolIndex``, and ``Reflectivity331``) where
the ``ErrorFlag`` variable is not 0, 1, or 2. These products are filtered the
same way whether they are read from the total column ozone or the sulfur
dioxide files.

The ``--filter-so2-by-error-flag`` flag removes pixels from the sulfur dioxide
file products (``s_ColumnamountSO2_*`` and ``s_*O3``) where the ``ErrorFlag``
variable is not 0, 1, or 5 (5 marks high SO2 values).

The ``--filter-eclipse`` flag removes pixels affected by a solar eclipse
(``EclipseFlag`` is not 0) from all products.

The ``--filter-negative-so2`` flag removes negative retrieval values from the
SO2 column amount products (``s_ColumnamountSO2_*``).

"""

from __future__ import annotations

from argparse import ArgumentParser, BooleanOptionalAction, _ArgumentGroup

from satpy import DataQuery

from ._base import ReaderProxyBase

PREFERRED_CHUNK_SIZE: int = 6400

PRODUCT_ALIASES = {}

TO3_PRODUCTS = ["Reflectivity331", "AerosolIndex", "ColumnAmountO3"]
TOS_PRODUCTS = [
    "ColumnAmountO3",
    "s_ColumnamountSO2_PBL",
    "s_ColumnamountSO2_TRL",
    "s_ColumnamountSO2_TRM",
    "s_ColumnamountSO2_STL",
    "s_STLO3",
    "s_TRLO3",
    "s_TRMO3",
]
DEFAULT_PRODUCTS = TO3_PRODUCTS + ["s_ColumnamountSO2_STL", "s_STLO3"]
P2G_PRODUCTS = TO3_PRODUCTS + TOS_PRODUCTS

# 'ErrorFlag' values to keep for each group of products
# Product names are the same as the Satpy/file variable names
OZONE_ERROR_FLAG_KEEP = [0, 1, 2]
OZONE_ERROR_FLAG_PRODUCTS = TO3_PRODUCTS
SO2_ERROR_FLAG_KEEP = [0, 1, 5]
SO2_ERROR_FLAG_PRODUCTS = [prod for prod in TOS_PRODUCTS if prod not in TO3_PRODUCTS]

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

    @classmethod
    def convert_reader_kwargs(cls, reader_kwargs: dict) -> dict:
        """Convert per-product-group error flag filtering flags to Satpy's per-variable mapping."""
        reader_kwargs = dict(reader_kwargs)
        error_flags_to_keep = {}
        if reader_kwargs.pop("filter_ozone_by_error_flag", False):
            error_flags_to_keep.update(dict.fromkeys(OZONE_ERROR_FLAG_PRODUCTS, OZONE_ERROR_FLAG_KEEP))
        if reader_kwargs.pop("filter_so2_by_error_flag", False):
            error_flags_to_keep.update(dict.fromkeys(SO2_ERROR_FLAG_PRODUCTS, SO2_ERROR_FLAG_KEEP))
        reader_kwargs["error_flags_to_keep"] = error_flags_to_keep or None
        return reader_kwargs


def add_reader_argument_groups(
    parser: ArgumentParser, group: _ArgumentGroup | None = None
) -> tuple[_ArgumentGroup | None, _ArgumentGroup | None]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="OMPS EDR Reader")

    group.add_argument(
        "--filter-ozone-by-error-flag",
        action=BooleanOptionalAction,
        default=True,
        dest="filter_ozone_by_error_flag",
        help="Remove pixels from the ozone products ("
        + ", ".join(OZONE_ERROR_FLAG_PRODUCTS)
        + ") where the 'ErrorFlag' variable is not "
        + _human_list(OZONE_ERROR_FLAG_KEEP)
        + ". This is on by default, specify '--no-filter-ozone-by-error-flag' to disable it.",
    )
    group.add_argument(
        "--filter-so2-by-error-flag",
        action=BooleanOptionalAction,
        default=True,
        dest="filter_so2_by_error_flag",
        help="Remove pixels from the SO2 file products ("
        + ", ".join(SO2_ERROR_FLAG_PRODUCTS)
        + ") where the 'ErrorFlag' variable is not "
        + _human_list(SO2_ERROR_FLAG_KEEP)
        + ". This is on by default, specify '--no-filter-so2-by-error-flag' to disable it.",
    )
    group.add_argument(
        "--filter-eclipse",
        action=BooleanOptionalAction,
        default=True,
        dest="filter_eclipse",
        help="Remove pixels affected by a solar eclipse ('EclipseFlag' is not 0) from all "
        "products. This is on by default, specify '--no-filter-eclipse' to disable it.",
    )
    group.add_argument(
        "--filter-negative-so2",
        action=BooleanOptionalAction,
        default=True,
        dest="filter_negative_so2",
        help="Remove negative values from the SO2 column amount products "
        "('s_ColumnamountSO2_*'). This is on by default, specify "
        "'--no-filter-negative-so2' to disable it.",
    )

    return group, None


def _human_list(values: list[int]) -> str:
    """Format values as a readable list (ex. '0, 1, or 2')."""
    str_values = [str(val) for val in values]
    return ", ".join(str_values[:-1]) + ", or " + str_values[-1]


def _int_or_none(value: str) -> int | None:
    if value.lower() == "none":
        return None
    return int(value)
