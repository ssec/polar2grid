#!/usr/bin/env python
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
#     Written by David Hoese    June 2017
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""The CLAVR-x reader is for reading files created by the Community 
Satellite Processing Package (CSPP) Clouds from AVHRR Extended 
(CLAVR-x) processing system software. The CLAVR-x reader 
supports CSPP CLAVR-x product files created from VIIRS, MODIS 
and AVHRR imaging sensors in the native HDF4 format.
The reader can be specified with the ``polar2grid.sh``
command using the ``clavrx`` reader name.
The CLAVR-x reader provides the following products:

+------------------------+---------------------------------------------+
| Product Name           | Description                                 |
+========================+=============================================+
| cloud_type             | Cloud Type                                  |
+------------------------+---------------------------------------------+
| cld_height_acha        | Cloud Top Height (m)                        |
+------------------------+---------------------------------------------+
| cld_temp_acha          | Cloud Top Temperature (K)                   |
+------------------------+---------------------------------------------+
| cld_emiss_acha         | Cloud Emissivity                            |
+------------------------+---------------------------------------------+
| cld_opd_dcomp          | Cloud Optical Depth Daytime                 |
+------------------------+---------------------------------------------+
| cld_opd_nlcomp         | Cloud Optical Depth Nighttime               |
+------------------------+---------------------------------------------+
| cld_reff_dcomp         | Cloud Effective Radius Daytime (micron)     |
+------------------------+---------------------------------------------+
| cld_reff_nlomp         | Cloud Effective Radius Nightttime (micron)  |
+------------------------+---------------------------------------------+
| cloud_phase            | Cloud Phase  (5 category)                   |
+------------------------+---------------------------------------------+
| rain_rate              | Rain Rate (mm/hr)                           |
+------------------------+---------------------------------------------+
| refl_lunar_dnb_nom     | Lunar Reflectance (VIIRS DNB nighttime only)|
+------------------------+---------------------------------------------+

"""

import os
import sys
import logging
import numpy as np
from polar2grid.readers import ReaderWrapper, main

LOG = logging.getLogger(__name__)

# Limit the number of products shown to Polar2Grid users
# if the user uses the environment variable they can display more
ADVERTISED_DATASETS = os.environ.get('CLAVRX_AD_DATASETS', None)
if ADVERTISED_DATASETS == 'all':
    ADVERTISED_DATASETS = None
elif ADVERTISED_DATASETS:
    ADVERTISED_DATASETS = ADVERTISED_DATASETS.split(" ")
else:
    ADVERTISED_DATASETS = set([
        'cloud_type',
        'cld_temp_acha',
        'cld_height_acha',
        'cloud_phase',
        'cld_opd_dcomp',
        'cld_opd_nlcomp',
        'cld_reff_dcomp',
        'cld_reff_nlcomp',
        'cld_emiss_acha',
        'refl_lunar_dnb_nom',
        'rain_rate',
    ])

DAY_ONLY = ['cld_opd_dcomp', 'cld_reff_dcomp']
NIGHT_ONLY = ['cld_opd_nlcomp', 'cld_reff_nlcomp', 'refl_lunar_dnb_nom']


class Frontend(ReaderWrapper):
    FILE_EXTENSIONS = ['.hdf']
    DEFAULT_READER_NAME = 'clavrx'
    DEFAULT_DATASETS = [
        'cloud_type'
        'cld_temp_acha',
        'cld_height_acha',
        'cloud_phase',
        'cld_opd_dcomp',
        'cld_opd_nlcomp',
        'cld_reff_dcomp',
        'cld_reff_nlcomp',
        'cld_emiss_acha',
        'refl_lunar_dnb_nom',
        'rain_rate',
    ]

    @property
    def default_products(self):
        return set(self.DEFAULT_DATASETS) & set(self.available_product_names)

    @property
    def available_product_names(self):
        available = set(self.scene.available_dataset_names(reader_name=self.reader, composites=True))
        return sorted(available & set(self.all_product_names))

    @property
    def all_product_names(self):
        # print(ADVERTISED_DATASETS)
        # print(ADVERTISED_DATASETS & set(self.scene.all_dataset_names(reader_name=self.reader)))
        return ADVERTISED_DATASETS & set(self.scene.all_dataset_names(reader_name=self.reader))

    def filter(self, scene):
        self.filter_daynight_datasets(scene)

    def filter_daynight_datasets(self, scene):
        """Some products are only available at daytime or nighttime"""
        for k in DAY_ONLY + NIGHT_ONLY:
            if k in scene and np.all(scene[k].mask):
                LOG.info("Removing dataset '{}' because it is completely empty".format(k))
                del scene[k]


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
    sys.exit(main(description="Extract CLAVR-X swath data into binary files",
                  add_argument_groups=add_frontend_argument_groups))
