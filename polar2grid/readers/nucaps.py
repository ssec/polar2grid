#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2016 Space Science and Engineering Center (SSEC),
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
"""The NUCAPS Reader supports reading NUCAPS Retrieval files. This reader can be
used by specifying the name ``nucaps`` to the ``polar2grid.sh`` script.
Files for this reader should follow the naming scheme:

    NUCAPS-EDR_v1r0_npp_s201603011158009_e201603011158307_c201603011222270.nc

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--fornav-D`` parameter is set to 40 and the
``--fornav-d`` parameter is set to 1.

This reader can provide the following products:

+---------------------------+-----------------------------------------------------+
| Product Name              | Description                                         |
+===========================+=====================================================+
| Temperature_Xmb           | Temperature at various pressure levels              |
+---------------------------+-----------------------------------------------------+
| H2O_MR_Xmb                | Water Vapor Mixing Ratio at various pressure levels |
+---------------------------+-----------------------------------------------------+
| Topography                | Height at surface                                   |
+---------------------------+-----------------------------------------------------+
| Surface_Pressure          | Pressure at surface                                 |
+---------------------------+-----------------------------------------------------+
| Skin_Temperature          | Skin Temperature                                    |
+---------------------------+-----------------------------------------------------+

Pressure based datasets are specified by the pressure level desired in millibars.
The value used in the product name is listed in the table below for each corresponding
pressure value:

+--------------------+--------------------+
|Pressure Value      |Name Value          |
+====================+====================+
| 0.016              |0.016               |
+--------------------+--------------------+
| 0.038              |0.038               |
+--------------------+--------------------+
| 0.077              |0.077               |
+--------------------+--------------------+
| 0.137              |0.137               |
+--------------------+--------------------+
| 0.224              |0.224               |
+--------------------+--------------------+
| 0.345              |0.345               |
+--------------------+--------------------+
| 0.506              |0.506               |
+--------------------+--------------------+
| 0.714              |0.714               |
+--------------------+--------------------+
| 0.975              |0.975               |
+--------------------+--------------------+
| 1.297              |1.297               |
+--------------------+--------------------+
| 1.687              |1.687               |
+--------------------+--------------------+
| 2.153              |2.153               |
+--------------------+--------------------+
| 2.701              |2.701               |
+--------------------+--------------------+
| 3.340              |3.340               |
+--------------------+--------------------+
| 4.077              |4.077               |
+--------------------+--------------------+
| 4.920              |4.920               |
+--------------------+--------------------+
| 5.878              |6                   |
+--------------------+--------------------+
| 6.957              |7                   |
+--------------------+--------------------+
| 8.165              |8                   |
+--------------------+--------------------+
| 9.512              |10                  |
+--------------------+--------------------+
| 11.004             |11                  |
+--------------------+--------------------+
| 12.649             |13                  |
+--------------------+--------------------+
| 14.456             |14                  |
+--------------------+--------------------+
| 16.432             |16                  |
+--------------------+--------------------+
| 18.585             |19                  |
+--------------------+--------------------+
| 20.922             |21                  |
+--------------------+--------------------+
| 23.453             |23                  |
+--------------------+--------------------+
| 26.183             |26                  |
+--------------------+--------------------+
| 29.121             |29                  |
+--------------------+--------------------+
| 32.274             |32                  |
+--------------------+--------------------+
| 35.651             |36                  |
+--------------------+--------------------+
| 39.257             |39                  |
+--------------------+--------------------+
| 43.100             |43                  |
+--------------------+--------------------+
| 47.188             |47                  |
+--------------------+--------------------+
| 51.528             |52                  |
+--------------------+--------------------+
| 56.126             |56                  |
+--------------------+--------------------+
| 60.989             |61                  |
+--------------------+--------------------+
| 66.125             |66                  |
+--------------------+--------------------+
| 71.540             |72                  |
+--------------------+--------------------+
| 77.240             |77                  |
+--------------------+--------------------+
| 83.231             |83                  |
+--------------------+--------------------+
| 89.520             |90                  |
+--------------------+--------------------+
| 96.114             |96                  |
+--------------------+--------------------+
| 103.017            |103                 |
+--------------------+--------------------+
| 110.237            |110                 |
+--------------------+--------------------+
| 117.777            |118                 |
+--------------------+--------------------+
| 125.646            |126                 |
+--------------------+--------------------+
| 133.846            |134                 |
+--------------------+--------------------+
| 142.385            |142                 |
+--------------------+--------------------+
| 151.266            |151                 |
+--------------------+--------------------+
| 160.496            |160                 |
+--------------------+--------------------+
| 170.078            |170                 |
+--------------------+--------------------+
| 180.018            |180                 |
+--------------------+--------------------+
| 190.320            |190                 |
+--------------------+--------------------+
| 200.989            |201                 |
+--------------------+--------------------+
| 212.028            |212                 |
+--------------------+--------------------+
| 223.441            |223                 |
+--------------------+--------------------+
| 235.234            |235                 |
+--------------------+--------------------+
| 247.408            |247                 |
+--------------------+--------------------+
| 259.969            |260                 |
+--------------------+--------------------+
| 272.919            |273                 |
+--------------------+--------------------+
| 286.262            |286                 |
+--------------------+--------------------+
| 300.000            |300                 |
+--------------------+--------------------+
| 314.137            |314                 |
+--------------------+--------------------+
| 328.675            |329                 |
+--------------------+--------------------+
| 343.618            |344                 |
+--------------------+--------------------+
| 358.966            |359                 |
+--------------------+--------------------+
| 374.724            |375                 |
+--------------------+--------------------+
| 390.893            |391                 |
+--------------------+--------------------+
| 407.474            |407                 |
+--------------------+--------------------+
| 424.470            |424                 |
+--------------------+--------------------+
| 441.882            |442                 |
+--------------------+--------------------+
| 459.712            |460                 |
+--------------------+--------------------+
| 477.961            |478                 |
+--------------------+--------------------+
| 496.630            |497                 |
+--------------------+--------------------+
| 515.720            |516                 |
+--------------------+--------------------+
| 535.232            |535                 |
+--------------------+--------------------+
| 555.167            |555                 |
+--------------------+--------------------+
| 575.525            |576                 |
+--------------------+--------------------+
| 596.306            |596                 |
+--------------------+--------------------+
| 617.511            |618                 |
+--------------------+--------------------+
| 639.140            |639                 |
+--------------------+--------------------+
| 661.192            |661                 |
+--------------------+--------------------+
| 683.667            |684                 |
+--------------------+--------------------+
| 706.565            |707                 |
+--------------------+--------------------+
| 729.886            |730                 |
+--------------------+--------------------+
| 753.628            |754                 |
+--------------------+--------------------+
| 777.790            |778                 |
+--------------------+--------------------+
| 802.371            |802                 |
+--------------------+--------------------+
| 827.371            |827                 |
+--------------------+--------------------+
| 852.788            |853                 |
+--------------------+--------------------+
| 878.620            |879                 |
+--------------------+--------------------+
| 904.866            |905                 |
+--------------------+--------------------+
| 931.524            |932                 |
+--------------------+--------------------+
| 958.591            |959                 |
+--------------------+--------------------+
| 986.067            |986                 |
+--------------------+--------------------+
| 1013.950           |1014                |
+--------------------+--------------------+
| 1042.230           |1042                |
+--------------------+--------------------+
| 1070.920           |1071                |
+--------------------+--------------------+
| 1100.000           |1100                |
+--------------------+--------------------+

"""

