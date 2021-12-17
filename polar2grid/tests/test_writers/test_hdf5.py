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
"""Tests for the hdf5 writer."""

import os

import pytest
import satpy

TEST_ETC_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "etc"))


class TestHDF5Writer:
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

    @pytest.mark.parametrize("add_geolocation", [False, True])
    def test_hdf5_basic(self, add_geolocation, abi_l1b_c01_scene, tmp_path):
        """Test basic writing of gridded data."""
        import h5py

        abi_l1b_c01_scene.save_datasets(
            writer="hdf5",
            base_dir=str(tmp_path),
            filename="{platform_name}_{sensor}_{start_time:%Y%m%d_%H%M%S}.h5",
            add_geolocation=add_geolocation,
        )
        exp_fn = tmp_path / "goes16_abi_20210101_120000.h5"

        assert os.path.isfile(exp_fn)
        hdf_file = h5py.File(exp_fn, "r")
        assert "goes_east" in hdf_file
        assert "C01" in hdf_file["goes_east"]
        if add_geolocation:
            assert "longitude" in hdf_file["goes_east"]
            assert "latitude" in hdf_file["goes_east"]
        else:
            assert "longitude" not in hdf_file["goes_east"]
            assert "latitude" not in hdf_file["goes_east"]
