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

from unittest import mock

import dask
import pytest
from pyresample.geometry import SwathDefinition
from pytest_lazyfixture import lazy_fixture
from satpy import Scene
from satpy.resample import DaskEWAResampler, KDTreeResampler, NativeResampler
from satpy.tests.utils import CustomScheduler

from polar2grid.resample._resample_scene import resample_scene


@pytest.mark.parametrize(
    (
        "input_scene",
        "grids",
        "grid_configs",
        "resampler",
        "exp_names",
        "max_computes",
        "is_polar2grid",
        "exp_resampler_cls",
        "extra_kwargs",
        "exp_kwargs",
    ),
    [
        (
            lazy_fixture("viirs_sdr_i01_scene"),
            ["wgs84_fit"],
            lazy_fixture("builtin_grids_yaml"),
            None,
            ["I01"],
            2,
            True,
            DaskEWAResampler,
            {},
            {"weight_delta_max": 40.0, "weight_distance_max": 2.0},
        ),
        (
            lazy_fixture("viirs_sdr_i01_scene"),
            ["wgs84_fit"],
            [],
            None,
            ["I01"],
            2,
            True,
            DaskEWAResampler,
            {},
            {"weight_delta_max": 40.0, "weight_distance_max": 2.0},
        ),
        (
            lazy_fixture("viirs_sdr_i01_scene"),
            ["wgs84_fit"],
            ["grids.conf"],
            None,
            ["I01"],
            2,
            True,
            DaskEWAResampler,
            {},
            {"weight_delta_max": 40.0, "weight_distance_max": 2.0},
        ),
        (
            lazy_fixture("viirs_sdr_i01_scene"),
            ["wgs84_fit"],
            ["grids.conf"],
            "ewa",
            ["I01"],
            2,
            True,
            DaskEWAResampler,
            {"weight_distance_max": 3.0, "maximum_weight_mode": True},
            {"weight_delta_max": 40.0, "weight_distance_max": 3.0, "maximum_weight_mode": True},
        ),
        (
            lazy_fixture("viirs_sdr_i01_scene"),
            ["wgs84_fit"],
            ["grids.conf"],
            None,
            ["I01"],
            2,
            True,
            DaskEWAResampler,
            {"weight_distance_max": 3.0, "maximum_weight_mode": True},
            {"weight_delta_max": 40.0, "weight_distance_max": 3.0, "maximum_weight_mode": True},
        ),
        (
            lazy_fixture("abi_l1b_c01_scene"),
            ["wgs84_fit"],
            lazy_fixture("builtin_grids_yaml"),
            "nearest",
            ["C01"],
            0,
            False,
            KDTreeResampler,
            {},
            {},
        ),
        (
            lazy_fixture("abi_l1b_c01_scene"),
            ["wgs84_fit"],
            lazy_fixture("builtin_grids_yaml"),
            None,
            ["C01"],
            0,
            False,
            KDTreeResampler,
            {},
            {},
        ),
        (
            lazy_fixture("abi_l1b_c01_scene"),
            ["MAX"],
            [],
            None,
            ["C01"],
            0,
            False,
            NativeResampler,
            {},
            {},
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
    exp_resampler_cls,
    extra_kwargs,
    exp_kwargs,
):
    from satpy.resample import resample

    with dask.config.set(scheduler=CustomScheduler(max_computes)), mock.patch(
        "satpy.resample.resample", wraps=resample
    ) as satpy_resample:
        input_scene.load(exp_names)
        scenes_to_save = resample_scene(
            input_scene,
            grids,
            grid_configs,
            resampler,
            is_polar2grid=is_polar2grid,
            **extra_kwargs,
        )
    satpy_resample.assert_called_once()
    satpy_resample.assert_called_once_with(
        mock.ANY, mock.ANY, mock.ANY, fill_value=mock.ANY, resampler=mock.ANY, **exp_kwargs
    )
    resample_kwargs = satpy_resample.call_args.kwargs
    assert isinstance(resample_kwargs["resampler"], exp_resampler_cls)
    assert len(scenes_to_save) == len(grids)
    for scene, data_ids_set in scenes_to_save:
        assert isinstance(scene, Scene)
        assert len(data_ids_set) == len(exp_names)
        id_names = [x["name"] for x in data_ids_set]
        for exp_name in exp_names:
            assert exp_name in id_names


def test_partial_filter(viirs_sdr_i01_data_array):
    """Test that resampling completes even when coverage filters some datasets."""
    # make another DataArray that is shifted away from the target area
    # orig_lons, orig_lats = viirs_sdr_i01_scene['I01'].attrs['area'].get_lonlats()
    new_i01 = viirs_sdr_i01_data_array.copy()
    orig_lons = new_i01.attrs["area"].lons
    orig_lats = new_i01.attrs["area"].lats
    new_lons = orig_lons + 180.0
    new_lons.attrs = orig_lons.attrs.copy()
    new_swath_def = SwathDefinition(new_lons, orig_lats)
    new_i01.attrs["name"] = "I01_2"
    new_i01.attrs["area"] = new_swath_def
    new_i01.attrs["sensor"] = {"viirs", "modis"}
    new_scn = Scene()
    new_scn["I01"] = viirs_sdr_i01_data_array
    new_scn["I01_2"] = new_i01

    # computation 1: input swath 1 polygon
    # computation 3: input swath 2 polygon (filtered and not resampled)
    with dask.config.set(scheduler=CustomScheduler(2)):
        scenes_to_save = resample_scene(
            new_scn,
            ["211e"],
            ["grids.conf"],
            None,
            is_polar2grid=True,
            grid_coverage=0.05,
        )
    assert len(scenes_to_save) == 1
    new_scn, data_ids = scenes_to_save[0]
    assert len(new_scn.keys()) == 1  # I01
