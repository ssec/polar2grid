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
"""Reader for NUCAPS Retrieval output.

Files for this reader should follow the naming scheme:

    NUCAPS-EDR_v1r0_npp_s201603011158009_e201603011158307_c201603011222270.nc

This reader can provide the following products:

+---------------------------+-----------------------------------------------------+
| Product Name              | Description                                         |
+===========================+=====================================================+
| Temperature_Xmb           | Temperature at various pressure levels              |
+---------------------------+-----------------------------------------------------+
| H2O_MR_Xmb                | Water Mixing Ratio at various pressure levels       |
+---------------------------+-----------------------------------------------------+

Pressure based datasets are specified by the pressure level desired in millibars.
If the pressure is less than 5mb then it should have three decimal places,
`Temperature_0.016`. If greater than 5mb then it should not contain any decimals
and should use the integer rounded version of the pressure level,
`Temperature_1071`. All pressure levels for a dataset can be requested using the
base name of the dataset, `Temperature`.

"""
__docformat__ = "restructuredtext en"

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
    parser.set_defaults(fornav_D=40, fornav_d=2, share_remap_mask=False, remap_method="nearest")

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
