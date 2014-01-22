#!/usr/bin/env python
# encoding: utf-8
"""Helper script for creating valid grid configuration lines. The user
provides a center longitude and latitude, along with other grid parameters,
and a configuration line is printed to stdout that can be added to a user's
own grid configuration file.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         April 2013
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

    Written by David Hoese    April 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

from .grids import P2GProj

import os
import sys

#grid_name,proj4, proj4_str,width,height,pixel_size_x,pixel_size_y,origin_x,origin_y
CONFIG_LINE_FORMAT = "%(grid_name)s, proj4, %(proj4_str)s, %(width)d, %(height)d, %(pixel_size_x)0.3f, %(pixel_size_y)0.3f, %(origin_x)0.3f, %(origin_y)0.3f"

def determine_projection(center_lon, center_lat):
    """Return the 'best' projection to be used based on the center
    longitude and latitude provided.
    """
    abs_lat = abs(center_lat)
    if abs_lat < 15:
        return "+proj=eqc +datum=WGS84 +ellps=WGS84 +lat_ts=%(center_lat)0.3f +lon_0=%(center_lon)0.3f +units=m +no_defs"
    elif abs_lat < 70:
        return "+proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=%(center_lat)0.3f +lat_1=%(center_lat)0.3f +lon_0=%(center_lon)0.3f +units=m +no_defs"
    else:
        return "+proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=%(center_lat)0.3f +lat_1=%(center_lat)0.3f +lon_0=%(center_lon)0.3f +units=m +no_defs"


def main():
    from argparse import ArgumentParser, SUPPRESS
    description = """Print out valid grid configuration line given grid
parameters. A default projection will be used based on the location of the
grid. A different projection can be specified if desired. The default
projection is referenced at the center lon/lat provided by the user."""
    parser = ArgumentParser(description=description)
    parser.add_argument('grid_name', type=str,
            help="Unique grid name")
    parser.add_argument('center_longitude', type=float,
            help="Decimal longitude value for center of grid (-180 to 180)")
    parser.add_argument('center_latitude', type=float,
            help="Decimal latitude value for center of grid (-90 to 90)")
    parser.add_argument('pixel_size_x', type=float,
            help="""Size of each pixel in the X direction in grid units,
usually meters.""")
    parser.add_argument('pixel_size_y', type=float,
            help="""Size of each pixel in the Y direction in grid units,
meters by default.""")
    parser.add_argument('grid_width', type=int,
            help="Grid width in number of pixels")
    parser.add_argument('grid_height', type=int,
            help="Grid height in number of pixels")
    parser.add_argument('-p', dest="proj_str", default=None,
            help="PROJ.4 projection string to override the default")
    # Don't force Y pixel size to be negative (for expert use only)
    parser.add_argument('--dont-touch-ysize', dest="dont_touch_ysize", action='store_true', default=False,
            help=SUPPRESS)
    args = parser.parse_args()

    grid_name = args.grid_name
    clon = args.center_longitude
    clat = args.center_latitude
    pixel_size_x = args.pixel_size_x
    pixel_size_y = args.pixel_size_y
    if pixel_size_y > 0 and not args.dont_touch_ysize: pixel_size_y *= -1
    grid_width = args.grid_width
    grid_height = args.grid_height

    if clon < -180 or clon > 180:
        print "ERROR: Center longitude must be between -180 and 180 degrees"
        return -1
    if clat < -90 or clat > 90:
        print "ERROR: Center latitude must be between -90 and 90 degrees"
        return -1

    proj_str = args.proj_str or determine_projection(clon, clat)
    proj_str = proj_str % {"center_lon":clon, "center_lat":clat}
    p = P2GProj(proj_str)
    origin_x = grid_width / 2.0 * pixel_size_x * -1
    origin_y = grid_height / 2.0 * pixel_size_y * -1

    valid_config_line = CONFIG_LINE_FORMAT % {
            "grid_name" : grid_name,
            "proj4_str" : proj_str,
            "origin_x" : origin_x,
            "origin_y" : origin_y,
            "pixel_size_x" : pixel_size_x,
            "pixel_size_y" : pixel_size_y,
            "width" : grid_width,
            "height" : grid_height,
            }
    print valid_config_line

if __name__ == "__main__":
    sys.exit(main())

