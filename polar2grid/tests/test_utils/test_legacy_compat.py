#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2021 Space Science and Engineering Center (SSEC),
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
"""Tests for legacy handling utilities."""

from __future__ import annotations

import logging

import pytest

from polar2grid.utils.legacy_compat import convert_p2g_pattern_to_satpy


@pytest.mark.parametrize(
    ("input_str", "exp_str", "num_exp_warnings"),
    [
        ("{p2g_name}_{start_time:%Y%m%d_%H%M%S}.tif", "{p2g_name}_{start_time:%Y%m%d_%H%M%S}.tif", 0),
        (
            "{satellite}_{instrument}_{product_name}_{begin_time}.tif",
            "{platform_name}_{sensor}_{p2g_name}_{start_time:%Y%m%d_%H%M%S}.tif",
            4,
        ),
        (
            "{grid_name}_{product_name}_{begin_time_HHMM}_{end_time_HHMM}.tif",
            "{area.area_id}_{p2g_name}_{start_time:%H%M}_{end_time:%H%M}.tif",
            4,
        ),
    ],
)
def test_pattern_formatting(input_str, exp_str, num_exp_warnings, caplog):
    with caplog.at_level(logging.WARNING):
        new_str = convert_p2g_pattern_to_satpy(input_str)
    assert new_str == exp_str
    legacy_warns = [record for record in caplog.records if "to avoid this warning" in record.message]
    assert len(legacy_warns) == num_exp_warnings
