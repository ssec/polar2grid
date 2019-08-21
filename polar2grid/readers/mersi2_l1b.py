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
"""
The MERSI2 Level 1B reader operates on Level 1B (L1B) HDF5 files files come in four varieties; band data
and geolocation data, both at 250m and 1000m resolution.
Files usually have the following naming scheme:

    tf{start_time:%Y%j%H%M%S}.{platform_shortname}-{trans_band:1s}_MERSI_1000M_L1B.{ext}

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--fornav-D`` parameter is set to 40 and the
``--fornav-d`` parameter is set to 1.

+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| 1                         | Channel 1 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| 2                         | Channel 2 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| 3                         | Channel 3 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| 4                         | Channel 4 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| 5                         | Channel 5 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| 6                         | Channel 6 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| 7                         | Channel 7 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| 8                         | Channel 8 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| 9                         | Channel 9 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| 10                        | Channel 10 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 11                        | Channel 11 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 12                        | Channel 12 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 13                        | Channel 13 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 14                        | Channel 14 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 15                        | Channel 15 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 16                        | Channel 16 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 17                        | Channel 17 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 18                        | Channel 18 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 19                        | Channel 19 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 20                        | Channel 20 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 21                        | Channel 21 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 22                        | Channel 22 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 23                        | Channel 23 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 24                        | Channel 24 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| 25                        | Channel 25 Reflectance Band                         |
+---------------------------+-----------------------------------------------------+
| true_color                | Rayleigh corrected true color RGB                   |
+---------------------------+-----------------------------------------------------+
| natural_color             | Natural color RGB                                   |
+---------------------------+-----------------------------------------------------+
"""
import sys
import logging
from polar2grid.readers import ReaderWrapper, main

LOG = logging.getLogger(__name__)

ALL_BANDS = [str(x) for x in range(1, 26)]
ALL_ANGLES = ['solar_zenith_angle', 'solar_azimuth_angle', 'sensor_zenith_angle', 'sensor_azimuth_angle']
ALL_COMPS = ['true_color', 'natural_color']


class Frontend(ReaderWrapper):
    FILE_EXTENSIONS = ['.HDF']
    DEFAULT_READER_NAME = 'mersi2_l1b'
    DEFAULT_DATASETS = ALL_BANDS + ALL_COMPS

    @property
    def available_product_names(self):
        available = set(self.scene.available_dataset_names(reader_name=self.reader, composites=True))
        return sorted(available & set(self.all_product_names))

    @property
    def all_product_names(self):
        # return self.scene.all_dataset_names(reader_name=self.reader, composites=True)
        return ALL_BANDS + ALL_ANGLES + ALL_COMPS


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
    sys.exit(main(description="Extract MERSI2 L1B swath data into binary files",
                  add_argument_groups=add_frontend_argument_groups))
