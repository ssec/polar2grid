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
"""Tests day/night filtering."""

import pytest
from satpy import Scene

from polar2grid.filters.day_night import DayCoverageFilter, NightCoverageFilter


@pytest.mark.parametrize(
    "filter_cls",
    [DayCoverageFilter, NightCoverageFilter],
)
@pytest.mark.parametrize(
    "criteria",
    ["default", None, {}],
)
def test_daynight_filter_no_filter_check_cases(filter_cls, criteria, viirs_sdr_i01_data_array):
    scn = Scene()
    scn["I01"] = viirs_sdr_i01_data_array

    if criteria == "default":
        filter = filter_cls()
    else:
        filter = filter_cls(criteria)
    new_scn = filter.filter_scene(scn)
    assert new_scn is not None
    assert new_scn is not scn
    assert "I01" in new_scn


@pytest.mark.parametrize(
    ("filter_cls", "kwargs"),
    [
        (DayCoverageFilter, {"day_fraction": 0.95}),
        (NightCoverageFilter, {"night_fraction": 0.5}),
    ],
)
def test_daynight_filter_filter_cases(filter_cls, kwargs, viirs_sdr_i01_data_array):
    scn = Scene()
    scn["I01"] = viirs_sdr_i01_data_array  # calculates to ~0.8 day

    criteria = {"standard_name": ["toa_bidirectional_reflectance"]}
    filter = filter_cls(criteria, **kwargs)
    new_scn = filter.filter_scene(scn)
    assert new_scn is None  # all filtered
    assert "I01" in scn
