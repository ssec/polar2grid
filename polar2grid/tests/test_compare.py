#!/usr/bin/env python3
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
"""Tests for the compare.py script."""

import os
from glob import glob

import numpy as np
import pytest

SHAPE1 = (200, 100)
SHAPE2 = (200, 101)
IMAGE1_L_UINT8_ZEROS = np.zeros(SHAPE1, dtype=np.uint8)
IMAGE2_L_UINT8_ZEROS = np.zeros(SHAPE2, dtype=np.uint8)
IMAGE3_L_UINT8_ONES = np.ones(SHAPE1, dtype=np.uint8)
IMAGE4_L_FLOAT32_ZEROS = np.zeros(SHAPE1, dtype=np.float32)
IMAGE4_RGB_UINT8_ZEROS = np.zeros((3,) + SHAPE1, dtype=np.uint8)
IMAGE5_RGB_UINT8_ZEROS = np.zeros((3,) + SHAPE2, dtype=np.uint8)
IMAGE6_RGBA_UINT8_ZEROS = np.zeros((4,) + SHAPE1, dtype=np.uint8)
IMAGE7_RGB_UINT8_ONES = np.ones((3,) + SHAPE1, dtype=np.uint8)
IMAGE_LIST1 = [IMAGE1_L_UINT8_ZEROS, IMAGE1_L_UINT8_ZEROS]
IMAGE_LIST2 = [IMAGE1_L_UINT8_ZEROS, IMAGE2_L_UINT8_ZEROS, IMAGE4_RGB_UINT8_ZEROS]


def _create_geotiffs(base_dir, img_data):
    import rasterio

    if not isinstance(img_data, (list, tuple)):
        img_data = [img_data]

    for idx, img_arr in enumerate(img_data):
        band_count = 1 if img_arr.ndim == 2 else img_arr.shape[0]
        gtiff_fn = os.path.join(base_dir, f"test{idx}.tif")
        with rasterio.open(
            gtiff_fn,
            "w",
            driver="GTiff",
            count=band_count,
            height=img_arr.shape[-2],
            width=img_arr.shape[-1],
            dtype=img_arr.dtype,
        ) as gtiff_file:
            if img_arr.ndim == 2:
                img_arr = img_arr[None, :, :]
            for band_idx, band_arr in enumerate(img_arr):
                gtiff_file.write(band_arr, band_idx + 1)


def _create_hdf5(base_dir, img_data):
    import h5py

    if not isinstance(img_data, (list, tuple)):
        img_data = [img_data]

    h5_fn = os.path.join(base_dir, "test.h5")
    with h5py.File(h5_fn, "w") as h:
        for idx, img_arr in enumerate(img_data):
            ds = h.create_dataset(f"image{idx}", data=img_arr)
            ds.attrs["some_attr"] = f"some_value{idx}"


def _create_binaries(base_dir, img_data):
    if not isinstance(img_data, (list, tuple)):
        img_data = [img_data]
    for idx, img_arr in enumerate(img_data):
        bin_fn = os.path.join(base_dir, f"test{idx}.dat")
        img_arr.tofile(bin_fn)


def _create_awips_tiled(base_dir, img_data):
    from netCDF4 import Dataset

    if not isinstance(img_data, (list, tuple)):
        img_data = [img_data]
    # 2 tiles per dataset
    for idx, img_arr in enumerate(img_data):
        for tile_id in ("T01", "T02"):
            fn = f"SSEC_AII_gcom-w1_amsr2_image{idx}_LCC_T{tile_id}_20160719_1903.nc"
            fp = os.path.join(base_dir, fn)
            nc = Dataset(fp, "w")
            nc.createDimension("y", img_arr.shape[-2])
            nc.createDimension("x", img_arr.shape[-1])
            dims = ("y", "x")
            if img_arr.ndim == 3:
                dims = ("bands",) + dims
                nc.createDimension("bands", img_arr.shape[0])
            nc_var = nc.createVariable("data", img_arr.dtype, dimensions=dims)
            nc_var[:] = img_arr
            nc_var.grid_mapping = "lcc_grid_mapping"

            lcc_grid_mapping = nc.createVariable("lcc_grid_mapping", np.int32)
            lcc_grid_mapping.grid_mapping_name = "lambert_conformal_conic"
            lcc_grid_mapping.standard_parallel = 25.0
            lcc_grid_mapping.longitude_of_central_meridian = 0.0
            lcc_grid_mapping.latitude_of_projection_origin = 35.0

            y_var = nc.createVariable("y", np.float32, dimensions=("y",))
            y_var[:] = np.arange(img_arr.shape[-2], dtype=np.float32)
            x_var = nc.createVariable("x", np.float32, dimensions=("x",))
            x_var[:] = np.arange(img_arr.shape[-1], dtype=np.float32)


