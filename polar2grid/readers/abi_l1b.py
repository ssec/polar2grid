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
"""The ABI Level 1B Reader operates on NASA Level 1B (L1B) NetCDF files
from the GOES-EAST (GOES-16) and GOES-WEST (GOES-17) Advanced Baseline Imager (ABI) instrument.
The ABI L1B reader analyzes the user provided filenames to determine if a file
can be used. Files usually have the following naming scheme::

    OR_ABI-L1b-RadF-M3C16_G16_s20182531700311_e20182531711090_c20182531711149.nc

The ABI L1B reader supports all instrument spectral bands, identified as
the products shown below. The creation of the ABI L1B reader can
be specified to the main script with the reader name ``abi_l1b``.

The list of supported products includes true and false color imagery. 
These are created  by means of a python based atmospheric Rayleigh 
Scattering algorithm that is executed as part of the |project| ABI L1B
reader.  

+---------------------------+-----------------------------------------------------+
| Product Name              | Description                                         |
+===========================+=====================================================+
| C01                       | Channel 1 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| C02                       | Channel 2 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| C03                       | Channel 3 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| C04                       | Channel 4 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| C05                       | Channel 5 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| C06                       | Channel 6 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| C07                       | Channel 7 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| C08                       | Channel 8 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| C09                       | Channel 9 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| C10                       | Channel 10 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| C11                       | Channel 11 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| C12                       | Channel 12 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| C13                       | Channel 13 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| C14                       | Channel 14 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| C15                       | Channel 15 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| C16                       | Channel 16 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |
+---------------------------+-----------------------------------------------------+
| natural_color             | Ratio sharpened rayleigh corrected natural color    |
+---------------------------+-----------------------------------------------------+

"""

READER_PRODUCTS = ['C{:02d}'.format(x) for x in range(1, 17)]
COMPOSITE_PRODUCTS = [
    'true_color',
    'natural_color',
]
DEFAULT_PRODUCTS = READER_PRODUCTS + COMPOSITE_PRODUCTS


def add_frontend_argument_groups(parser):
    return parser
