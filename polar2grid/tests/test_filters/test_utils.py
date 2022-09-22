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


@pytest.mark.parametrize(
    ("geom_func", "exp_func"),
    [
        (_swath_def_nan_rows, _exp_boundary_nan_rows),
        (_swath_def_antimeridian_nan_rows, _exp_boundary_antimeridian_nan_rows),
    ],
)
def test_boundary_for_area(geom_func, exp_func):
    geom_obj = geom_func()
    exp_boundary = exp_func()

    with dask.config.set(scheduler=CustomScheduler(1)):
        boundary = boundary_for_area(geom_obj)

    np.testing.assert_allclose(boundary.contour()[0], exp_boundary.contour()[0])
    np.testing.assert_allclose(boundary.contour()[1], exp_boundary.contour()[1])
