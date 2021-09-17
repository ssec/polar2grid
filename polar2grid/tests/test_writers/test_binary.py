#!/usr/bin/env python3
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
"""Tests for the binary writer."""

import os
from datetime import datetime
from unittest import mock

import satpy
from satpy import Scene
import xarray as xr
import dask.array as da
import numpy as np
import pytest


TEST_ETC_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "etc"))


def _int_min_max(dtype):
    info = np.iinfo(dtype)
    return info.min, info.max


def _min_max_for_two_dtypes(src_dtype, dst_dtype):
    src_is_int = not np.issubdtype(src_dtype, np.floating)
    dst_is_int = not np.issubdtype(dst_dtype, np.floating)
    if src_is_int and dst_is_int:
        smin, smax = _int_min_max(src_dtype)
        dmin, dmax = _int_min_max(dst_dtype)
        return max(smin, dmin), min(smax, dmax)
    elif src_is_int:
        return _int_min_max(src_dtype)
    return _int_min_max(dst_dtype)


def _create_fake_data_arr(shape=(100, 50), dims=("y", "x"), dtype=np.float64):
    area_mock = mock.MagicMock()
    area_mock.area_id = "fake_area"
    attrs = {
        "name": "fake_name",
        "p2g_name": "fake_p2g_name",
        "platform_name": "NOAA-20",
        "sensor": "viirs",
        "start_time": datetime(2021, 1, 1, 12, 0, 0),
        "end_time": datetime(2021, 1, 1, 12, 10, 0),
        "area": area_mock,
        "standard_name": "test_arange",
    }
    data = np.arange(np.prod(shape), dtype=np.float64)
    if not np.issubdtype(dtype, np.floating):
        data = np.clip(data, *_int_min_max(dtype))
        attrs["_FillValue"] = 0
    data = data.astype(dtype)
    data = da.from_array(data, chunks=10).reshape(shape)
    data_arr = xr.DataArray(data, attrs=attrs, dims=dims)
    return data_arr


class TestBinaryWriter:
    """Test the binary writer."""

    def setup_method(self):
        """Add P2G configs to the Satpy path."""
        from polar2grid.utils.config import add_polar2grid_config_paths

        self._old_path = satpy.config.get("config_path")
        add_polar2grid_config_paths()
        # add test specific configs
        curr_path = satpy.config.get("config_path")
        satpy.config.set(config_path=[TEST_ETC_DIR] + curr_path)

    def teardown_method(self):
        """Reset Satpy config path back to the original value."""
        satpy.config.set(config_path=self._old_path)

    @pytest.mark.parametrize("enhance", [True, False])
    @pytest.mark.parametrize("dst_dtype", [None, np.float32, np.float64, np.uint8])
    @pytest.mark.parametrize("src_dtype", [np.float32, np.float64, np.uint8])
    def test_basic_write(self, tmpdir, src_dtype, dst_dtype, enhance):
        """Test writing data to disk."""
        src_data_arr = _create_fake_data_arr(dtype=src_dtype)
        scn = Scene()
        scn[src_data_arr.attrs["name"]] = src_data_arr
        scn.save_datasets(writer="binary", base_dir=str(tmpdir), dtype=dst_dtype, enhance=enhance)
        exp_fn = tmpdir.join("noaa-20_viirs_fake_p2g_name_20210101_120000_fake_area.dat")

        if dst_dtype is None:
            dst_dtype = src_dtype if src_dtype != np.float64 else np.float32
        assert os.path.isfile(exp_fn)
        data = np.memmap(str(exp_fn), mode="r", dtype=dst_dtype)
        exp_data = self._generate_expected_output(src_data_arr, dst_dtype, enhance)
        np.testing.assert_allclose(data, exp_data, atol=2e-7)

    @staticmethod
    def _generate_expected_output(src_data_arr, dst_dtype, enhance):
        src_dtype = src_data_arr.dtype
        exp_data = src_data_arr.values.astype(np.float64).ravel()
        if enhance:
            exp_data = exp_data / 500.0  # see polar2grid/tests/etc/enhancements/generic.yaml
            if not np.issubdtype(dst_dtype, np.floating):
                rmin, rmax = _int_min_max(dst_dtype)
                exp_data = exp_data * (rmax - rmin) + rmin
                exp_data = np.clip(exp_data, rmin, rmax)
            exp_data = exp_data.astype(dst_dtype)
        elif not np.issubdtype(dst_dtype, np.floating) or not np.issubdtype(src_dtype, np.floating):
            rmin, rmax = _min_max_for_two_dtypes(src_dtype, dst_dtype)
            exp_data = np.clip(exp_data, rmin, rmax)
        return exp_data
