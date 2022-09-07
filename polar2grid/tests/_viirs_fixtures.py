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
"""Test fixtures representing VIIRS swath data."""
from __future__ import annotations

import dask.array as da
import numpy as np
import pytest
import xarray as xr
from numpy.typing import DTypeLike, NDArray
from pyresample import SwathDefinition
from satpy import Scene
from satpy.tests.utils import make_dataid

from ._fixture_utils import START_TIME, _TestingScene

VIIRS_I_CHUNKS = (32 * 3, 6400)
VIIRS_M_CHUNKS = (16 * 3, 3200)
VIIRS_DNB_CHUNKS = (16 * 3, 4064)

_mods = ("sunz_corrected_iband",)
VIIRS_I_IDS = [
    make_dataid(name="I01", wavelength=(0.6, 0.64, 0.68), resolution=371, calibration="reflectance", modifiers=_mods),
    make_dataid(
        name="I02", wavelength=(0.845, 0.865, 0.884), resolution=371, calibration="reflectance", modifiers=_mods
    ),
    make_dataid(
        name="I03", wavelength=(1.580, 1.610, 1.640), resolution=371, calibration="reflectance", modifiers=_mods
    ),
    make_dataid(name="I04", wavelength=(3.58, 3.74, 3.90), resolution=371, calibration="brightness_temperature"),
    make_dataid(name="I05", wavelength=(10.5, 11.45, 12.3), resolution=371, calibration="brightness_temperature"),
]
VIIRS_M_IDS = []
_mods = ("sunz_corrected",)
VIIRS_M_IDS.append(
    make_dataid(
        name="M01", wavelength=(0.402, 0.412, 0.422), resolution=742, calibration="reflectance", modifiers=_mods
    )
)
VIIRS_M_IDS.append(
    make_dataid(
        name="M02", wavelength=(0.436, 0.445, 0.454), resolution=742, calibration="reflectance", modifiers=_mods
    )
)
VIIRS_M_IDS.append(
    make_dataid(
        name="M03", wavelength=(0.478, 0.488, 0.498), resolution=742, calibration="reflectance", modifiers=_mods
    )
)
VIIRS_M_IDS.append(
    make_dataid(
        name="M04", wavelength=(0.545, 0.555, 0.565), resolution=742, calibration="reflectance", modifiers=_mods
    )
)
VIIRS_M_IDS.append(
    make_dataid(
        name="M05", wavelength=(0.662, 0.672, 0.682), resolution=742, calibration="reflectance", modifiers=_mods
    )
)
VIIRS_M_IDS.append(
    make_dataid(
        name="M06", wavelength=(0.739, 0.746, 0.754), resolution=742, calibration="reflectance", modifiers=_mods
    )
)
VIIRS_M_IDS.append(
    make_dataid(
        name="M07", wavelength=(0.846, 0.865, 0.885), resolution=742, calibration="reflectance", modifiers=_mods
    )
)
VIIRS_M_IDS.append(
    make_dataid(name="M08", wavelength=(1.23, 1.24, 1.25), resolution=742, calibration="reflectance", modifiers=_mods)
)
VIIRS_M_IDS.append(
    make_dataid(
        name="M09", wavelength=(1.371, 1.378, 1.386), resolution=742, calibration="reflectance", modifiers=_mods
    )
)
VIIRS_M_IDS.append(
    make_dataid(name="M10", wavelength=(1.58, 1.61, 1.64), resolution=742, calibration="reflectance", modifiers=_mods)
)
VIIRS_M_IDS.append(
    make_dataid(name="M11", wavelength=(2.225, 2.25, 2.275), resolution=742, calibration="reflectance", modifiers=_mods)
)
VIIRS_M_IDS.append(
    make_dataid(name="M12", wavelength=(3.61, 3.7, 3.79), resolution=742, calibration="brightness_temperature")
)
VIIRS_M_IDS.append(
    make_dataid(name="M13", wavelength=(3.973, 4.05, 4.128), resolution=742, calibration="brightness_temperature")
)
VIIRS_M_IDS.append(
    make_dataid(name="M14", wavelength=(8.4, 8.55, 8.7), resolution=742, calibration="brightness_temperature")
)
VIIRS_M_IDS.append(
    make_dataid(name="M15", wavelength=(10.263, 10.763, 11.263), resolution=742, calibration="brightness_temperature")
)
VIIRS_M_IDS.append(
    make_dataid(name="M16", wavelength=(11.538, 12.013, 12.489), resolution=742, calibration="brightness_temperature")
)
VIIRS_DNB_IDS = [make_dataid(name="DNB", resolution=743, calibration="radiance")]
VIIRS_M_ANGLES_IDS = []
VIIRS_I_ANGLES_IDS = []
VIIRS_DNB_ANGLES_IDS = []
for angle_suffix in ["solar_zenith_angle", "solar_azimuth_angle", "satellite_zenith_angle", "satellite_azimuth_angle"]:
    VIIRS_M_ANGLES_IDS.append(make_dataid(name=angle_suffix, resolution=742))
    VIIRS_I_ANGLES_IDS.append(make_dataid(name=angle_suffix, resolution=371))
    VIIRS_DNB_ANGLES_IDS.append(make_dataid(name="dnb_" + angle_suffix, resolution=743))
