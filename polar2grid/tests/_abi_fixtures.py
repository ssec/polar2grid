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
"""Test fixtures representing ABI gridded data."""
from __future__ import annotations

import pytest
import xarray as xr
from dask import array as da
from pyresample.geometry import AreaDefinition
from satpy import Scene
from satpy.tests.utils import make_dataid

from ._fixture_utils import START_TIME, _TestingScene


@pytest.fixture(scope="session")
def goes_east_conus_area_def() -> AreaDefinition:
    return AreaDefinition(
        "goes_east",
        "",
        "",
        "+proj=geos +lon_0=-75.0 +h=35786023.0 +a=6378137.0 +b=6356752.31414 +sweep=x +units=m +no_defs",
        5000,
        3000,
        (-3627271.2913, 1583173.6575, 1382771.9287, 4589199.5895),
    )


@pytest.fixture
def abi_l1b_c01_data_array(goes_east_conus_area_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros((3000, 5000), chunks=4096),
        dims=("y", "x"),
        attrs={
            "area": goes_east_conus_area_def,
            "platform_name": "goes16",
            "sensor": "abi",
            "name": "C01",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "observation_type": "Rad",
            "standard_name": "toa_bidirectional_reflectance",
            "scene_abbr": "C",
            "resolution": 1000,
            "reader": "abi_l1b",
        },
    )


@pytest.fixture
def abi_l1b_airmass_data_array(goes_east_conus_area_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros((3, 3000, 5000), chunks=4096),
        coords={"bands": ["R", "G", "B"]},
        dims=("bands", "y", "x"),
        attrs={
            "area": goes_east_conus_area_def,
            "platform_name": "goes16",
            "sensor": "abi",
            "name": "airmass",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "observation_type": "Rad",
            "standard_name": "airmass",
            "scene_abbr": "C",
        },
    )


@pytest.fixture
def abi_l1b_c01_scene(abi_l1b_c01_data_array) -> Scene:
    c01_id = make_dataid(name="C01", calibration="reflectance", resolution=1000)
    data_arrays = {
        c01_id: abi_l1b_c01_data_array,
    }
    scn = _TestingScene(
        reader="abi_l1b",
        filenames=["/fake/filename"],
        data_array_dict=data_arrays,
        all_dataset_ids=[c01_id],
        available_dataset_ids=[c01_id],
    )
    return scn


@pytest.fixture
def abi_l1b_airmass_scene(abi_l1b_airmass_data_array) -> Scene:
    scn = Scene()
    scn["airmass"] = abi_l1b_airmass_data_array
    return scn
