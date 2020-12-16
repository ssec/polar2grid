#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2020 Space Science and Engineering Center (SSEC),
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
"""

+-----------------------------------+--------------------------------------------+
| Product Name                      | Description                                |
+===========================+====================================================+
| Rain_Rate                         | Surface Rain Rate                          |
+-----------------------------------+--------------------------------------------+
| CLW                               | Cloud Liquid Water                         |
+-----------------------------------+--------------------------------------------+
| SST                               | Sea Surface Temperature                    |
+-----------------------------------+--------------------------------------------+
| TPW                               | Total Precipitable Water                   |
+-----------------------------------+--------------------------------------------+
| WSPD                              | Wind Speed                                 |
+-----------------------------------+--------------------------------------------+
| Snow_Cover                        | Snow Cover (Snow Surface Flag)             |
+-----------------------------------+--------------------------------------------+
| SWE                               | Snow Water Equivalent                      |
+-----------------------------------+--------------------------------------------+
| Snow_Depth                        | Snow Depth                                 |
+-----------------------------------+--------------------------------------------+
| Soil_Moisture                     | Soil Moisture                              |
+-----------------------------------+--------------------------------------------+
| NASA_Team_2_Ice_Concentration_NH  |  Ice Concentration (Northern Hemisphere)   |
+-----------------------------------+--------------------------------------------+

"""

OCEAN_PRECIP_PRODUCTS = [
    "Rain_Rate",
    "CLW",
    "SST",
    "TPW",
    "WSPD",
]
SNOW_PRODUCTS = [
    "Snow_Cover",
    "SWE",
    "Snow_Depth",
]
SOIL_PRODUCTS = [
    "Soil_Moisture",
]
SEAICE_PRODUCTS = [
    "NASA_Team_2_Ice_Concentration_NH",
    # "Latency_NH",
]

DEFAULT_PRODUCTS = OCEAN_PRECIP_PRODUCTS + SNOW_PRODUCTS + SOIL_PRODUCTS + SEAICE_PRODUCTS


def add_reader_argument_groups(parser):
    return parser