VIIRS_DNB_ANGLES_IDS.append(make_dataid(name="dnb_lunar_zenith_angle", resolution=743))
VIIRS_DNB_ANGLES_IDS.append(make_dataid(name="dnb_lunar_azimuth_angle", resolution=743))
VIIRS_DNB_ANGLES_IDS.append(make_dataid(name="dnb_moon_illumination_fraction"))

# VIIRS_COMP_IDS = [
#     make_dataid(name="dynamic_dnb"),
#     make_dataid(name="histogram_dnb"),
#     make_dataid(name="adaptive_dnb"),
#     make_dataid(name="hncc_dnb"),
#     make_dataid(name="ifog"),
#     make_dataid(name="true_color"),
#     make_dataid(name="false_color"),
# ]
VIIRS_ALL_IDS = (
    VIIRS_I_IDS + VIIRS_M_IDS + VIIRS_DNB_IDS + VIIRS_M_ANGLES_IDS + VIIRS_I_ANGLES_IDS + VIIRS_DNB_ANGLES_IDS
)


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
def viirs_sdr_m_swath_def() -> SwathDefinition:
    lons, lats = _generate_lonlat_data((768, 3200))
    lons_data_arr = xr.DataArray(
        da.from_array(lons, chunks=VIIRS_M_CHUNKS),
        dims=("y", "x"),
        attrs={
            "rows_per_scan": 16,
            "platform_name": "npp",
            "sensor": "viirs",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 742,
            "reader": "viirs_sdr",
        },
    )
    lats_data_arr = xr.DataArray(
        da.from_array(lats, chunks=VIIRS_M_CHUNKS),
        dims=("y", "x"),
        attrs={
            "rows_per_scan": 16,
            "platform_name": "npp",
            "sensor": "viirs",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 742,
            "reader": "viirs_sdr",
        },
    )
    return SwathDefinition(lons_data_arr, lats_data_arr)


@pytest.fixture(scope="session")
def viirs_sdr_dnb_swath_def() -> SwathDefinition:
    lons, lats = _generate_lonlat_data((768, 4064))
    lons_data_arr = xr.DataArray(
        da.from_array(lons, chunks=VIIRS_DNB_CHUNKS),
        dims=("y", "x"),
        attrs={
            "rows_per_scan": 16,
            "platform_name": "npp",
            "sensor": "viirs",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 743,
            "reader": "viirs_sdr",
        },
    )
    lats_data_arr = xr.DataArray(
        da.from_array(lats, chunks=VIIRS_DNB_CHUNKS),
        dims=("y", "x"),
        attrs={
            "rows_per_scan": 16,
            "platform_name": "npp",
            "sensor": "viirs",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 743,
            "reader": "viirs_sdr",
        },
    )
    return SwathDefinition(lons_data_arr, lats_data_arr)


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
            "calibration": "reflectance",
            "standard_name": "toa_bidirectional_reflectance",
            "units": "%",
        },
    )


@pytest.fixture
def viirs_sdr_i04_data_array(viirs_sdr_i_swath_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros((1536, 6400), dtype=np.float32),
        dims=("y", "x"),
        attrs={
            "area": viirs_sdr_i_swath_def,
            "rows_per_scan": 32,
            "platform_name": "npp",
            "sensor": "viirs",
            "name": "I04",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 371,
            "reader": "viirs_sdr",
            "calibration": "brightness_temperature",
            "standard_name": "toa_brightness_temperature",
            "units": "K",
        },
    )


@pytest.fixture
def viirs_sdr_m01_data_array(viirs_sdr_m_swath_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros((768, 3200), dtype=np.float32),
        dims=("y", "x"),
        attrs={
            "area": viirs_sdr_m_swath_def,
            "rows_per_scan": 16,
            "platform_name": "npp",
            "sensor": "viirs",
            "name": "M01",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 742,
            "reader": "viirs_sdr",
            "calibration": "reflectance",
            "standard_name": "toa_bidirectional_reflectance",
            "units": "%",
        },
    )


