#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2013 Space Science and Engineering Center (SSEC),
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
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    March 2013
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Script for converting lon/lat decimal values to X/Y values of the grid provided.
This script mimics the `proj` binary that comes with the PROJ.4 library, but
handles any projection string that `pyproj` can handle (like 'latlong' which the
`proj` binary does not handle).

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Mar 2013
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import sys

try:
    from pyproj import Proj
except ImportError:
    # This module is loaded by meta.py which could be all a user needs so we shouldn't fail if they don't have pyproj
    import warnings
    warnings.warn("Package 'pyproj' could not be imported. Some functionality will be missing")
    Proj = object


class Proj(Proj):
    def __call__(self, data1, data2, **kwargs):
        if self.is_latlong():
            return data1, data2

        return super(Proj, self).__call__(data1, data2, **kwargs)


def get_parser():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Convert latitude/longitude coordinates to X/Y values.")
    parser.add_argument("-i", "--inverse", dest="inv", action="store_true", default=False,
                        help="Convert X/Y values to latitude/longitude coordinates")
    parser.add_argument("proj4_str",
                        help="PROJ.4 projection string (in quotes)")
    parser.add_argument("lon_point", type=float,
                        help="Longitude of the point to be converted (single value only)")
    parser.add_argument("lat_point", type=float,
                        help="Latitude of the point to be converted (single value only)")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    p = Proj(args.proj4_str)
    x, y = p(args.lon_point, args.lat_point, inverse=args.inv)
    print(x, y)

if __name__ == "__main__":
    sys.exit(main())

