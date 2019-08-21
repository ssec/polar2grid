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
#
#     Written by William Roberts and David Hoese    May 2019
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     wroberts4@wisc.edu and david.hoese@ssec.wisc.edu
"""The VIRR Level 1B reader operates on Level 1B (L1B) HDF5 files.
Files usually have the following naming scheme:

    tf2018343030324.FY3C-L_VIRRX_L1B.HDF or tf2018343092538.FY3B-L_VIRRX_L1B.HDF
    the numbers at the start are year julian-day hour minute seconds

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--fornav-D`` parameter is set to 40 and the
``--fornav-d`` parameter is set to 1.

+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| R1                        | Channel 1 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| R2                        | Channel 2 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| E1                        | Channel 3 Emissive Band                             |
+---------------------------+-----------------------------------------------------+
| E2                        | Channel 4 Emissive Band                             |
+---------------------------+-----------------------------------------------------+
| E3                        | Channel 5 Emissive Band                             |
+---------------------------+-----------------------------------------------------+
| R3                        | Channel 6 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| R4                        | Channel 7 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| R5                        | Channel 8 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| R6                        | Channel 9 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| R7                        | Channel 10 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |
+---------------------------+-----------------------------------------------------+
"""
import sys
import logging
from polar2grid.readers import ReaderWrapper, main

LOG = logging.getLogger(__name__)

ALL_RBANDS = ['R{:d}'.format(x) for x in range(1, 8)]
ALL_EBANDS = ['E{:d}'.format(x) for x in range(1, 4)]
ALL_COMPS = ['true_color']


class Frontend(ReaderWrapper):
    FILE_EXTENSIONS = ['.HDF']
    DEFAULT_READER_NAME = 'virr_l1b'
    DEFAULT_DATASETS = ALL_RBANDS + ALL_EBANDS + ALL_COMPS


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
    sys.exit(main(description="Extract VIRR L1B swath data into binary files",
                  add_argument_groups=add_frontend_argument_groups))