@pytest.fixture
def viirs_sdr_m12_data_array(viirs_sdr_m_swath_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros((768, 3200), dtype=np.float32),
        dims=("y", "x"),
        attrs={
            "area": viirs_sdr_m_swath_def,
            "rows_per_scan": 16,
            "platform_name": "npp",
            "sensor": "viirs",
            "name": "M12",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 743,
            "reader": "viirs_sdr",
            "calibration": "brightness_temperature",
            "standard_name": "toa_brightness_temperature",
            "units": "K",
        },
    )


@pytest.fixture
def viirs_sdr_dnb_data_array(viirs_sdr_dnb_swath_def) -> xr.DataArray:
    return xr.DataArray(
        da.zeros((768, 4064), dtype=np.float32),
        dims=("y", "x"),
        attrs={
            "area": viirs_sdr_dnb_swath_def,
            "rows_per_scan": 16,
            "platform_name": "npp",
            "sensor": "viirs",
            "name": "DNB",
            "start_time": START_TIME,
            "end_time": START_TIME,
            "resolution": 743,
            "reader": "viirs_sdr",
            "calibration": "brightness_temperature",
            "standard_name": "toa_brightness_temperature",
            "units": "W m-2 sr-1",
        },
    )


@pytest.fixture
def full_viirs_data_array_dict(
    viirs_sdr_i_dict,
    viirs_sdr_m_dict,
    viirs_sdr_dnb_dict,
):
    data_arrays = {}
    data_arrays.update(viirs_sdr_i_dict)
    data_arrays.update(viirs_sdr_m_dict)
    data_arrays.update(viirs_sdr_dnb_dict)
    return data_arrays


@pytest.fixture
def viirs_sdr_i_dict(viirs_sdr_i01_data_array, viirs_sdr_i04_data_array):
    data_arrays = {}
    for data_id in VIIRS_I_IDS[:3]:
        data_arrays[data_id] = viirs_sdr_i01_data_array.copy()
    for data_id in VIIRS_I_IDS[3:]:
        data_arrays[data_id] = viirs_sdr_i04_data_array.copy()
    data_arrays.update(_viirs_sdr_angles_dict(viirs_sdr_i01_data_array, VIIRS_I_ANGLES_IDS))
    return data_arrays


@pytest.fixture
def viirs_sdr_m_dict(viirs_sdr_m01_data_array, viirs_sdr_m12_data_array):
    data_arrays = {}
    for data_id in VIIRS_M_IDS[:12]:
        data_arrays[data_id] = viirs_sdr_m01_data_array.copy()
    for data_id in VIIRS_M_IDS[12:]:
        data_arrays[data_id] = viirs_sdr_m12_data_array.copy()
    data_arrays.update(_viirs_sdr_angles_dict(viirs_sdr_m01_data_array, VIIRS_M_ANGLES_IDS))
    return data_arrays


@pytest.fixture
def viirs_sdr_dnb_dict(viirs_sdr_dnb_data_array):
    data_arrays = {}
    for data_id in VIIRS_DNB_IDS:
        data_arrays[data_id] = viirs_sdr_dnb_data_array.copy()
    data_arrays.update(_viirs_sdr_angles_dict(viirs_sdr_dnb_data_array, VIIRS_DNB_ANGLES_IDS))
    return data_arrays


def _viirs_sdr_angles_dict(
    base_data_arr,
    angle_ids,
):
    data_arrays = {}
    for angle_id in angle_ids:
        data_arr = base_data_arr.copy()
        del data_arr.attrs["calibration"]
        data_arr.attrs["name"] = angle_id["name"]
        data_arrays[angle_id] = data_arr
    return data_arrays


@pytest.fixture
def viirs_sdr_i01_scene(viirs_sdr_i01_data_array) -> Scene:
    scn = _TestingScene(
        reader="viirs_sdr",
        filenames=["/fake/filename"],
        data_array_dict={
            VIIRS_I_IDS[0]: viirs_sdr_i01_data_array.copy(),
        },
        all_dataset_ids=VIIRS_ALL_IDS,
        available_dataset_ids=VIIRS_I_IDS[:1],
    )
    return scn


@pytest.fixture
def viirs_sdr_full_scene(full_viirs_data_array_dict) -> Scene:
    data_arrays = full_viirs_data_array_dict
    scn = _TestingScene(
        reader="viirs_sdr",
        filenames=["/fake/filename"],
        data_array_dict=data_arrays,
        all_dataset_ids=VIIRS_ALL_IDS,
        available_dataset_ids=list(data_arrays.keys()),
    )
    return scn
