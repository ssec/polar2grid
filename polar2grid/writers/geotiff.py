#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2018 Space Science and Engineering Center (SSEC),
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
"""The GeoTIFF writer puts gridded image data into a standard GeoTIFF file.  It
uses the GDAL python API and rasterio python package to create the GeoTIFF files.
It can handle any grid that can be described by PROJ.4 and understood by the
GeoTIFF format.

By default the 'geotiff' writer will add an "Alpha" band to the file to mark
any invalid or missing data pixels. This results in invalid pixels showing up
as transparent in most image viewers.

"""
import logging
from polar2grid.core.dtype import NUMPY_DTYPES, str2dtype, int_or_float

LOG = logging.getLogger(__name__)

# reader_name -> filename
DEFAULT_OUTPUT_FILENAME = {
    None: '{platform_name!u}_{sensor!u}_{name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.tif',
    'abi_l1b': '{platform_name!u}_{sensor!u}_{observation_type}{scene_abbr}_'
               '{name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.tif',
}


def add_writer_argument_groups(parser):
    group_1 = parser.add_argument_group(title='Geotiff Writer')
    group_1.add_argument('--output-filename', dest='filename',
                         help='custom file pattern to save dataset to')
    group_1.add_argument('--dtype', choices=[NUMPY_DTYPES], type=str2dtype,
                         help='Data type of the output file (8-bit unsigned '
                              'integer by default - uint8)')
    group_1.add_argument('--no-enhance', dest='enhance', action='store_false',
                         help='Don\'t try to enhance the data before saving it')
    group_1.add_argument('--fill-value', dest='fill_value', type=int_or_float,
                         help='Instead of an alpha channel fill invalid '
                              'values with this value. Turns LA or RGBA '
                              'images in to L or RGB images respectively.')
    # Saving specific keyword arguments
    # group_2 = parser.add_argument_group(title='Writer Save')
    return group_1, None
