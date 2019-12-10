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

+---------------------------+-----------------------------------------------------+-------------------------+
| **Product Name**          | **Description**                                     | Central Wavelength (um) |
+===========================+=====================================================+=========================+
| 1                         | Channel 1 Reflectance Band                          |0.63                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| 2                         | Channel 2 Reflectance Band                          |0.865                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 3                         | Channel 3 Emissive Band                             |3.74                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| 4                         | Channel 4 Emissive Band                             |10.8                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| 5                         | Channel 5 Emissive Band                             |12.0                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| 6                         | Channel 6 Reflectance Band                          |1.60                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| 7                         | Channel 7 Reflectance Band                          |0.455                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 8                         | Channel 8 Reflectance Band                          |0.505                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 9                         | Channel 9 Reflectance Band                          |0.555                    |
+---------------------------+-----------------------------------------------------+-------------------------+
| 10                        | Channel 10 Reflectance Band                         |1.36                     |
+---------------------------+-----------------------------------------------------+-------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |N/A                      |
+---------------------------+-----------------------------------------------------+-------------------------+
"""
import sys
import logging
from polar2grid.readers import ReaderWrapper, main

LOG = logging.getLogger(__name__)

ALL_BANDS = [str(x) for x in range(1, 11)]
ALL_COMPS = ['true_color']
ALL_ANGLES = ['solar_zenith_angle', 'solar_azimuth_angle', 'sensor_zenith_angle', 'sensor_azimuth_angle']


class Frontend(ReaderWrapper):
    FILE_EXTENSIONS = ['.HDF']
    DEFAULT_READER_NAME = 'virr_l1b'
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
    sys.exit(main(description="Extract VIRR L1B swath data into binary files",
                  add_argument_groups=add_frontend_argument_groups))
