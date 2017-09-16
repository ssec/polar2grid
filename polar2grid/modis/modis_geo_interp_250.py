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

import numpy as np
from scipy.ndimage.interpolation import map_coordinates

import logging

LOG = logging.getLogger(__name__)

# MODIS has 10 rows of data in the array for every scan line
ROWS_PER_SCAN = 10
EARTH_RADIUS = 6370997.0

# FUTURE: Add this to the pytroll python-geotiepoints package if it can be more generalized
# Most of the cartesian conversions were taken from the existing python-geotiepoints develop branch

def get_lons_from_cartesian(x__, y__):
    """Get longitudes from cartesian coordinates.
    """
    return np.rad2deg(np.arccos(x__ / np.sqrt(x__ ** 2 + y__ ** 2))) * np.sign(y__)

def get_lats_from_cartesian(x__, y__, z__, thr=0.8):
    """Get latitudes from cartesian coordinates.
    """
    # if we are at low latitudes - small z, then get the
    # latitudes only from z. If we are at high latitudes (close to the poles)
    # then derive the latitude using x and y:

    lats = np.where(np.logical_and(np.less(z__, thr * EARTH_RADIUS),
                                   np.greater(z__, -1. * thr * EARTH_RADIUS)),
                    90 - np.rad2deg(np.arccos(z__/EARTH_RADIUS)),
                    np.sign(z__) *
                    (90 - np.rad2deg(np.arcsin(np.sqrt(x__ ** 2 + y__ ** 2)
                                         / EARTH_RADIUS))))
    return lats


def interpolate_geolocation_cartesian(lon_array, lat_array, res_factor=4):
    """Interpolate MODIS navigation from 1000m resolution to 250m.

    Python rewrite of the IDL function ``MODIS_GEO_INTERP_250`` but converts to cartesian (X, Y, Z) coordinates
    first to avoid problems with the anti-meridian/poles.

    :param nav_array: MODIS 1km latitude array or 1km longitude array

    :returns: MODIS 250m latitude array or 250m longitude array

    If we are going from 1000m to 250m we have 4 times the size of the original
    If we are going from 1000m to 250m we have 2 times the size of the original
    """
    num_rows,num_cols = lon_array.shape
    num_scans = num_rows / ROWS_PER_SCAN

    lons_rad = np.radians(lon_array)
    lats_rad = np.radians(lat_array)
    x_in = EARTH_RADIUS * np.cos(lats_rad) * np.cos(lons_rad)
    y_in = EARTH_RADIUS * np.cos(lats_rad) * np.sin(lons_rad)
    z_in = EARTH_RADIUS * np.sin(lats_rad)

    # Create an array of indexes that we want our result to have
    x = np.arange(res_factor * num_cols, dtype=np.float32) * (1./res_factor)
    # 0.375 for 250m, 0.25 for 500m
    y = np.arange(res_factor * ROWS_PER_SCAN, dtype=np.float32) * (1./res_factor) - (res_factor * (1./16) + (1./8))
    x,y = np.meshgrid(x,y)
    coordinates = np.array([y,x]) # Used by map_coordinates, major optimization

    new_x = np.empty((num_rows * res_factor, num_cols * res_factor), dtype=np.float64)
    new_y = new_x.copy()
    new_z = new_x.copy()
    nav_arrays = [(x_in, new_x), (y_in, new_y), (z_in, new_z)]

    # Interpolate each scan, one at a time, otherwise the math doesn't work well
    for scan_idx in range(num_scans):
        # Calculate indexes
        j0 = ROWS_PER_SCAN              * scan_idx
        j1 = j0 + ROWS_PER_SCAN
        k0 = ROWS_PER_SCAN * res_factor * scan_idx
        k1 = k0 + ROWS_PER_SCAN * res_factor

        for nav_array, result_array in nav_arrays:
            # Use bilinear interpolation for all 250 meter pixels
            map_coordinates(nav_array[ j0:j1, : ], coordinates, output=result_array[ k0:k1, : ], order=1, mode='nearest')

            if res_factor == 4:
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
            else:
                # 500m
                # Use linear extrapolation for the first two 250 meter pixels along track
                m = (result_array[ k0 + 2, : ] - result_array[ k0 + 1, : ]) / (y[2,0] - y[1,0])
                b = result_array[ k0 + 2, : ] - m * y[2,0]
                result_array[ k0 + 0, : ] = m * y[0,0] + b

                # Use linear extrapolation for the last  two 250 meter pixels along track
                m = (result_array[ k0 + 18, : ] - result_array[ k0 + 17, : ]) / (y[18,0] - y[17,0])
                b = result_array[ k0 + 18, : ] - m * y[18,0]
                result_array[ k0 + 19, : ] = m * y[19,0] + b

    # Convert from cartesian to lat/lon space
    new_lons = get_lons_from_cartesian(new_x, new_y)
    new_lats = get_lats_from_cartesian(new_x, new_y, new_z)

    return new_lons.astype(lon_array.dtype), new_lats.astype(lat_array.dtype)


def interpolate_geolocation(nav_array):
    """Interpolate MODIS navigation from 1000m resolution to 250m.

    Python rewrite of the IDL function ``MODIS_GEO_INTERP_250``

    :param nav_array: MODIS 1km latitude array or 1km longitude array

    :returns: MODIS 250m latitude array or 250m longitude array
    """
    num_rows,num_cols = nav_array.shape
    num_scans = num_rows / ROWS_PER_SCAN

    # Make a resulting array that is the right size for the new resolution
    result_array = np.empty((num_rows * res_factor, num_cols * res_factor), dtype=np.float32)
    x = np.arange(res_factor * num_cols, dtype=np.float32) * 0.25
    y = np.arange(res_factor * ROWS_PER_SCAN, dtype=np.float32) * 0.25 - 0.375
    x,y = np.meshgrid(x,y)
    coordinates = np.array([y,x]) # Used by map_coordinates, major optimization

    # Interpolate each scan, one at a time, otherwise the math doesn't work well
    for scan_idx in range(num_scans):
        # Calculate indexes
        j0 = ROWS_PER_SCAN              * scan_idx
        j1 = j0 + ROWS_PER_SCAN
        k0 = ROWS_PER_SCAN * res_factor * scan_idx
        k1 = k0 + ROWS_PER_SCAN * res_factor

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
