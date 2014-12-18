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

from polar2grid.proj import Proj
import numpy

import logging
import math

LOG = logging.getLogger(__name__)


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
        LOG.debug("Point crosses the anti-meridian, adding %f" % (proj_circum,))
        x += proj_circum
    return x,y

def _transform_array(tformer, lon, lat, proj_circum, stradles_anti=False):
    """See _transform_point above
    """
    x,y = tformer(lon, lat)
    if stradles_anti:
        x[x < 0] += proj_circum
    return x,y


def projection_circumference(p):
    """Return the projection circumference if the projection is cylindrical. None is returned otherwise.

    Projections that are not cylindrical and centered on the globes axis can not easily have data cross the antimeridian
    of the projection.
    """
    lon0, lat0 = p(0, 0, inverse=True)
    lon1 = lon0 + 180.0
    lat1 = lat0 + 5.0
    x0, y0 = p(lon0, lat0)  # should result in zero or near zero
    x1, y1 = p(lon1, lat0)
    x2, y2 = p(lon1, lat1)
    if y0 != y1 or x1 != x2:
        return None
    return abs(x1 - x0) * 2


def mask_helper(arr, fill):
    if numpy.isnan(fill):
        return numpy.isnan(arr)
    else:
        return arr == fill


def ll2cr(lon_arr, lat_arr, grid_info, fill_in=numpy.nan, fill_out=None, cols_out=None, rows_out=None):
    """Project longitude and latitude points to column rows in the specified grid.

    :param lon_arr: Numpy array of longitude floats
    :param lat_arr: Numpy array of latitude floats
    :param grid_info: dictionary of grid information (see below)
    :param fill_in: (optional) Fill value for input longitude and latitude arrays (default: NaN)
    :param fill_out: (optional) Fill value for output column and row array (default: `fill_in`)
    :returns: tuple(points_in_grid, cols_out, rows_out)

    The provided grid info must have the following parameters (optional grids mean dynamic):

        - proj4_definition
        - cell_width
        - cell_height
        - width (optional/None)
        - height (optional/None)
        - origin_x (optional/None)
        - origin_y (optional/None)

    Steps taken in this function:

        1. Convert (lon, lat) points to (X, Y) points in the projection space
        2. If grid is missing some parameters (dynamic grid), then fill them in
        3. Convert (X, Y) points to (column, row) points in the grid space
    """
    p = Proj(grid_info["proj4_definition"])
    cw = grid_info["cell_width"]
    ch = grid_info["cell_height"]
    w = grid_info.get("width", None)
    h = grid_info.get("height", None)
    ox = grid_info.get("origin_x", None)
    oy = grid_info.get("origin_y", None)
    is_static = None not in [w, h, ox, oy]
    proj_circum = projection_circumference(p)

    if rows_out is None:
        rows_out = numpy.zeros_like(lat_arr)
    if cols_out is None:
        cols_out = numpy.zeros_like(lon_arr)
    if fill_out is None:
        fill_out = fill_in

    mask = ~(mask_helper(lon_arr, fill_in) | mask_helper(lat_arr, fill_in))
    x, y = p(lon_arr, lat_arr)
    mask = mask & (x < 1e30) & (y < 1e30)
    # need temporary storage because x and y are might NOT be copies (latlong projections)
    cols_out[:] = numpy.where(mask, x, fill_out)
    rows_out[:] = numpy.where(mask, y, fill_out)
    # we only need the good Xs and Ys from here on out
    x = cols_out[mask]
    y = rows_out[mask]

    if not is_static:
        # fill in grid parameters
        xmin = numpy.nanmin(x)
        xmax = numpy.nanmax(x)
        ymin = numpy.nanmin(y)
        ymax = numpy.nanmax(y)
        # if the data seems to be covering more than 75% of the projection space then the antimeridian is being crossed
        # if proj_circum is None then we can't simply wrap the data around projection, the grid will probably be large
        LOG.debug("Projection circumference: %f", proj_circum)
        if proj_circum is not None and xmax - xmin >= proj_circum * .75:
            old_xmin = xmin
            old_xmax = xmax
            x[x < 0] += proj_circum
            xmin = numpy.nanmin(x)
            xmax = numpy.nanmax(x)
            print proj_circum
            LOG.debug("Data seems to cross the antimeridian: old_xmin=%f; old_xmax=%f; xmin=%f; xmax=%f", old_xmin, old_xmax, xmin, xmax)
        LOG.debug("Xmin=%f; Xmax=%f; Ymin=%f; Ymax=%f", xmin, xmax, ymin, ymax)

        if ox is None:
            # upper-left corner
            ox = grid_info["origin_x"] = float(xmin)
            oy = grid_info["origin_y"] = float(ymax)
            LOG.debug("Dynamic grid origin (%f, %f)", xmin, ymax)
        if w is None:
            w = grid_info["width"] = int(abs((xmax - xmin) / cw))
            h = grid_info["height"] = int(abs((ymax - ymin) / ch))
            LOG.debug("Dynamic grid width and height (%d x %d) with cell width and height (%f x %f)", w, h, cw, ch)

    good_cols = (x - ox) / cw
    good_rows = (y - oy) / ch
    cols_out[mask] = good_cols
    rows_out[mask] = good_rows

    points_in_grid = numpy.count_nonzero((good_cols >= -1) & (good_cols <= w + 1) & (good_rows >= -1) & (good_rows <= h + 1))

    return points_in_grid, cols_out, rows_out


