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
"""Test Polar2Grid-specific enhancement functions."""

import contextlib
import os
import shutil

import dask.array as da
import numpy as np
import pytest
import rasterio
import satpy
from satpy import Scene

from polar2grid.tests import TEST_ETC_DIR


@contextlib.contextmanager
def easy_cwd(new_dir=None):
    cur_dir = os.getcwd()
    try:
        if new_dir:
            os.chdir(new_dir)
        yield
    finally:
        os.chdir(cur_dir)


class TestP2GEnhancements:
    """Test p2g-specific enhancements."""

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

    def test_temperature_difference(self, tmpdir, abi_l1b_c01_data_array):
        new_data_arr = abi_l1b_c01_data_array.copy()
        data = da.linspace(-10, 10, new_data_arr.size).reshape(new_data_arr.shape)
        new_data_arr.data = data
        new_data_arr.attrs["name"] = "test_temperature_difference"
        scn = Scene()
        scn["test_temperature_difference"] = new_data_arr
        out_fn = str(tmpdir + "test_temperature_difference.tif")
        scn.save_datasets(filename=out_fn)

        with rasterio.open(out_fn, "r") as out_ds:
            assert out_ds.count == 2
            l_data = out_ds.read(1)
            # see polar2grid/tests/etc/enhancements/generic.yaml
            flat_l_data = l_data.ravel()
            data = data.ravel().compute()
            exp_out = np.round(np.linspace(5.0, 205.0, data.size)).astype(np.uint8)
            np.testing.assert_allclose(flat_l_data, exp_out)

    @pytest.mark.parametrize(
        "ds_name",
        [
            "test_p2g_palettize",
            "test_p2g_palettize2",
            "test_p2g_palettize3",
            "test_p2g_palettize4",
            "test_p2g_colorize",
        ],
    )
    @pytest.mark.parametrize("keep_palette", [False, True])
    def test_p2g_palettize(self, keep_palette, ds_name, tmpdir, abi_l1b_c01_data_array):
        if ds_name == "test_p2g_palettize3":
            shutil.copy(os.path.join(TEST_ETC_DIR, f"{ds_name}.npy"), tmpdir)
        new_data_arr = abi_l1b_c01_data_array.copy()
        data = da.linspace(180, 280, new_data_arr.size).reshape(new_data_arr.shape)
        new_data_arr.data = data
        new_data_arr.attrs["name"] = ds_name
        scn = Scene()
        scn[ds_name] = new_data_arr
        out_fn = str(tmpdir + f"{ds_name}_{keep_palette}.tif")
        with easy_cwd(tmpdir):
            scn.save_datasets(filename=out_fn, keep_palette=keep_palette)

        with rasterio.open(out_fn, "r") as out_ds:
            is_palette = keep_palette and "palettize" in ds_name
            num_bands = 1 if is_palette else 4
            assert out_ds.count == num_bands
            if is_palette:
                assert out_ds.colormap(1) is not None
