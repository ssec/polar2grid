#!/usr/bin/env python
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
"""Interpolate MODIS 1km navigation arrays to 250m.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2014
:license:      GNU GPLv3
"""

import numpy
from scipy.ndimage.interpolation import map_coordinates

import logging

LOG = logging.getLogger(__name__)

# MODIS has 10 rows of data in the array for every scan line
ROWS_PER_SCAN = 10
# If we are going from 1000m to 250m we have 4 times the size of the original
RES_FACTOR = 4


def interpolate_geolocation(nav_array):
    """Interpolate MODIS navigation from 1000m resolution to 250m.

    Python rewrite of the IDL function ``MODIS_GEO_INTERP_250``

    :param nav_array: MODIS 1km latitude array or 1km longitude array

    :returns: MODIS 250m latitude array or 250m longitude array
    """
    num_rows,num_cols = nav_array.shape
    num_scans = num_rows / ROWS_PER_SCAN

    # Make a resulting array that is the right size for the new resolution
    result_array = numpy.empty( (num_rows * RES_FACTOR, num_cols * RES_FACTOR), dtype=numpy.float32 )
    x = numpy.arange(RES_FACTOR * num_cols, dtype=numpy.float32) * 0.25
    y = numpy.arange(RES_FACTOR * ROWS_PER_SCAN, dtype=numpy.float32) * 0.25 - 0.375
    x,y = numpy.meshgrid(x,y)
    coordinates = numpy.array([y,x]) # Used by map_coordinates, major optimization

    # Interpolate each scan, one at a time, otherwise the math doesn't work well
    for scan_idx in range(num_scans):
        # Calculate indexes
        j0 = ROWS_PER_SCAN              * scan_idx
        j1 = j0 + ROWS_PER_SCAN
        k0 = ROWS_PER_SCAN * RES_FACTOR * scan_idx
        k1 = k0 + ROWS_PER_SCAN * RES_FACTOR

        # Use bilinear interpolation for all 250 meter pixels
        map_coordinates(nav_array[ j0:j1, : ], coordinates, output=result_array[ k0:k1, : ], order=1, mode='nearest')

        # Use linear extrapolation for the first two 250 meter pixels along track
        m = (result_array[ k0 + 5, : ] - result_array[ k0 + 2, : ]) / (y[5,0] - y[2,0])
        b = result_array[ k0 + 5, : ] - m * y[5,0]
        result_array[ k0 + 0, : ] = m * y[0,0] + b
        result_array[ k0 + 1, : ] = m * y[1,0] + b

        # Use linear extrapolation for the last  two 250 meter pixels along track
        m = (result_array[ k0 + 37, : ] - result_array[ k0 + 34, : ]) / (y[37,0] - y[34,0])
        b = result_array[ k0 + 37, : ] - m * y[37,0]
        result_array[ k0 + 38, : ] = m * y[38,0] + b
        result_array[ k0 + 39, : ] = m * y[39,0] + b

    return result_array
