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
r"""The cf writer puts gridded image data into a `CF-compliant` netCDF file.

All datasets to be saved must have the same projection coordinates ``x`` and ``y``. If a scene holds datasets with
different grids, the CF compliant workaround is to save the datasets to separate files.

Group key and list values  must use escapes before quoting.

Example:
  >>>  python glue.py -r clavrx -w cf -f clavrx_OR_ABI-L1b-RadC-M6C01_G16_s202212419011712.level2.nc \
       -vvv -g WGS84_MESO --grid-configs mygrid.conf -p cld_press_acha cld_temp_acha --method nearest \
       --groups "{\"WGS84_MESO\": [\"cld_press_acha\", \"cld_temp_acha\"]}"

"""
import json
import logging

LOG = logging.getLogger(__name__)

# reader_name -> filename
DEFAULT_OUTPUT_FILENAMES = {
    "polar2grid": {
        None: "{platform_name}_{sensor}_{start_time:%Y%m%d_%H%M%S}.nc",
    },
    "geo2grid": {
        None: "{platform_name}_{sensor}_{start_time:%Y%m%d_%H%M%S}.nc",
    },
}


def add_writer_argument_groups(parser, group=None):
    if group is None:
        group = parser.add_argument_group(title="cf Writer")
    group.add_argument(
        "--output-filename",
        dest="filename",
        help="Custom file pattern to save dataset to",
    )
    group.add_argument(
        "--groups",
        dest="groups",
        type=json.loads,
        help="Group datasets according to the given assignment: `{'group_name': ['dataset1', 'dataset2', ...]}`.",
    )

    group.add_argument(
        "--header_attrs",
        dest="header_attrs",
        type=json.loads,
        help="Global attributes to be included.",
    )

    group.add_argument(
        "--engine",
        default="netcdf4",
        help="Module to be used for writing netCDF files. Follows xarray's"
        ":meth:`~xarray.Dataset.to_netcdf` engine choices with a"
        "preference for 'netcdf4'.",
    )
    group.add_argument(
        "--epoch",
        help="Reference time for encoding of time coordinates",
    )

    group.add_argument(
        "--exclude_attrs",
        nargs="+",
        help="List of dataset attributes to be excluded",
    )
    group.add_argument(
        "--no_lonlats",
        dest="include_lonlats",
        action="store_false",
        help="Don't include latitude and longitude coordinates.",
    )

    group.add_argument("--not_pretty", dest="pretty", action="store_true", help="Modify coordinate names")

    group.add_argument(
        "--no_include_orig_name",
        dest="include_orig_name",
        action="store_false",
        help="Do not include the original dataset name as a variable attribute in the final netcdf.",
    )

    group.add_argument(
        "--flatten_attrs",
        action="store_true",
        help="If invoked, flatten dict-type attributes",
    )

    group.add_argument(
        "--numeric_name_prefix",
        default="CHANNEL_",
        help="Prefix added to each variable. For name starting with a digit.Use '' or None to leave this out..",
    )

    return group, None
