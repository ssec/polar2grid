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

import pytest
from polar2grid.resample._resample_scene import resample_scene
from satpy import Scene


def test_viirs_sdr_i01_resample(viirs_sdr_i01_scene, builtin_grids_conf):
    scenes_to_save = resample_scene(
        viirs_sdr_i01_scene,
        ["wgs84_fit"],
        [builtin_grids_conf],
        None,
    )
    assert len(scenes_to_save) == 1
    scene, data_ids_set = scenes_to_save[0]
    assert isinstance(scene, Scene)
    assert len(data_ids_set) == 1
    assert list(data_ids_set)[0]["name"] == "I01"
