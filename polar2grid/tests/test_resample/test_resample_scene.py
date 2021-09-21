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
"""Tests for resampling a Scene."""

import dask
import pytest
from pytest_lazyfixture import lazy_fixture
from satpy import Scene
from satpy.tests.utils import CustomScheduler

from polar2grid.resample._resample_scene import resample_scene


@pytest.mark.parametrize(
    ("input_scene", "grids", "grid_configs", "resampler", "exp_names", "max_computes", "is_polar2grid"),
    [
        (
            lazy_fixture("viirs_sdr_i01_scene"),
            ["wgs84_fit"],
            lazy_fixture("builtin_grids_yaml"),
            None,
            ["I01"],
            2,
            True,
        ),
        (
            lazy_fixture("viirs_sdr_i01_scene"),
            ["wgs84_fit"],
            [],
            None,
            ["I01"],
            2,
            True,
        ),
        (
            lazy_fixture("viirs_sdr_i01_scene"),
            ["wgs84_fit"],
            ["grids.conf"],
            None,
            ["I01"],
            2,
            True,
        ),
        (
            lazy_fixture("abi_l1b_c01_scene"),
            ["wgs84_fit"],
            lazy_fixture("builtin_grids_yaml"),
            "nearest",
            ["C01"],
            0,
            False,
        ),
        (
            lazy_fixture("abi_l1b_c01_scene"),
            ["MAX"],
            [],
            None,
            ["C01"],
            0,
            False,
        ),
    ],
)
def test_resample_single_result_per_grid(
    input_scene,
    grids,
    grid_configs,
    resampler,
    exp_names,
    max_computes,
    is_polar2grid,
):
    with dask.config.set(scheduler=CustomScheduler(max_computes)):
        scenes_to_save = resample_scene(
            input_scene,
            grids,
            grid_configs,
            resampler,
            is_polar2grid=is_polar2grid,
        )
    assert len(scenes_to_save) == len(grids)
    for scene, data_ids_set in scenes_to_save:
        assert isinstance(scene, Scene)
        assert len(data_ids_set) == len(exp_names)
        id_names = [x["name"] for x in data_ids_set]
        for exp_name in exp_names:
            assert exp_name in id_names
