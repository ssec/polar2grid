#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2013-2018 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
#     input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    March 2015
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Helper script for creating valid grid configuration lines. The user
provides a center longitude and latitude, along with other grid parameters,
and a configuration line is printed to stdout that can be added to a user's
own grid configuration file.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2015 University of Wisconsin SSEC. All rights reserved.
:date:         Mar 2015
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import sys

from polar2grid.core.proj import Proj

#grid_name,proj4, proj4_str,width,height,pixel_size_x,pixel_size_y,origin_x,origin_y
CONFIG_LINE_FORMAT = "%(grid_name)s, proj4, %(proj4_str)s, %(width)d, %(height)d, %(pixel_size_x)0.5f, %(pixel_size_y)0.5f, %(origin_x)s, %(origin_y)s"


def determine_projection(center_lon, center_lat, proj4_str=None):
    """Return the 'best' projection to be used based on the center
    longitude and latitude provided.
    """
    abs_lat = abs(center_lat)
    if proj4_str is None:
        if abs_lat < 15:
            proj4_str = "+proj=eqc +datum=WGS84 +ellps=WGS84 +lat_ts=%(center_lat)0.5f +lon_0=%(center_lon)0.5f +units=m +no_defs"
        elif abs_lat < 70:
            proj4_str =  "+proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=%(center_lat)0.5f +lat_1=%(center_lat)0.5f +lon_0=%(center_lon)0.5f +units=m +no_defs"
        else:
            proj4_str = "+proj=stere +datum=WGS84 +ellps=WGS84 +lat_0=90 +lat_ts=%(center_lat)0.5f +lon_0=%(center_lon)0.5f +units=m"

    proj4_str = proj4_str % dict(center_lon=center_lon, center_lat=center_lat)
    return proj4_str


def get_parser():
    from argparse import ArgumentParser, SUPPRESS
    description = """This script is meant to help those unfamiliar with PROJ.4 and projections
in general. By providing a few grid parameters this script will provide a
grid configuration line that can be added to a user's custom grid
configuration. Based on a center longitude and latitude, the script will
choose an appropriate projection."""
    parser = ArgumentParser(description=description)
    parser.add_argument('grid_name', type=str,
                        help="Unique grid name")
    parser.add_argument('center_longitude', type=float,
                        help="Decimal longitude value for center of grid (-180 to 180)")
    parser.add_argument('center_latitude', type=float,
                        help="Decimal latitude value for center of grid (-90 to 90)")
    parser.add_argument('pixel_size_x', type=float,
                        help="""Size of each pixel in the X direction in grid units,
meters for default projections.""")
    parser.add_argument('pixel_size_y', type=float,
                        help="""Size of each pixel in the Y direction in grid units,
meters for default projections.""")
    parser.add_argument('grid_width', type=int,
                        help="Grid width in number of pixels")
    parser.add_argument('grid_height', type=int,
                        help="Grid height in number of pixels")
    parser.add_argument('-p', dest="proj_str", default=None,
                        help="PROJ.4 projection string to override the default")
    # Don't force Y pixel size to be negative (for expert use only)
    parser.add_argument('--dont-touch-ysize', dest="dont_touch_ysize", action='store_true', default=False,
                        help=SUPPRESS)
    return parser


def main():
    parser = get_parser()
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

    proj_str = determine_projection(clon, clat, args.proj_str)
    p = Proj(proj_str)
    origin_x = p(clon, clat)[0] + (grid_width / 2.0 * pixel_size_x * -1)
    origin_y = p(clon, clat)[1] + (grid_height / 2.0 * pixel_size_y * -1)
    if p.is_latlong():
        # Origin is in degrees so we need to add a unit string to it
        origin_x = "%0.5fdeg" % origin_x
        origin_y = "%0.5fdeg" % origin_y
    else:
        origin_lon, origin_lat = p(origin_x, origin_y, inverse=True)
        origin_x = "%0.5fdeg" % origin_lon
        origin_y = "%0.5fdeg" % origin_lat

    valid_config_line = CONFIG_LINE_FORMAT % {
            "grid_name": grid_name,
            "proj4_str": proj_str,
            "origin_x": origin_x,
            "origin_y": origin_y,
            "pixel_size_x": pixel_size_x,
            "pixel_size_y": pixel_size_y,
            "width": grid_width,
            "height": grid_height,
            }
    print valid_config_line


if __name__ == "__main__":
    sys.exit(main())

