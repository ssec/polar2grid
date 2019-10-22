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
| 1                         | Channel 1 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| 2                         | Channel 2 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| 3                         | Channel 3 Emissive Band                             |
+---------------------------+-----------------------------------------------------+
| 4                         | Channel 4 Emissive Band                             |
+---------------------------+-----------------------------------------------------+
| 5                         | Channel 5 Emissive Band                             |
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
| true_color                | Ratio sharpened rayleigh corrected true color       |
+---------------------------+-----------------------------------------------------+
"""
import os
import sys
import logging
from polar2grid.readers import ReaderWrapper, main
from satpy import DatasetID
import numpy as np

LOG = logging.getLogger(__name__)

ALL_BANDS = [str(x) for x in range(1, 11)]
ALL_COMPS = ['true_color']
ALL_ANGLES = ['solar_zenith_angle', 'solar_azimuth_angle', 'sensor_zenith_angle', 'sensor_azimuth_angle']


class Frontend(ReaderWrapper):
    FILE_EXTENSIONS = ['.HDF']
    DEFAULT_READER_NAME = 'virr_l1b'
    DEFAULT_DATASETS = ALL_BANDS + ALL_COMPS

    def __init__(self, *args, **kwargs):
        self.day_fraction = kwargs.pop('day_fraction', 0.1)
        LOG.debug("Day fraction set to %f", self.day_fraction)
        # self.night_fraction = kwargs.pop('night_fraction', 0.1)
        # LOG.debug("Night fraction set to %f", self.night_fraction)
        self.sza_threshold = kwargs.pop('sza_threshold', 100.)
        LOG.debug("SZA threshold set to %f", self.sza_threshold)
        self.fraction_day_scene = None
        self.fraction_night_scene = None
        super(Frontend, self).__init__(**kwargs)

    @property
    def available_product_names(self):
        available = set(self.scene.available_dataset_names(reader_name=self.reader, composites=True))
        return sorted(available & set(self.all_product_names))

    @property
    def all_product_names(self):
        # return self.scene.all_dataset_names(reader_name=self.reader, composites=True)
        return ALL_BANDS + ALL_ANGLES + ALL_COMPS

    def _calc_percent_day(self, scene):
        if 'solar_zenith_angle' in scene:
            sza_data = scene['solar_zenith_angle']
        else:
            for sza_name in ('solar_zenith_angle',):
                scene.load([sza_name])
                if sza_name not in scene:
                    continue
                sza_data = scene[sza_name]
                del scene[sza_name]
                break
            else:
                raise ValueError("Could not check day or night time percentage without SZA data")

        sza_data = sza_data.persist()
        invalid_mask = sza_data.isnull().compute().data
        valid_day_mask = (sza_data < self.sza_threshold) & ~invalid_mask
        valid_night_mask = (sza_data >= self.sza_threshold) & ~invalid_mask
        self.fraction_day_scene = np.count_nonzero(valid_day_mask) / (float(sza_data.size) - np.count_nonzero(invalid_mask))
        self.fraction_night_scene = np.count_nonzero(valid_night_mask) / (float(sza_data.size) - np.count_nonzero(invalid_mask))
        LOG.debug("Fraction of scene that is valid day pixels: %f%%", self.fraction_day_scene * 100.)
        LOG.debug("Fraction of scene that is valid night pixels: %f%%", self.fraction_night_scene * 100.)

    def filter(self, scene):
        self.filter_daytime(scene)

    def filter_daytime(self, scene):
        if self.fraction_day_scene is None:
            self._calc_percent_day(scene)
        # make a copy of the scene list so we can edit it later
        for ds in list(scene):
            if ds.attrs['standard_name'] in ('toa_bidirectional_reflectance', 'false_color', 'true_color') and \
                    self.fraction_day_scene <= self.day_fraction:
                ds_id = DatasetID.from_dict(ds.attrs)
                LOG.info("Will not create product '%s' because there is less than %f%% of day data",
                         ds.attrs['name'], self.day_fraction * 100.)
                del scene[ds_id]


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
    group.add_argument("--day-fraction", dest="day_fraction", type=float, default=float(os.environ.get("P2G_DAY_FRACTION", 0.10)),
                       help="Fraction of day required to produce reflectance products (default 0.10)")
    # group.add_argument("--night-fraction", dest="night_fraction", type=float, default=float(os.environ.get("P2G_NIGHT_FRACTION", 0.10)),
    #                    help="Fraction of night required to product products like fog (default 0.10)")
    group.add_argument("--sza-threshold", dest="sza_threshold", type=float, default=float(os.environ.get("P2G_SZA_THRESHOLD", 100)),
                       help="Angle threshold of solar zenith angle used when deciding day or night (default 100)")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    group.add_argument("-p", "--products", dest="products", nargs="+", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    return ["Frontend Initialization", "Frontend Swath Extraction"]


if __name__ == "__main__":
    sys.exit(main(description="Extract VIRR L1B swath data into binary files",
                  add_argument_groups=add_frontend_argument_groups))
