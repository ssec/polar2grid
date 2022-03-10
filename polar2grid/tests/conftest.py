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
"""Test initialization and fixtures."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import dask.array as da
import numpy as np
import pytest
import xarray as xr
from numpy.typing import DTypeLike, NDArray
from pyresample.geometry import AreaDefinition, SwathDefinition
from satpy import Scene

PKG_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
VIIRS_I_CHUNKS = (32 * 3, 6400)
START_TIME = datetime(2021, 1, 1, 12, 0, 0)


def pytest_configure(config):
    from polar2grid.utils.config import add_polar2grid_config_paths

    add_polar2grid_config_paths()


# Utilities #


@pytest.fixture
def chtmpdir(tmp_path: Path):
    lwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(lwd)


# Config Files #


@pytest.fixture(scope="session")
def builtin_grids_yaml() -> list[str]:
    return [os.path.join(PKG_ROOT, "grids", "grids.yaml")]


@pytest.fixture(scope="session")
def builtin_test_grids_conf() -> list[str]:
    return [os.path.join(PKG_ROOT, "tests", "etc", "grids.conf")]


# Geometries #


def _generate_lonlat_data(shape: tuple[int, int], dtype: DTypeLike = np.float32) -> tuple[NDArray, NDArray]:
    lat = np.repeat(np.linspace(25.0, 55.0, shape[0])[:, None], shape[1], 1)
    lat *= np.linspace(0.9, 1.1, shape[1])
    lon = np.repeat(np.linspace(-45.0, -65.0, shape[1])[None, :], shape[0], 0)
    lon *= np.linspace(0.9, 1.1, shape[0])[:, None]
    return lon.astype(dtype), lat.astype(dtype)


@pytest.fixture(scope="session")
def viirs_sdr_i_swath_def() -> SwathDefinition:
    lons, lats = _generate_lonlat_data((1536, 6400))
    lons_data_arr = xr.DataArray(
        da.from_array(lons, chunks=VIIRS_I_CHUNKS),
        dims=("y", "x"),
        attrs={
            "rows_per_scan": 32,
            "platform_name": "npp",
            "sensor": "viirs",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 371,
            "reader": "viirs_sdr",
        },
    )
    lats_data_arr = xr.DataArray(
        da.from_array(lats, chunks=VIIRS_I_CHUNKS),
        dims=("y", "x"),
        attrs={
            "rows_per_scan": 32,
            "platform_name": "npp",
            "sensor": "viirs",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 371,
            "reader": "viirs_sdr",
        },
    )
    return SwathDefinition(lons_data_arr, lats_data_arr)


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


# Data Arrays #


@pytest.fixture
def viirs_sdr_i01_data_array(viirs_sdr_i_swath_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros((1536, 6400), dtype=np.float32),
        dims=("y", "x"),
        attrs={
            "area": viirs_sdr_i_swath_def,
            "rows_per_scan": 32,
            "platform_name": "npp",
            "sensor": "viirs",
            "name": "I01",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 371,
            "reader": "viirs_sdr",
        },
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


# Scenes #


@pytest.fixture
def viirs_sdr_i01_scene(viirs_sdr_i01_data_array) -> Scene:
    scn = Scene()
    scn["I01"] = viirs_sdr_i01_data_array
    return scn


@pytest.fixture
def abi_l1b_c01_scene(abi_l1b_c01_data_array) -> Scene:
    scn = Scene()
    scn["C01"] = abi_l1b_c01_data_array
    return scn


@pytest.fixture
def abi_l1b_airmass_scene(abi_l1b_airmass_data_array) -> Scene:
    scn = Scene()
    scn["airmass"] = abi_l1b_airmass_data_array
    return scn
