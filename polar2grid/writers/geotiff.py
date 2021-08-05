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
import os
import logging
from polar2grid.core.dtype import NUMPY_DTYPE_STRS, str_to_dtype, int_or_float
from polar2grid.core.script_utils import NumpyDtypeList

LOG = logging.getLogger(__name__)

# reader_name -> filename
DEFAULT_OUTPUT_FILENAMES = {
    None: "{platform_name!u}_{sensor!u}_{p2g_name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.tif",
    "abi_l1b": "{platform_name!u}_{sensor!u}_{observation_type}{scene_abbr}_"
    "{p2g_name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.tif",
    "viirs_sdr": "{platform_name!l}_{sensor!l}_{p2g_name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.tif",
    "mirs": "{platform_name!l}_{sensor!l}_{p2g_name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.tif",
    "clavrx": "{platform_name!l}_{sensor!l}_{name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.tif",
    "virr_l1b": "{platform_name!l}_{sensor!l}_{name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.tif",
}


def add_writer_argument_groups(parser, group=None):
    from argparse import SUPPRESS

    if group is None:
        group = parser.add_argument_group(title="Geotiff Writer")
    group.add_argument(
        "--output-filename",
        dest="filename",
        help="Custom file pattern to save dataset to",
    )
    group.add_argument(
        "--dtype",
        choices=NumpyDtypeList(NUMPY_DTYPE_STRS),
        type=str_to_dtype,
        help="Data type of the output file (8-bit unsigned " "integer by default - uint8)",
    )
    group.add_argument(
        "--no-enhance",
        dest="enhance",
        action="store_false",
        help="Don't try to enhance the data before saving it",
    )
    group.add_argument(
        "--fill-value",
        dest="fill_value",
        type=int_or_float,
        help="Instead of an alpha channel fill invalid "
        "values with this value. Turns LA or RGBA "
        "images in to L or RGB images respectively.",
    )
    group.add_argument(
        "--compress",
        default="LZW",
        help="File compression algorithm (DEFLATE, LZW, NONE, etc)",
    )
    group.add_argument("--tiled", action="store_true", help="Create tiled geotiffs")
    group.add_argument("--blockxsize", default=SUPPRESS, type=int, help="Set tile block X size")
    group.add_argument("--blockysize", default=SUPPRESS, type=int, help="Set tile block Y size")
    group.add_argument(
        "--gdal-num-threads",
        dest="num_threads",
        default=os.environ.get("DASK_NUM_WORKERS", 4),
        help=SUPPRESS,
    )  # don't show this option to the user
    # help='Set number of threads used for compressing '
    #      'geotiffs (default: Same as num-workers)')
    group.add_argument(
        "--overviews",
        type=lambda x: x.split(" "),
        help="Build lower resolution versions of your image "
        "for better performance in some clients. "
        "Specified as a space separate list of numbers, "
        "typically as powers of 2. Example: '2 4 8 16'",
    )
    # Saving specific keyword arguments
    # group_2 = parser.add_argument_group(title='Writer Save')
    return group, None
