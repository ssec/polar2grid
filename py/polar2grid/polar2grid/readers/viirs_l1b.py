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
"""SatPy compatible readers and legacy P2G frontends to wrap them.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2016 University of Wisconsin SSEC. All rights reserved.
:date:         Mar 2016
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

import sys
import logging
from polar2grid.readers import ReaderWrapper, main

LOG = logging.getLogger(__name__)


I_PRODUCTS = [
    "I01",
    "I02",
    "I03",
    "I04",
    "I05",
]
M_PRODUCTS = [
    "M01",
    "M02",
    "M03",
    "M04",
    "M05",
    "M06",
    "M07",
    "M08",
    "M09",
    "M10",
    "M11",
    "M12",
    "M13",
    "M14",
    "M15",
    "M16",
]
TRUE_COLOR_PRODUCTS = [
    "true_color"
]
FALSE_COLOR_PRODUCTS = [
    "false_color"
]


class Frontend(ReaderWrapper):
    FILE_EXTENSIONS = [".nc"]
    DEFAULT_READER_NAME = "viirs_l1b"
    DEFAULT_DATASETS = I_PRODUCTS + M_PRODUCTS + [
        "histogram_dnb",
        "adaptive_dnb",
        "dynamic_dnb",
    ]


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    from polar2grid.core.script_utils import ExtendAction, ExtendConstAction
    # Set defaults for other components that may be used in polar2grid processing
    parser.set_defaults(fornav_D=40, fornav_d=2)

    # Use the append_const action to handle adding products to the list
    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                       help="List available frontend products and exit")
    # group.add_argument("--no-tc", dest="use_terrain_corrected", action="store_false",
    #                    help="Don't use terrain-corrected navigation")
    # group.add_argument("--day-fraction", dest="day_fraction", type=float, default=float(os.environ.get("P2G_DAY_FRACTION", 0.10)),
    #                    help="Fraction of day required to produce reflectance products (default 0.10)")
    # group.add_argument("--night-fraction", dest="night_fraction", type=float, default=float(os.environ.get("P2G_NIGHT_FRACTION", 0.10)),
    #                    help="Fraction of night required to product products like fog (default 0.10)")
    # group.add_argument("--sza-threshold", dest="sza_threshold", type=float, default=float(os.environ.get("P2G_SZA_THRESHOLD", 100)),
    #                    help="Angle threshold of solar zenith angle used when deciding day or night (default 100)")
    # group.add_argument("--dnb-saturation-correction", action="store_true",
    #                    help="Enable dynamic DNB saturation correction (normally used for aurora scenes)")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    # FIXME: Probably need some proper defaults
    group.add_argument("-p", "--products", dest="products", nargs="+", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    group.add_argument('--i-bands', dest='products', action=ExtendConstAction, const=I_PRODUCTS,
                       help="Add all I-band raw products to list of products")
    group.add_argument('--m-bands', dest='products', action=ExtendConstAction, const=M_PRODUCTS,
                       help="Add all M-band raw products to list of products")
    group.add_argument("--true-color", dest='products', action=ExtendConstAction, const=TRUE_COLOR_PRODUCTS,
                       help="Add the True Color product to the list of products")
    group.add_argument("--false-color", dest='products', action=ExtendConstAction, const=FALSE_COLOR_PRODUCTS,
                       help="Add the False Color product to the list of products")
    # group.add_argument('--dnb-angle-products', dest='products', action=ExtendConstAction, const=DNB_ANGLE_PRODUCTS,
    #                    help="Add DNB-band geolocation 'angle' products to list of products")
    # group.add_argument('--i-angle-products', dest='products', action=ExtendConstAction, const=I_ANGLE_PRODUCTS,
    #                    help="Add I-band geolocation 'angle' products to list of products")
    # group.add_argument('--m-angle-products', dest='products', action=ExtendConstAction, const=M_ANGLE_PRODUCTS,
    #                    help="Add M-band geolocation 'angle' products to list of products")
    # group.add_argument('--m-rad-products', dest='products', action=ExtendConstAction, const=M_RAD_PRODUCTS,
    #                    help="Add M-band geolocation radiance products to list of products")
    # group.add_argument('--i-rad-products', dest='products', action=ExtendConstAction, const=I_RAD_PRODUCTS,
    #                    help="Add I-band geolocation radiance products to list of products")
    return ["Frontend Initialization", "Frontend Swath Extraction"]

if __name__ == "__main__":
    sys.exit(main(description="Extract VIIRS L1B swath data into binary files",
                  add_argument_groups=add_frontend_argument_groups))
