#!/usr/bin/env python
# encoding: utf-8
"""Python replacement for ms2gt's ll2cr using pyproj and
proj4 strings.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3

Copyright (C) 2013 Space Science and Engineering Center (SSEC),
 University of Wisconsin-Madison.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

This file is part of the polar2grid software package. Polar2grid takes
satellite observation data, remaps it, and writes it to a file format for
input into another program.
Documentation: http://www.ssec.wisc.edu/software/polar2grid/

    Written by David Hoese    January 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

from polar2grid.core import Workspace
from polar2grid.core.constants import DEFAULT_FILL_VALUE
from polar2grid.proj import Proj
import numpy

import os
import sys
import logging
import math

log = logging.getLogger(__name__)

def _transform_point(tformer, lon, lat, proj_circum, stradles_anti=False):
    """Transform single points into the projection Proj object provided.

    Main purpose is to handle if the data is in the west/negative side
    of the projections reference and it stradles the anti-meridian, then move
    it to the positive side by adding on 360 degrees worth of projection
    units.

    Example (EPSG 4326 : wgs84 lat/lon)
    -----------------------------------
    If data crosses -180/180 (the anti-meridian of 4326) then if -179.0
    is the longitude value of the data, add a full circumference (360) to that
    projected value to place it in the positive range (181.0).  That way
    origin math difference calculations work properly (181-170=11 instead of
    -179-170=-349).
    """
    x,y = tformer(lon, lat)
    if stradles_anti and x < 0:
        # Put negative values into the positive side
        log.debug("Point crosses the anti-meridian, adding %f" % (proj_circum,))
        x += proj_circum
    return x,y

def _transform_array(tformer, lon, lat, proj_circum, stradles_anti=False):
    """See _transform_point above
    """
    x,y = tformer(lon, lat)
    if stradles_anti:
        x[x < 0] += proj_circum
    return x,y

def ll2cr(lon_arr, lat_arr, proj4_str,
        pixel_size_x=None, pixel_size_y=None,
        grid_origin_x=None, grid_origin_y=None,
        swath_lat_south=None, swath_lat_north=None,
        swath_lon_west=None, swath_lon_east=None,
        grid_width=None, grid_height=None,
        dtype=None,
        fill_in=None,
        lon_fill_in=None,
        lat_fill_in=None,
        fill_out=-1e30,
        rows_fn=None,
        cols_fn=None,
        prefix="ll2cr_"):
    """Similar to GDAL, y pixel resolution should be negative for downward
    images.

    origin_lon,origin_lat are the grids origins
    """
    lon_fill_in = lon_fill_in or fill_in or DEFAULT_FILL_VALUE
    lat_fill_in = lat_fill_in or lon_fill_in

    ### Parameter check ###

    if lat_arr.shape != lon_arr.shape:
        log.error("Longitude and latitude arrays must be the same shape (%r vs %r)" % (lat_arr.shape, lon_arr.shape))
        raise ValueError("Longitude and latitude arrays must be the same shape (%r vs %r)" % (lat_arr.shape, lon_arr.shape))

    if (pixel_size_x is None and pixel_size_y is not None) or \
            (pixel_size_y is None and pixel_size_x is not None):
        log.error("pixel_size_x and pixel_size_y must both be specified or neither")
        raise ValueError("pixel_size_x and pixel_size_y must both be specified or neither")

    if (grid_width is None and grid_height is not None) or \
            (grid_width is not None and grid_height is None):
        log.error("grid_width and grid_height must both be specified or neither")
        raise ValueError("grid_width and grid_height must both be specified or neither")

    if (grid_origin_x is None and grid_origin_y is not None) or \
            (grid_origin_y is None and grid_origin_x is not None):
        log.error("grid_origin_x and grid_origin_y must both be specified or neither")
        raise ValueError("grid_origin_x and grid_origin_y must both be specified or neither")

    if pixel_size_x is None and grid_width is None:
        log.error("Either pixel size or grid width/height must be specified")
        raise ValueError("Either pixel size or grid width/height must be specified")

    # Handle EPSG codes
    tformer = Proj(proj4_str)

    if dtype is None:
        dtype = lat_arr.dtype

    # Memory map the output filenames
    # cols then rows in FBF filenames
    if rows_fn is None:
        rows_fn = prefix + "_rows.real4.%d.%d" % lat_arr.shape[::-1]
    rows_arr = numpy.memmap(rows_fn, dtype=dtype, mode="w+", shape=lat_arr.shape)
    if cols_fn is None:
        cols_fn = prefix + "_cols.real4.%d.%d" % lat_arr.shape[::-1]
    cols_arr = numpy.memmap(cols_fn, dtype=dtype, mode="w+", shape=lat_arr.shape)

    good_mask = (lon_arr != lon_fill_in) & (lat_arr != lat_fill_in)

    # Calculate west/east south/north boundaries
    # These can be provided by the user to save time
    stradles_180 = False
    if grid_origin_x is None or grid_width is None or pixel_size_x is None:
        if swath_lon_west is None:
            swath_lon_west = float(lon_arr[good_mask].min())
            log.debug("Data west longitude: %f" % swath_lon_west)
        if swath_lon_east is None:
            swath_lon_east = float(lon_arr[good_mask].max())
            log.debug("Data east longitude: %f" % swath_lon_east)
        if swath_lat_south is None:
            swath_lat_south = float(lat_arr[good_mask].min())
            log.debug("Data south latitude: %f" % swath_lat_south)
        if swath_lat_north is None:
            swath_lat_north = float(lat_arr[good_mask].max())
            log.debug("Data upper latitude: %f" % swath_lat_north)

        # Are we on the -180/180 boundary
        if swath_lon_west <= -179.0 and swath_lon_east >= 179.0:
            # Obviously assumes data is not smaller than 1 degree longitude wide
            swath_lon_west = float(lon_arr[ good_mask & (lon_arr < 0) ].max())
            log.debug("Data west longitude: %f" % swath_lon_west)
            swath_lon_east = float(lon_arr[ good_mask & (lon_arr > 0) ].min())
            log.debug("Data east longitude: %f" % swath_lon_east)
            stradles_180 = True

    ### Find out if we stradle the anti-meridian of the projection ###
    # Get the projections origin in lon/lat space
    proj_anti_lon,proj_anti_lat = tformer(0, 0, inverse=True)
    # get the 'opposite' side of the globe
    proj_anti_lon += 180 if proj_anti_lon < 0 else -180
    # Get projection units of the anti-meridian (positive only, it's a distance)
    proj_anti_x = abs(tformer(proj_anti_lon, proj_anti_lat)[0])
    # half the circumerence multiplied by 2 (full circumference in projection units)
    proj_circum = proj_anti_x * 2
    # Get data bounds as projection units
    if grid_width is not None and pixel_size_x is not None and grid_origin_x is not None:
        # If we have a fully defined grid then we can do exact measurements
        # XXX: Can this be done with one less parameter? I don't think so -djh
        data_grid_west = grid_origin_x
        data_grid_east = grid_origin_x + pixel_size_x * grid_width
    else:
        # The size of the grid is based on the data, so use the data bounds
        data_grid_west = tformer(swath_lon_west, proj_anti_lat)[0]
        data_grid_east = tformer(swath_lon_east, proj_anti_lat)[0]
    # Put data into positive domain
    data_grid_west += proj_circum if data_grid_west < 0 else 0
    data_grid_east += proj_circum if data_grid_east < 0 else 0

    # see if the grids bounds stradle the anti-meridian
    stradles_anti = False
    if (data_grid_west < proj_anti_x) and (data_grid_east > proj_anti_x):
        log.debug("Data crosses the projections anti-meridian")
        stradles_anti = True

    # If we are doing anything dynamic, then we need to get the bounding box of the data in *grid* space
    if grid_origin_x is None or grid_width is None or pixel_size_x is None:
        normal_lon_east = swath_lon_east if swath_lon_east > swath_lon_west else swath_lon_east + 360
        lon_range = numpy.linspace(swath_lon_west, normal_lon_east, 15)
        lat_range = numpy.linspace(swath_lat_north, swath_lat_south, 15)

        ### Create a matrix of projection points to find the bounding box of the grid ###
        # Test the left, right, ul2br diagonal, ur2bl diagonal, top, bottom
        # If we are over the north pole then handle strong possibility of data in all longitudes
        if swath_lat_north >= 89.5: bottom_lon_range = numpy.linspace(-180, 180, 15)
        else: bottom_lon_range = lon_range
        # If we are over the north pole then handle strong possibility of data in all longitudes
        if swath_lat_south <= -89.5: top_lon_range = numpy.linspace(-180, 180, 15)
        else: top_lon_range = lon_range

        lon_test = numpy.array([ [swath_lon_west]*15, [swath_lon_east]*15, lon_range, lon_range,       top_lon_range, bottom_lon_range ])
        lat_test = numpy.array([ lat_range,           lat_range,           lat_range, lat_range[::-1], [swath_lat_north]*15, [swath_lat_south]*15 ])
        x_test,y_test = _transform_array(tformer, lon_test, lat_test, proj_circum, stradles_anti=stradles_anti)

    # Calculate the best corners of the data
    if grid_width is None or pixel_size_x is None:
        # only used if calculate grid/pixel size
        corner_x = x_test.max()
        corner_y = y_test.min()
        log.debug("Grid Corners: %f,%f" % (corner_x,corner_y))

    # Calculate the best origin of the data if they weren't already specified
    if grid_origin_x is None:
        # We already have 
        grid_origin_x = x_test.min()
        grid_origin_y = y_test.max()
        log.debug("Grid Origin: %f,%f" % (grid_origin_x,grid_origin_y))

    # Calculate the rest of the grid specification (for dynamic grids)
    if grid_width is None:
        # Calculate grid size
        grid_width = math.ceil((corner_x - grid_origin_x) / pixel_size_x)
        grid_height = math.ceil((corner_y - grid_origin_y) / pixel_size_y)
        log.debug("Grid width/height (%d, %d)" % (grid_width,grid_height))
        if grid_width < 5 or grid_height < 5:
            msg = "No data fit in the grid at origin (%f, %f)" % (grid_origin_x, grid_origin_y)
            log.error(msg)
            raise ValueError(msg)
    elif pixel_size_x is None:
        # Calculate pixel size
        pixel_size_x = (corner_x - grid_origin_x) / float(grid_width)
        pixel_size_y = (corner_y - grid_origin_y) / float(grid_height)
        log.debug("Grid pixel size (%f, %f)" % (pixel_size_x,pixel_size_y))
        
    good_mask = numpy.zeros(lat_arr.shape[1], dtype=numpy.bool)
    log.debug("Real upper-left corner (%f,%f)" % tformer(grid_origin_x, grid_origin_y, inverse=True))
    log.debug("Real lower-right corner (%f,%f)" % tformer(grid_origin_x+pixel_size_x*grid_width, grid_origin_y+pixel_size_y*grid_height, inverse=True))

    ### Handle special cases for certain projections ###
    ll2cr_info = {}
    ll2cr_info["grid_origin_x"] = grid_origin_x
    ll2cr_info["grid_origin_y"] = grid_origin_y
    ll2cr_info["grid_width"] = grid_width
    ll2cr_info["grid_height"] = grid_height
    ll2cr_info["pixel_size_x"] = pixel_size_x
    ll2cr_info["pixel_size_y"] = pixel_size_y
    ll2cr_info["rows_filename"] = rows_fn
    ll2cr_info["cols_filename"] = cols_fn

    # Do calculations for each row in the source file
    # Go per row to save on memory, disk load
    for idx in range(lon_arr.shape[0]):
        x_tmp,y_tmp = _transform_array(tformer, lon_arr[idx], lat_arr[idx], proj_circum, stradles_anti=stradles_anti)
        x_tmp = x_tmp.copy()
        y_tmp = y_tmp.copy()
        numpy.subtract(x_tmp, grid_origin_x, x_tmp)
        numpy.divide(x_tmp, pixel_size_x, x_tmp)
        numpy.subtract(y_tmp, grid_origin_y, y_tmp)
        numpy.divide(y_tmp, pixel_size_y, y_tmp)

        # good_mask here is True for good values
        good_mask[:] =  ~( ((lon_arr[idx] == lon_fill_in) | (lat_arr[idx] == lon_fill_in)) )
        cols_arr[idx,good_mask] = x_tmp[good_mask]
        cols_arr[idx,~good_mask] = fill_out
        rows_arr[idx,good_mask] = y_tmp[good_mask]
        rows_arr[idx,~good_mask] = fill_out

    log.info("row and column calculation complete")

    return ll2cr_info

def ll2cr_fbf(lon_fbf, lat_fbf, *args, **kwargs):
    """Wrapper around the python version of ll2cr that accepts numpy arrays
    as arguments.  This function will load the numpy arrays from flat binary
    files.
    """
    W = Workspace('.')
    lon_arr = getattr(W, lon_fbf.split('.')[0])
    lat_arr = getattr(W, lat_fbf.split('.')[0])
    return ll2cr(lon_arr, lat_arr, *args, **kwargs)

def main():
    from optparse import OptionParser
    usage = """
    %prog [options] lon_file lat_file "quoted proj4 string (can be 'epsg:####')"

    Resolutions
    ===========

    If 'pixel_size_x' is not specified it will be computed by the following formula:

        pixel_size_x = abs(in_meters(lat[0,0]) - in_meters(lat[-1,0])) / num_lines

    Same for 'pixel_size_y'.

    Grid Origin
    ===========

    If the latitude and longitude of the grid origin aren't specified, they
    will be calculated by taking the minimum longitude and maximum latitude
    (upper-left corner).  This will increase processing time and memory usage
    significantly as intermediate calculations must stored until the min and
    max can be calculated.

    """
    parser = OptionParser(usage=usage)
    parser.add_option("--pixel_size_x", dest="pixel_size_x", default=None,
            help="Specify the X resolution (pixel size) of the output grid (in meters)")
    parser.add_option("--pixel_size_y", dest="pixel_size_y", default=None,
            help="Specify the Y resolution (pixel size) of the output grid (in meters)")
    parser.add_option("--olon", dest="origin_lon", default=None,
            help="Specify the longitude of the grid's origin (upper-left corner)")
    parser.add_option("--olat", dest="origin_lat", default=None,
            help="Specify the latitude of the grid's origin (upper-left corner)")
    parser.add_option("--width", dest="grid_width", default=None,
            help="Number of pixels wide")
    parser.add_option("--height", dest="grid_height", default=None,
            help="Number of pixels high")
    parser.add_option("--fill-in", dest="fill_in", default=-999.0,
            help="Specify the fill value that incoming latitude and" + \
                    "longitude arrays use to mark invalid data points")
    parser.add_option("--fill-out", dest="fill_out", default=-1e30,
            help="Specify the fill value that outgoing cols and rows" + \
                    "arrays will use to identify bad data")
    options,args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    fill_in = float(options.fill_in)
    fill_out = float(options.fill_out)
    pixel_size_x = options.pixel_size_x and float(options.pixel_size_x)
    pixel_size_y = options.pixel_size_y and float(options.pixel_size_y)
    origin_lon = options.origin_lon
    if origin_lon is not None:
        origin_lon = float(origin_lon)
    origin_lat = options.origin_lat
    if origin_lat is not None:
        origin_lat = float(origin_lat)
    grid_width = options.grid_width and int(options.grid_width)
    grid_height = options.grid_height and int(options.grid_height)

    if len(args) != 3:
        log.error("Expected 3 arguments, got %d" % (len(args),))
        raise ValueError("Expected 3 arguments, got %d" % (len(args),))

    lon_fn = os.path.realpath(args[0])
    lat_fn = os.path.realpath(args[1])
    proj4_str = args[2]

    origin_x = None
    origin_y = None
    if origin_lon is not None and origin_lat is not None:
        p = Proj(proj4_str)
        origin_x, origin_y = p(origin_lon, origin_lat)

    w_dir,lat_var = os.path.split(lat_fn)
    lat_var = lat_var.split(".")[0]
    W = Workspace(w_dir)
    lat_arr = getattr(W, lat_var)
    w_dir,lon_var = os.path.split(lon_fn)
    lon_var = lon_var.split(".")[0]
    W = Workspace(w_dir)
    lon_arr = getattr(W, lon_var)

    from pprint import pprint
    ll2cr_dict = ll2cr(lon_arr, lat_arr, proj4_str,
            pixel_size_x=pixel_size_x, pixel_size_y=pixel_size_y,
            grid_origin_x=origin_x, grid_origin_y=origin_y,
            grid_width=grid_width, grid_height=grid_height,
            fill_in=fill_in, fill_out=fill_out)
    pprint(ll2cr_dict)

if __name__ == "__main__":
    sys.exit(main())

