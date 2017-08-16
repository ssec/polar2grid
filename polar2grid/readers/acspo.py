#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2017 Space Science and Engineering Center (SSEC),
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
#     Written by David Hoese    April 2017
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""The ACSPO reader is for reading files created by the Advanced Clear-Sky
Processor for Oceans (ACSPO) system. The ACSPO system typically produces
NetCDF4 files. The frontend can be specified with the ``polar2grid.sh``
command using the ``acspo`` frontend name.
The ACSPO frontend provides the following products:

+------------------------+--------------------------------------------+
| Product Name           | Description                                |
+========================+============================================+
| sst                    | Sea Surface Temperature                    |
+------------------------+--------------------------------------------+
| wind_speed             | Wind Speed                                 |
+------------------------+--------------------------------------------+
| sea_ice_fraction       | Sea Ice Fraction                           |
+------------------------+--------------------------------------------+
| satellite_zenith_angle | Satellite Zenith Angle                     |
+------------------------+--------------------------------------------+

"""

import sys

import logging
from polar2grid.readers import ReaderWrapper, main

LOG = logging.getLogger(__name__)


class Frontend(ReaderWrapper):
    FILE_EXTENSIONS = [".nc"]
    DEFAULT_READER_NAME = "acspo"
    DEFAULT_DATASETS = ['sst']


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    from polar2grid.core.script_utils import ExtendAction
    # Set defaults for other components that may be used in polar2grid processing
    parser.set_defaults(fornav_D=40, fornav_d=1)

    # Use the append_const action to handle adding products to the list
    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                       help="List available frontend products and exit")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    group.add_argument("-p", "--products", dest="products", nargs="+", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    return ["Frontend Initialization", "Frontend Swath Extraction"]

if __name__ == "__main__":
    sys.exit(main(description="Extract ACSPO swath data into binary files",
                  add_argument_groups=add_frontend_argument_groups))
