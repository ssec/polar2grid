#!/usr/bin/env python
# encoding: utf-8
"""Interpolate MODIS 1km navigation arrays to 250m.
"""

import numpy
from scipy.ndimage.interpolation import map_coordinates

import os
import sys

import logging

log = logging.getLogger(__name__)

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

    print "Done processing"
    return result_array

def main():
    from argparse import ArgumentParser
    from polar2grid.core import Workspace
    parser = ArgumentParser(description="Create 250m navigation data from 1km navigation data")
    parser.add_argument("lon_in",
            help="1km Longitude flat binary file input")
    parser.add_argument("lat_in",
            help="1km Latitude flat binary file input")
    parser.add_argument("lon_out",
            help="Filename for output 250m longitude flat binary file, '%%{rows}d' and '%%{cols}d' are filled in")
    parser.add_argument("lat_out",
            help="Filename for output 250m longitude flat binary file, '%%{rows}d' and '%%{cols}d' are filled in")
    args = parser.parse_args()

    W = Workspace('.')
    lon_in = getattr(W, args.lon_in.split(".")[0])
    lat_in = getattr(W, args.lat_in.split(".")[0])

    #import cProfile
    #cProfile.runctx("lon_out = interpolate_geolocation(lon_in)", globals(), locals())
    #return 0
    lon_out = interpolate_geolocation(lon_in)
    lat_out = interpolate_geolocation(lat_in)

    lon_out_fn = args.lon_out % {"rows" : lon_out.shape[0], "cols" : lon_out.shape[1]}
    lat_out_fn = args.lat_out % {"rows" : lat_out.shape[0], "cols" : lat_out.shape[1]}

    lon_out.tofile(lon_out_fn)
    lat_out.tofile(lat_out_fn)

    return 0

if __name__ == "__main__":
    sys.exit(main())

