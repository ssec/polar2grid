#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
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
#     Written by David Hoese    December 2014
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""Tests for polar2grid.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import numpy


def create_test_longitude(start, stop, shape, twist_factor=0.0, dtype=numpy.float32):
    if start > stop:
        stop += 360.0

    lon_row = numpy.linspace(start, stop, num=shape[1]).astype(dtype)
    twist_array = numpy.arange(shape[0]).reshape((shape[0], 1)) * twist_factor
    lon_array = numpy.repeat([lon_row], shape[0], axis=0)
    lon_array += twist_array

    if stop > 360.0:
        lon_array[lon_array > 360.0] -= 360
    return lon_array


def create_test_latitude(start, stop, shape, twist_factor=0.0, dtype=numpy.float32):
    lat_col = numpy.linspace(start, stop, num=shape[0]).astype(dtype).reshape((shape[0], 1))
    twist_array = numpy.arange(shape[1]) * twist_factor
    lat_array = numpy.repeat(lat_col, shape[1], axis=1)
    lat_array += twist_array
    return lat_array
