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
"""The AHI HSD Reader operates on HSD files
from the Himawari-8 Advanced Himawari Imager (AHI) instrument.
The AHI HSD reader analyzes the user provided filenames to determine if a file
can be used. Files usually have the following naming scheme::

    HS_H08_20181022_0300_B09_FLDK_R20_S1010.DAT

The AHI HSD reader supports all instrument spectral bands, identified as
the products shown below. The creation of the AHI HSD reader can
be specified to the main script with the reader name ``ahi_hsd``.

The list of supported products includes true and natural color imagery.
These are created by means of a python based atmospheric Rayleigh
scattering algorithm that is executed as part of the |project| reader.

+---------------------------+-----------------------------------------------------+
| Product Name              | Description                                         |
+===========================+=====================================================+
| B01                       | Channel 1 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B02                       | Channel 2 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B03                       | Channel 3 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B04                       | Channel 4 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B05                       | Channel 5 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B06                       | Channel 6 Reflectance Band                          |
+---------------------------+-----------------------------------------------------+
| B07                       | Channel 7 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| B08                       | Channel 8 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| B09                       | Channel 9 Brightness Temperature Band               |
+---------------------------+-----------------------------------------------------+
| B10                       | Channel 10 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B11                       | Channel 11 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B12                       | Channel 12 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B13                       | Channel 13 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B14                       | Channel 14 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B15                       | Channel 15 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| B16                       | Channel 16 Brightness Temperature Band              |
+---------------------------+-----------------------------------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |
+---------------------------+-----------------------------------------------------+
| natural_color             | Ratio sharpened rayleigh corrected natural color    |
+---------------------------+-----------------------------------------------------+

"""

READER_PRODUCTS = ['B{:02d}'.format(x) for x in range(1, 17)]
COMPOSITE_PRODUCTS = [
    'true_color',
    'natural_color',
]
DEFAULT_PRODUCTS = READER_PRODUCTS + COMPOSITE_PRODUCTS[:2]


def add_reader_argument_groups(parser):
    return parser
