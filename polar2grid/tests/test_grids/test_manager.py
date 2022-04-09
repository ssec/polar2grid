#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2015-2021 Space Science and Engineering Center (SSEC),
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
"""Test grid manager."""

from pyresample import AreaDefinition, DynamicAreaDefinition

from polar2grid.grids import GridManager


def test_grid_manager_basic(builtin_test_grids_conf, viirs_sdr_i_swath_def):
    """Test basic parsing of .conf files."""
    gm = GridManager(*builtin_test_grids_conf)
    for grid_name in gm.grid_information:
        grid_def = gm.get_grid_definition(grid_name)
        area_def = grid_def.to_satpy_area()
        assert isinstance(area_def, (AreaDefinition, DynamicAreaDefinition))
        if isinstance(area_def, DynamicAreaDefinition):
            new_area_def = area_def.freeze(viirs_sdr_i_swath_def)
            assert new_area_def.shape[0] > 0
            assert new_area_def.shape[1] > 0
            assert new_area_def.area_extent[0] < new_area_def.area_extent[2]
            assert new_area_def.area_extent[1] < new_area_def.area_extent[3]