@pytest.mark.parametrize(
    ("expected_file_func", "actual_file_func"),
    [
        (None, None),  # no files
        (_create_geotiffs, _create_hdf5),
        (_create_geotiffs, _create_geotiffs),
        (_create_hdf5, _create_hdf5),
        (_create_binaries, _create_binaries),
        (_create_awips_tiled, _create_awips_tiled),
    ],
)
@pytest.mark.parametrize(
    ("expected_data", "actual_data", "exp_num_diff"),
    [
        (IMAGE1_L_UINT8_ZEROS, IMAGE1_L_UINT8_ZEROS, 0),
        (IMAGE1_L_UINT8_ZEROS, IMAGE2_L_UINT8_ZEROS, 1),
        (IMAGE1_L_UINT8_ZEROS, IMAGE3_L_UINT8_ONES, 1),
        (IMAGE3_L_UINT8_ONES, IMAGE3_L_UINT8_ONES, 0),
        (IMAGE4_RGB_UINT8_ZEROS, IMAGE4_RGB_UINT8_ZEROS, 0),
        (IMAGE6_RGBA_UINT8_ZEROS, IMAGE6_RGBA_UINT8_ZEROS, 0),
        (IMAGE4_RGB_UINT8_ZEROS, IMAGE5_RGB_UINT8_ZEROS, 1),
        (IMAGE4_RGB_UINT8_ZEROS, IMAGE6_RGBA_UINT8_ZEROS, 1),
        (IMAGE4_RGB_UINT8_ZEROS, IMAGE7_RGB_UINT8_ONES, 1),
        (IMAGE_LIST1, IMAGE_LIST1, 0),
        (IMAGE_LIST2, IMAGE_LIST2, 0),
        (IMAGE_LIST2, IMAGE_LIST1, 2),
        (IMAGE4_L_FLOAT32_ZEROS, IMAGE4_L_FLOAT32_ZEROS, 0),
    ],
)
@pytest.mark.parametrize("include_html", [False, True])
def test_basic_compare(
    tmp_path, expected_file_func, actual_file_func, expected_data, actual_data, exp_num_diff, include_html
):
    from polar2grid.compare import main

    expected_dir = tmp_path / "expected"
    expected_dir.mkdir()
    actual_dir = tmp_path / "actual"
    actual_dir.mkdir()

    if expected_file_func:
        expected_file_func(expected_dir, expected_data)
    if actual_file_func:
        actual_file_func(actual_dir, actual_data)

    margin_of_error = 81231 / 1514041.44

    args = [
        str(expected_dir),
        str(actual_dir),
        "--margin-of-error",
        str(margin_of_error),
    ]
    dtype = None
    if dtype is not None:
        args.extend(["--dtype", dtype])
    html_file = tmp_path / "test_output.html"
    if include_html:
        args.extend(["--html", str(html_file)])

    num_diff_files = main(args)
    exp_num_png_files = _get_exp_num_png_files(actual_data, expected_data, expected_file_func)
    _check_num_diff_files(num_diff_files, exp_num_diff, expected_file_func, actual_file_func)
    _check_html_output(include_html, html_file, exp_num_png_files, expected_file_func, actual_file_func)


def _get_exp_num_png_files(actual_data, expected_data, expected_file_func):
    exp_num_expected_png_files = len(expected_data) if isinstance(expected_data, list) else 1
    exp_num_actual_png_files = len(actual_data) if isinstance(actual_data, list) else 1
    if _is_multivar_format(expected_file_func):
        # if the file exists then we will be creating a thumbnail for every possible variable
        exp_num_png_files = exp_num_actual_png_files + exp_num_expected_png_files
    else:
        # images are only generated when both files exist
        exp_num_png_files = min(exp_num_expected_png_files, exp_num_actual_png_files) * 2
    exp_num_png_files *= _files_per_variable(expected_file_func)
    return exp_num_png_files


def _check_num_diff_files(num_diff_files, exp_num_diff, expected_file_func, actual_file_func):
    have_files = actual_file_func is not None and expected_file_func is not None
    if not have_files:
        assert num_diff_files == 0
    elif actual_file_func is not expected_file_func:
        assert num_diff_files != 0
    elif _is_multivar_format(expected_file_func):
        # multiple variables in one file
        assert num_diff_files == (1 if exp_num_diff > 0 else 0)
    else:
        assert num_diff_files == exp_num_diff * _files_per_variable(expected_file_func)


def _is_multivar_format(expected_file_func):
    return {
        _create_hdf5: True,
    }.get(expected_file_func, False)


def _files_per_variable(expected_file_func):
    return {_create_awips_tiled: 2}.get(expected_file_func, 1)


def _check_html_output(include_html, html_file, exp_total_files, expected_file_func, actual_file_func):
    base_dir = os.path.dirname(html_file)
    if include_html:
        assert os.path.isfile(html_file)
        img_glob = os.path.join(base_dir, "_images", "*.png")
        formats_are_different = actual_file_func is not expected_file_func
        files_were_generated = actual_file_func is not None and expected_file_func is not None
        can_gen_tn = _can_generate_thumbnails(actual_file_func)
        should_have_thumbnails = not formats_are_different and files_were_generated and can_gen_tn

        if should_have_thumbnails:
            print(len(glob(img_glob)))
            assert len(glob(img_glob)) == exp_total_files
        else:
            assert len(glob(img_glob)) == 0
    else:
        assert len(glob(os.path.join(base_dir, "*.html"))) == 0


def _can_generate_thumbnails(creation_func) -> bool:
    return creation_func in (_create_geotiffs, _create_awips_tiled, _create_hdf5, _create_binaries)
