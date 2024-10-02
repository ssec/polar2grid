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
"""Test fixtures representing AVHRR swath data."""

from __future__ import annotations

import dask.array as da
import numpy as np
import pytest
import xarray as xr
from pyresample import SwathDefinition
from satpy import Scene
from satpy.tests.utils import make_dataid

from ._fixture_utils import START_TIME, _TestingScene, generate_lonlat_data

AVHRR_SHAPE = (2361, 2048)
AVHRR_CHUNKS = AVHRR_SHAPE

AVHRR_IDS = [
    make_dataid(
        name="1",
        wavelength=(0.58, 0.63, 0.68),
        resolution=1050,
        calibration="reflectance",
    ),
    make_dataid(
        name="2",
        wavelength=(0.725, 0.8625, 1.0),
        resolution=1050,
        calibration="reflectance",
    ),
    make_dataid(
        name="3a",
        wavelength=(1.58, 1.61, 1.64),
        resolution=1050,
        calibration="reflectance",
    ),
    make_dataid(
        name="3b",
        wavelength=(3.55, 3.74, 3.93),
        resolution=1050,
        calibration="brightness_temperature",
    ),
    make_dataid(
        name="4",
        wavelength=(10.3, 10.8, 11.3),
        resolution=1050,
        calibration="brightness_temperature",
    ),
    make_dataid(
        name="5",
        wavelength=(11.5, 12.0, 12.5),
        resolution=1050,
        calibration="brightness_temperature",
    ),
]


@pytest.fixture(scope="session")
def avhrr_l1b_swath_def() -> SwathDefinition:
    lons, lats = generate_lonlat_data(AVHRR_SHAPE)
    lons_data_arr = xr.DataArray(
        da.from_array(lons, chunks=AVHRR_CHUNKS),
        dims=("y", "x"),
        attrs={
            "platform_name": "noaa19",
            "sensor": "avhrr-3",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 1050,
            "reader": "avhrr_l1b_aapp",
        },
    )
    lats_data_arr = xr.DataArray(
        da.from_array(lats, chunks=AVHRR_CHUNKS),
        dims=("y", "x"),
        attrs={
            "platform_name": "noaa19",
            "sensor": "avhrr-3",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 1050,
            "reader": "avhrr_l1b_aapp",
        },
    )
    return SwathDefinition(lons_data_arr, lats_data_arr)


@pytest.fixture
def avhrr_l1b_1_data_array(avhrr_l1b_swath_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros(AVHRR_SHAPE, dtype=np.float32),
        dims=("y", "x"),
        attrs={
            "area": avhrr_l1b_swath_def,
            "platform_name": "noaa19",
            "sensor": "avhrr-3",
            "name": "1",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 1050,
            "reader": "avhrr_l1b_aapp",
            "calibration": "reflectance",
            "standard_name": "toa_bidirectional_reflectance",
            "units": "%",
        },
    )


@pytest.fixture
def avhrr_l1b_2_data_array(avhrr_l1b_swath_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros(AVHRR_SHAPE, dtype=np.float32),
        dims=("y", "x"),
        attrs={
            "area": avhrr_l1b_swath_def,
            "platform_name": "noaa19",
            "sensor": "avhrr-3",
            "name": "2",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 1050,
            "reader": "avhrr_l1b_aapp",
            "calibration": "reflectance",
            "standard_name": "toa_bidirectional_reflectance",
            "units": "%",
        },
    )


@pytest.fixture
def avhrr_l1b_3a_data_array(avhrr_l1b_swath_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros(AVHRR_SHAPE, dtype=np.float32),
        dims=("y", "x"),
        attrs={
            "area": avhrr_l1b_swath_def,
            "platform_name": "noaa19",
            "sensor": "avhrr-3",
            "name": "3a",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 1050,
            "reader": "avhrr_l1b_aapp",
            "calibration": "reflectance",
            "standard_name": "toa_bidirectional_reflectance",
            "units": "%",
        },
    )


# No 3b. Assume day time scene


@pytest.fixture
def avhrr_l1b_4_data_array(avhrr_l1b_swath_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros(AVHRR_SHAPE, dtype=np.float32),
        dims=("y", "x"),
        attrs={
            "area": avhrr_l1b_swath_def,
            "platform_name": "noaa19",
            "sensor": "avhrr-3",
            "name": "4",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 1050,
            "reader": "avhrr_l1b_aapp",
            "calibration": "brightness_temperature",
            "standard_name": "toa_brightness_temperature",
            "units": "K",
        },
    )


@pytest.fixture
def avhrr_l1b_5_data_array(avhrr_l1b_swath_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros(AVHRR_SHAPE, dtype=np.float32),
        dims=("y", "x"),
        attrs={
            "area": avhrr_l1b_swath_def,
            "platform_name": "noaa19",
            "sensor": "avhrr-3",
            "name": "5",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 1050,
            "reader": "avhrr_l1b_aapp",
            "calibration": "brightness_temperature",
            "standard_name": "toa_brightness_temperature",
            "units": "K",
        },
    )


@pytest.fixture
def avhrr_l1b_1_scene(
    avhrr_l1b_1_data_array,
    avhrr_l1b_2_data_array,
    avhrr_l1b_3a_data_array,
    avhrr_l1b_4_data_array,
    avhrr_l1b_5_data_array,
) -> Scene:
    scn = _TestingScene(
        reader="avhrr_l1b_aapp",
        filenames=["/fake/filename"],
        data_array_dict={
            AVHRR_IDS[0]: avhrr_l1b_1_data_array.copy(),
            AVHRR_IDS[1]: avhrr_l1b_2_data_array.copy(),
            AVHRR_IDS[2]: avhrr_l1b_3a_data_array.copy(),
            AVHRR_IDS[4]: avhrr_l1b_4_data_array.copy(),
            AVHRR_IDS[5]: avhrr_l1b_5_data_array.copy(),
        },
        all_dataset_ids=AVHRR_IDS,
        available_dataset_ids=AVHRR_IDS[:3] + AVHRR_IDS[4:],
    )
    return scn
