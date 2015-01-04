#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
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
#     Written by David Hoese    December 2014
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""Elliptical weighted averaging (EWA) resampling algorithm

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import os
import sys
import logging

import _fornav
import numpy

LOG = logging.getLogger(__name__)


def fornav(cols_array, rows_array, rows_per_scan, input_arrays, cr_fill=numpy.nan, input_fill=numpy.nan,
           output_arrays=None, output_fill=None, grid_cols=None, grid_rows=None,
           weight_count=10000, weight_min=0.01, weight_distance_max=1.0, weight_delta_max=10.0,
           weight_sum_min=-1.0, maximum_weight_mode=False):
    input_arrays = tuple(input_arrays)
    include_output = False
    if output_arrays is None:
        if grid_cols is None or grid_rows is None:
            raise ValueError("Must either specify grid_cols and grid_rows when output_arrays is not specified")
        output_arrays = tuple(numpy.empty((grid_rows, grid_cols), dtype=ia.dtype) for ia in input_arrays)
        include_output = True
    if output_fill is None:
        output_fill = input_fill

    got_points = _fornav.fornav_wrapper(cols_array, rows_array, input_arrays, output_arrays,
                          cr_fill, input_fill, output_fill, rows_per_scan,
                          weight_count=weight_count, weight_min=weight_min, weight_distance_max=weight_distance_max,
                          weight_delta_max=weight_delta_max, weight_sum_min=weight_sum_min,
                          maximum_weight_mode=maximum_weight_mode)
    if include_output:
        return got_points, output_arrays
    else:
        return got_points


def main():
    pass


if __name__ == "__main__":
    sys.exit(main())