#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2015 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
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
#     Written by David Hoese    March 2015
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""Test ll2cr and the extension modules.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2015 University of Wisconsin SSEC. All rights reserved.
:date:         Mar 2015
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import sys

import logging
import numpy
import pytest

from polar2grid.remap import ll2cr
from polar2grid.tests.test_remap import create_test_longitude, create_test_latitude

LOG = logging.getLogger(__name__)


dynamic_wgs84 = {
    "grid_name": "test_wgs84_fit",
    "origin_x": None,
    "origin_y": None,
    "width": None,
    "height": None,
    "cell_width": 0.0057,
    "cell_height": -0.0057,
    "proj4_definition": "+proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs",
}

static_lcc = {
    "grid_name": "test_lcc",
    "origin_x": -1950510.636800,
    "origin_y": 4368587.226913,
    "width": 5120,
    "height": 5120,
    "cell_width": 1015.9,
    "cell_height": -1015.9,
    "proj4_definition": "+proj=lcc +a=6371200 +b=6371200 +lat_0=25 +lat_1=25 +lon_0=-95 +units=m +no_defs",
}


class TestLL2CRStatic(object):
    def test_lcc_basic1(self):
        lon_arr = create_test_longitude(-95.0, -75.0, (50, 100))
        lat_arr = create_test_latitude(18.0, 40.0, (50, 100))
        grid_info = static_lcc.copy()
        points_in_grid, lon_res, lat_res = ll2cr.ll2cr(lon_arr, lat_arr, grid_info)
        assert points_in_grid == lon_arr.size, "all these test points should fall in this grid"
        assert lon_arr is lon_res
        assert lat_arr is lat_res

    def test_lcc_fail1(self):
        lon_arr = create_test_longitude(-15.0, 15.0, (50, 100))
        lat_arr = create_test_latitude(18.0, 40.0, (50, 100))
        grid_info = static_lcc.copy()
        points_in_grid, lon_res, lat_res = ll2cr.ll2cr(lon_arr, lat_arr, grid_info)
        assert points_in_grid == 0, "none of these test points should fall in this grid"
        assert lon_arr is lon_res
        assert lat_arr is lat_res


class TestLL2CRDynamic(object):
    def test_latlong_basic1(self):
        lon_arr = create_test_longitude(-95.0, -75.0, (50, 100))
        lat_arr = create_test_latitude(15.0, 30.0, (50, 100))
        grid_info = dynamic_wgs84.copy()
        points_in_grid, lon_res, lat_res = ll2cr.ll2cr(lon_arr, lat_arr, grid_info)
        assert points_in_grid == lon_arr.size, "all points should be contained in a dynamic grid"
        assert lon_arr is lon_res
        assert lat_arr is lat_res
        assert lon_arr[0, 0] == 0, "ll2cr returned the wrong result for a dynamic latlong grid"
        assert lat_arr[-1, 0] == 0, "ll2cr returned the wrong result for a dynamic latlong grid"

    def test_latlong_basic2(self):
        lon_arr = create_test_longitude(-95.0, -75.0, (50, 100), twist_factor=0.6)
        lat_arr = create_test_latitude(15.0, 30.0, (50, 100), twist_factor=-0.1)
        grid_info = dynamic_wgs84.copy()
        points_in_grid, lon_res, lat_res = ll2cr.ll2cr(lon_arr, lat_arr, grid_info)
        assert points_in_grid == lon_arr.size, "all points should be contained in a dynamic grid"
        assert lon_arr is lon_res
        assert lat_arr is lat_res
        assert lon_arr[0, 0] == 0, "ll2cr returned the wrong result for a dynamic latlong grid"
        assert lat_arr[-1, 0] == 0, "ll2cr returned the wrong result for a dynamic latlong grid"

    def test_latlong_dateline1(self):
        lon_arr = create_test_longitude(165.0, -165.0, (50, 100), twist_factor=0.6)
        lat_arr = create_test_latitude(15.0, 30.0, (50, 100), twist_factor=-0.1)
        grid_info = dynamic_wgs84.copy()
        points_in_grid, lon_res, lat_res = ll2cr.ll2cr(lon_arr, lat_arr, grid_info)
        assert points_in_grid == lon_arr.size, "all points should be contained in a dynamic grid"
        assert lon_arr is lon_res
        assert lat_arr is lat_res
        assert lon_arr[0, 0] == 0, "ll2cr returned the wrong result for a dynamic latlong grid over the dateline"
        assert lat_arr[-1, 0] == 0, "ll2cr returned the wrong result for a dynamic latlong grid over the dateline"
        assert numpy.all(numpy.diff(lon_arr[0]) >= 0), "ll2cr didn't return monotonic columns over the dateline"


def main():
    import os
    return pytest.main([os.path.dirname(os.path.realpath(__file__))])


if __name__ == "__main__":
    sys.exit(main())