# Above pressure list created using:
# line_fmt = "|{:<20}|{:<20}|"
# sep_fmt = "+{:<20}+{:<20}+"
# sep_line = sep_fmt.format('-'*20, '-'*20)
# title_line = sep_fmt.format('='*20, '='*20)
# pressure_lines = list(
#     line_fmt.format(" {:0.03f}".format(x),
#                     "{:0.0f}".format(x) if x >= 5. else "{:0.03f}".format(x)) for x in ALL_PRESSURE_LEVELS
# )
# pressure_lines = "\n".join(
#     [x + "\n" + y for x, y in itertools.izip_longest(pressure_lines, [sep_line]*len(pressure_lines))]
# )
# print("\n".join([sep_line, line_fmt.format("Pressure Value", "Name Value"), title_line] + [pressure_lines]))

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from satpy import DataQuery

from ._base import ReaderProxyBase

PRESSURE_BASED = ["Temperature", "H2O_MR"]


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return self.get_all_products()

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        reader = self.scn._readers["nucaps"]  # noqa
        products = ["Topography", "Surface_Pressure", "Skin_Temperature"]
        for base_name in PRESSURE_BASED:
            products.extend(reader.pressure_dataset_names[base_name])
        return products

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
        group = parser.add_argument_group(title="NUCAPS Reader")
    group.add_argument(
        "--no-mask-surface",
        dest="mask_surface",
        action="store_false",
        help="Don't mask pressure based datasets that go below the surface pressure",
    )
    group.add_argument(
        "--no-mask-quality", dest="mask_quality", action="store_false", help="Don't mask datasets based on Quality Flag"
    )
    load_group = parser.add_argument_group(title="NUCAPS Product Filters")
    load_group.add_argument(
        "--pressure-levels",
        nargs=2,
        type=float,
        default=(110.0, 987.0),
        help="Min and max pressure value to make available",
    )
    return group, load_group
