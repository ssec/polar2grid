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
The VIIRS EDR Active Fires reader operates on NetCDF and ASCII files.
Files usually have the following naming scheme:

    AFIMG_{satellite_name}_d{start_time:%Y%m%d_t%H%M%S%f}_e{end_time:%H%M%S%f}_b{orbit:5d}_c{creation_time}_{source}.nc
    or
    AFIMG_{satellite_name}_d{start_time:%Y%m%d_t%H%M%S%f}_e{end_time:%H%M%S%f}_b{orbit:5d}_c{creation_time}_{source}.txt

This reader's default resampling algorithm is ``nearest`` for Nearest Neighbor resampling.
The ``--remap_method`` parameter is set to ``nearest``.

+---------------------------+-----------------------------------------------------+
| **Product Name**          | **Description**                                     |
+===========================+=====================================================+
| confidence_cat            | Confidence of there being a fire                    |
+---------------------------+-----------------------------------------------------+
| confidence_pct            |                                                     |
+---------------------------+-----------------------------------------------------+
| power                     |                                                     |
+---------------------------+-----------------------------------------------------+
| T13                       |                                                     |
+---------------------------+-----------------------------------------------------+
| T4                        |                                                     |
+---------------------------+-----------------------------------------------------+
"""
import sys
import logging
from polar2grid.readers import ReaderWrapper, main

LOG = logging.getLogger(__name__)


class Frontend(ReaderWrapper):
    FILE_EXTENSIONS = ['.nc', '.txt']
    DEFAULT_READER_NAME = 'viirs_edr_active_fires'
    # confidence_cat and T4 are IMG resolution only
    # confidence_pct and T13 are MOD resolution only
    DEFAULT_DATASETS = ['T4', 'T13', 'confidence_cat', 'confidence_pct', 'power']

    @property
    def available_product_names(self):
        available = set(self.scene.available_dataset_names(reader_name=self.reader, composites=True))
        # remove longitude and latitude as available datasets to avoid confusion
        available -= {'longitude', 'latitude'}
        return sorted(available & set(self.all_product_names))


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    from polar2grid.core.script_utils import ExtendAction
    # Set defaults for other components that may be used in polar2grid processing
    parser.set_defaults(remap_method='nearest', grid_coverage=0)

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
    sys.exit(main(description="Extract VIIRS_EDR_ACTIVE_FIRES swath data into binary files",
                  add_argument_groups=add_frontend_argument_groups))
