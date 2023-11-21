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
"""The FCI Level 1c Reader operates on EUMETSAT Level 1c NetCDF files
from the Meteosat Third Generation (MTG) Flexible Combined Imager (FCI)
instrument. The FCI L1c reader works off of the input filenames
to determine if a file is supported by Geo2Grid. Files usually have the
following naming scheme::

    W_XX-EUMETSAT-Darmstadt,IMG+SAT,MTI1+FCI-1C-RRAD-FDHSI-FD--CHK-BODY---NC4E_C_EUMT_20170920115515_GTT_DEV_20170920115008_20170920115015_N__T_0072_0001.nc

The FCI L1c reader supports all instrument spectral bands, identified in
Geo2Grid as the products shown in the table below. The
reader can be provided to the main geo2grid.sh script
using the ``-r`` option and the reader name ``fci_l1c_nc``.

+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| vis_04                    | 0.44um Reflectance Band                             |
+---------------------------+-----------------------------------------------------+
| vis_05                    | 0.51um Reflectance Band                             |
+---------------------------+-----------------------------------------------------+
| vis_06                    | 0.64um Reflectance Band                             |
+---------------------------+-----------------------------------------------------+
| vis_08                    | 0.86um Reflectance Band                             |
+---------------------------+-----------------------------------------------------+
| vis_09                    | 0.91um Reflectance Band                             |
+---------------------------+-----------------------------------------------------+
| nir_13                    | 1.3um Near-IR Reflectance Band                      |
+---------------------------+-----------------------------------------------------+
| nir_16                    | 1.6um Near-IR Reflectance Band                      |
+---------------------------+-----------------------------------------------------+
| nir_22                    | 2.2um Near-IR Reflectance Band                      |
+---------------------------+-----------------------------------------------------+
| ir_38                     | 3.8um Brightness Temperature Band                   |
+---------------------------+-----------------------------------------------------+
| wv_63                     | 6.3um Water Vapor Brightness Temperature Band       |
+---------------------------+-----------------------------------------------------+
| wv_73                     | 7.3um Water Vapor Brightness Temperature Band       |
+---------------------------+-----------------------------------------------------+
| ir_87                     | 8.7um Brightness Temperature Band                   |
+---------------------------+-----------------------------------------------------+
| ir_97                     | 9.7um Brightness Temperature Band                   |
+---------------------------+-----------------------------------------------------+
| ir_105                    | 10.5um Brightness Temperature Band                  |
+---------------------------+-----------------------------------------------------+
| ir_123                    | 12.3um Brightness Temperature Band                  |
+---------------------------+-----------------------------------------------------+
| ir_133                    | 13.3um Brightness Temperature Band                  |
+---------------------------+-----------------------------------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |
+---------------------------+-----------------------------------------------------+
| natural_color             | Ratio sharpened corrected natural color             |
+---------------------------+-----------------------------------------------------+

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from ._base import ReaderProxyBase

PREFERRED_CHUNK_SIZE: int = 1024

READER_PRODUCTS = [
    "vis_04",
    "vis_05",
    "vis_06",
    "vis_08",
    "vis_09",
    "nir_13",
    "nir_16",
    "nir_22",
    "ir_23",
    "wv_63",
    "wv_73",
    "ir_87",
    "ir_97",
    "ir_105",
    "ir_123",
    "ir_133",
]
COMPOSITE_PRODUCTS = [
    "true_color",
    "natural_color",
]


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_geo2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return READER_PRODUCTS + COMPOSITE_PRODUCTS[:2]

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
        group = parser.add_argument_group(title="FCI L1c NetCDF Reader")
    load_group = parser.add_argument_group(title="FCI L1c NetCDF Reader Loading")
    load_group.add_argument(
        "--upper-right-corner",
        default="NE",
        help="Orientation of the data. Data in files is 'SE' for South-East "
        "which is upside down from the traditional 'north is up'. This "
        "argument defaults to 'NE' for North-East and produces the "
        "traditional north-up image orientation.",
    )
    return group, load_group