def ll2cr_old(lon_arr, lat_arr, proj4_str,
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
        rows_out=None,
        cols_out=None,
        prefix="ll2cr_"):
    """Similar to GDAL, y pixel resolution should be negative for downward
    images.

    origin_lon,origin_lat are the grids origins
    """
    lon_fill_in = lon_fill_in or fill_in or -999.0
    lat_fill_in = lat_fill_in or lon_fill_in

    ### Parameter check ###

    if lat_arr.shape != lon_arr.shape:
        LOG.error("Longitude and latitude arrays must be the same shape (%r vs %r)" % (lat_arr.shape, lon_arr.shape))
        raise ValueError("Longitude and latitude arrays must be the same shape (%r vs %r)" % (lat_arr.shape, lon_arr.shape))

    if (pixel_size_x is None and pixel_size_y is not None) or \
            (pixel_size_y is None and pixel_size_x is not None):
        LOG.error("pixel_size_x and pixel_size_y must both be specified or neither")
        raise ValueError("pixel_size_x and pixel_size_y must both be specified or neither")

    if (grid_width is None and grid_height is not None) or \
            (grid_width is not None and grid_height is None):
        LOG.error("grid_width and grid_height must both be specified or neither")
        raise ValueError("grid_width and grid_height must both be specified or neither")

    if (grid_origin_x is None and grid_origin_y is not None) or \
            (grid_origin_y is None and grid_origin_x is not None):
        LOG.error("grid_origin_x and grid_origin_y must both be specified or neither")
        raise ValueError("grid_origin_x and grid_origin_y must both be specified or neither")

    if pixel_size_x is None and grid_width is None:
        LOG.error("Either pixel size or grid width/height must be specified")
        raise ValueError("Either pixel size or grid width/height must be specified")

    # Handle EPSG codes
    tformer = Proj(proj4_str)

    if dtype is None:
        dtype = lat_arr.dtype

    # Memory map the output filenames
    # cols then rows in FBF filenames
    if rows_out is None:
        rows_out = numpy.zeros_like(lat_arr)
    if cols_out is None:
        cols_out = numpy.zeros_like(lon_arr)

    good_mask = (lon_arr != lon_fill_in) & (lat_arr != lat_fill_in)

    # Calculate west/east south/north boundaries
    # These can be provided by the user to save time
    stradles_180 = False
    if grid_origin_x is None or grid_width is None or pixel_size_x is None:
        if swath_lon_west is None:
            swath_lon_west = float(lon_arr[good_mask].min())
            LOG.debug("Data west longitude: %f" % swath_lon_west)
        if swath_lon_east is None:
            swath_lon_east = float(lon_arr[good_mask].max())
            LOG.debug("Data east longitude: %f" % swath_lon_east)
        if swath_lat_south is None:
            swath_lat_south = float(lat_arr[good_mask].min())
            LOG.debug("Data south latitude: %f" % swath_lat_south)
        if swath_lat_north is None:
            swath_lat_north = float(lat_arr[good_mask].max())
            LOG.debug("Data upper latitude: %f" % swath_lat_north)

        # Are we on the -180/180 boundary
        if swath_lon_west <= -179.0 and swath_lon_east >= 179.0:
            # Obviously assumes data is not smaller than 1 degree longitude wide
            swath_lon_west = float(lon_arr[ good_mask & (lon_arr < 0) ].max())
            LOG.debug("Data west longitude: %f" % swath_lon_west)
            swath_lon_east = float(lon_arr[ good_mask & (lon_arr > 0) ].min())
            LOG.debug("Data east longitude: %f" % swath_lon_east)
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
        LOG.debug("Data crosses the projections anti-meridian")
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
        LOG.debug("Grid Corners: %f,%f" % (corner_x,corner_y))

    # Calculate the best origin of the data if they weren't already specified
    if grid_origin_x is None:
        # We already have 
        grid_origin_x = x_test.min()
        grid_origin_y = y_test.max()
        LOG.debug("Grid Origin: %f,%f" % (grid_origin_x,grid_origin_y))

    # Calculate the rest of the grid specification (for dynamic grids)
    if grid_width is None:
        # Calculate grid size
        grid_width = math.ceil((corner_x - grid_origin_x) / pixel_size_x)
        grid_height = math.ceil((corner_y - grid_origin_y) / pixel_size_y)
        LOG.debug("Grid width/height (%d, %d)" % (grid_width,grid_height))
        if grid_width < 5 or grid_height < 5:
            msg = "No data fit in the grid at origin (%f, %f)" % (grid_origin_x, grid_origin_y)
            LOG.error(msg)
            raise ValueError(msg)
    elif pixel_size_x is None:
        # Calculate pixel size
        pixel_size_x = (corner_x - grid_origin_x) / float(grid_width)
        pixel_size_y = (corner_y - grid_origin_y) / float(grid_height)
        LOG.debug("Grid pixel size (%f, %f)" % (pixel_size_x,pixel_size_y))
        
    good_mask = numpy.zeros(lat_arr.shape[1], dtype=numpy.bool)
    LOG.debug("Real upper-left corner (%f,%f)" % tformer(grid_origin_x, grid_origin_y, inverse=True))
    LOG.debug("Real lower-right corner (%f,%f)" % tformer(grid_origin_x+pixel_size_x*grid_width, grid_origin_y+pixel_size_y*grid_height, inverse=True))

    ### Handle special cases for certain projections ###
    ll2cr_info = {}
    ll2cr_info["grid_origin_x"] = grid_origin_x
    ll2cr_info["grid_origin_y"] = grid_origin_y
    ll2cr_info["grid_width"] = grid_width
    ll2cr_info["grid_height"] = grid_height
    ll2cr_info["pixel_size_x"] = pixel_size_x
    ll2cr_info["pixel_size_y"] = pixel_size_y
    ll2cr_info["rows_array"] = rows_out
    ll2cr_info["cols_array"] = cols_out

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
        cols_out[idx,good_mask] = x_tmp[good_mask]
        cols_out[idx,~good_mask] = fill_out
        rows_out[idx,good_mask] = y_tmp[good_mask]
        rows_out[idx,~good_mask] = fill_out

    LOG.info("row and column calculation complete")

    return ll2cr_info
