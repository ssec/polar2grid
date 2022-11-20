#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2022 Space Science and Engineering Center (SSEC),
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
"""Tests for filtering utilities."""

import dask
import dask.array as da
import numpy as np
import pytest
from pyresample import SwathDefinition
from pyresample.boundary import AreaBoundary
from satpy.tests.utils import CustomScheduler

from polar2grid.filters._utils import boundary_for_area

from .._fixture_utils import generate_lonlat_data


def _swath_def_nan_rows() -> SwathDefinition:
    lons, lats = generate_lonlat_data((200, 100))
    lons[:9, :] = np.nan
    lats[:9, :] = np.nan
    lons_da = da.from_array(lons)
    lats_da = da.from_array(lats)
    swath_def = SwathDefinition(
        lons_da,
        lats_da,
    )
    return swath_def


def _swath_def_antimeridian_nan_rows() -> SwathDefinition:
    lons, lats = generate_lonlat_data((200, 100))
    lons = lons - 115.0
    lons[lons <= -180] += 360
    lons[:9, :] = np.nan
    lats[:9, :] = np.nan
    lons_da = da.from_array(lons)
    lats_da = da.from_array(lats)
    swath_def = SwathDefinition(
        lons_da,
        lats_da,
    )
    return swath_def


def _swath_def_nans_in_right_column() -> SwathDefinition:
    lons, lats = generate_lonlat_data((200, 100))
    lons[:100, -1] = np.nan
    lons_da = da.from_array(lons)
    lats_da = da.from_array(lats)
    swath_def = SwathDefinition(
        lons_da,
        lats_da,
    )
    return swath_def


def _exp_boundary_nan_rows():
    exp_boundary = AreaBoundary(
        ([-71.5, -40.907036], [60.5, 60.5]),
        ([-40.907036, -40.907036], [60.5, 23.721106]),
        ([-40.907036, -71.5], [23.721106, 23.721106]),
        ([-71.5, -40.907036], [23.721106, 60.5]),
    )
    return exp_boundary


def _exp_boundary_antimeridian_nan_rows():
    exp_boundary = AreaBoundary(
        ([-71.5 - 115.0 + 360.0, -40.907036 - 115.0], [60.5, 60.5]),
        ([-40.907036 - 115.0, -40.907036 - 115.0], [60.5, 23.721106]),
        ([-40.907036 - 115.0, -71.5 - 115.0 + 360.0], [23.721106, 23.721106]),
        ([-71.5 - 115.0 + 360.0, -40.907036 - 115.0 + 360.0], [23.721106, 60.5]),
    )
    return exp_boundary


def _exp_boundary_nans_in_right_column():
    exp_boundary = AreaBoundary(
        (
            [
                -40.5,
                -41.227272,
                -43.045456,
                -44.863636,
                -46.68182,
                -48.5,
                -50.31818,
                -52.136364,
                -53.954544,
                -55.772728,
                -57.590908,
                -58.31818,
            ],
            [
                22.5,
                22.70202,
                23.207071,
                23.712122,
                24.217173,
                24.722221,
                25.227272,
                25.732323,
                26.237373,
                26.742424,
                27.247475,
                27.449495,
            ],
        ),
        (
            [
                -65.03266,
                -65.68593,
                -66.339195,
                -66.99246,
                -67.64573,
                -68.298996,
                -68.95226,
                -69.60553,
                -70.2588,
                -70.91206,
                -71.5,
            ],
            [
                44.082916,
                45.741207,
                47.399498,
                49.05779,
                50.71608,
                52.37437,
                54.03266,
                55.690956,
                57.349247,
                59.007538,
                60.5,
            ],
        ),
        (
            [
                -71.5,
                -69.27778,
                -67.05556,
                -64.833336,
                -62.61111,
                -60.38889,
                -58.166668,
                -55.944443,
                -53.72222,
                -51.5,
                -49.5,
            ],
            [60.5, 59.38889, 58.27778, 57.166668, 56.055557, 54.944443, 53.833332, 52.72222, 51.61111, 50.5, 49.5],
        ),
        (
            [
                -49.5,
                -49.047737,
                -48.595478,
                -48.143215,
                -47.690956,
                -47.238693,
                -46.78643,
                -46.33417,
                -45.88191,
                -45.42965,
                -44.977386,
                -44.525127,
                -44.072865,
                -43.6206,
                -43.168343,
                -42.71608,
                -42.26382,
                -41.811558,
                -41.359295,
                -40.907036,
                -40.5,
            ],
            [
                49.5,
                48.143215,
                46.78643,
                45.42965,
                44.072865,
                42.71608,
                41.359295,
                40.002514,
                38.64573,
                37.288944,
                35.93216,
                34.57538,
                33.218594,
                31.861809,
                30.505026,
                29.148241,
                27.791458,
                26.434673,
                25.07789,
                23.721106,
                22.5,
            ],
        ),
    )
    return exp_boundary


@pytest.mark.parametrize(
    ("geom_func", "exp_func"),
    [
        (_swath_def_nan_rows, _exp_boundary_nan_rows),
        (_swath_def_antimeridian_nan_rows, _exp_boundary_antimeridian_nan_rows),
        (_swath_def_nans_in_right_column, _exp_boundary_nans_in_right_column),
    ],
)
def test_boundary_for_area(geom_func, exp_func):
    geom_obj = geom_func()
    exp_boundary = exp_func()

    with dask.config.set(scheduler=CustomScheduler(1)):
        boundary = boundary_for_area(geom_obj)

    np.testing.assert_allclose(boundary.contour()[0], exp_boundary.contour()[0])
    np.testing.assert_allclose(boundary.contour()[1], exp_boundary.contour()[1])
