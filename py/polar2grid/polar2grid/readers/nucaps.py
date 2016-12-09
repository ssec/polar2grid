#!/usr/bin/env python
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
#
#     Written by David Hoese    March 2016
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
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
__docformat__ = "restructuredtext en"

# Above pressure list created using:
# line_fmt = "|{:<20}|{:<20}|"
# sep_fmt = "+{:<20}+{:<20}+"
# sep_line = sep_fmt.format('-'*20, '-'*20)
# title_line = sep_fmt.format('='*20, '='*20)
# pressure_lines = list(line_fmt.format(" {:0.03f}".format(x), "{:0.0f}".format(x) if x >= 5.else "{:0.03f}".format(x)) for x in ALL_PRESSURE_LEVELS)
# pressure_lines = "\n".join([x + "\n" + y for x, y in itertools.izip_longest(pressure_lines, [sep_line]*len(pressure_lines))])
# print("\n".join([sep_line, line_fmt.format("Pressure Value", "Name Value"), title_line] + [pressure_lines]))

import sys
import logging
from polar2grid.readers import ReaderWrapper, main

LOG = logging.getLogger(__name__)


class Frontend(ReaderWrapper):
    FILE_EXTENSIONS = [".nc"]
    DEFAULT_READER_NAME = "nucaps"
    DEFAULT_DATASETS = []

    def __init__(self, *args, **kwargs):
        super(Frontend, self).__init__(*args, **kwargs)
        reader = self.scene.readers[self.reader]
        self.DEFAULT_DATASETS = []
        for base_name in ["Temperature", "H2O_MR"]:
            self.DEFAULT_DATASETS.extend(reader.pressure_dataset_names[base_name])

    def create_scene(self, products=None, **kwargs):
        # P2G can't handle 3D sets so we know if they have non-pressure separated dataset names
        # they mean all of them
        if products:
            old_products = products
            products = []
            for product in old_products:
                if not product.endswith("mb"):
                    products.extend(self.scene.readers[self.reader].pressure_dataset_names[product])
                else:
                    products.append(product)
        return super(Frontend, self).create_scene(products=products, **kwargs)


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    from polar2grid.core.script_utils import ExtendAction
    # Set defaults for other components that may be used in polar2grid processing
    parser.set_defaults(fornav_D=40, fornav_d=1, share_remap_mask=False, remap_method="nearest")

    # Use the append_const action to handle adding products to the list
    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                       help="List available frontend products and exit")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    # FIXME: Probably need some proper defaults
    group.add_argument("-p", "--products", dest="products", nargs="+", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    group.add_argument("--pressure-levels", nargs=2, type=float, default=(110., 987.0),
                       help="Min and max pressure value to make available")
    return ["Frontend Initialization", "Frontend Swath Extraction"]

if __name__ == "__main__":
    sys.exit(main(description="Extract VIIRS L1B swath data into binary files",
                  add_argument_groups=add_frontend_argument_groups))
