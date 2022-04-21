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
IMAGE4_RGB_UINT8_ZEROS = np.zeros((3,) + SHAPE1, dtype=np.uint8)
IMAGE5_RGB_UINT8_ZEROS = np.zeros((3,) + SHAPE2, dtype=np.uint8)
IMAGE6_RGBA_UINT8_ZEROS = np.zeros((4,) + SHAPE1, dtype=np.uint8)
IMAGE7_RGB_UINT8_ONES = np.ones((3,) + SHAPE1, dtype=np.uint8)


def _create_geotiff(gtiff_fn, img_data):
    import rasterio

    band_count = 1 if img_data.ndim == 2 else img_data.shape[0]
    with rasterio.open(
        gtiff_fn,
        "w",
        driver="GTiff",
        count=band_count,
        height=img_data.shape[-2],
        width=img_data.shape[-1],
        dtype=img_data.dtype,
    ) as gtiff_file:
        if img_data.ndim == 2:
            img_data = img_data[None, :, :]
        for band_idx, band_arr in enumerate(img_data):
            gtiff_file.write(band_arr, band_idx + 1)


@pytest.mark.parametrize(
    ("expected_file_func", "actual_file_func"),
    [
        (None, None),  # no files
        (_create_geotiff, _create_geotiff),
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
        _create_geotiff(expected_dir / "test1.tif", expected_data)
    if actual_file_func:
        _create_geotiff(actual_dir / "test1.tif", actual_data)

    html_file = tmp_path / "test_output.html"
    dtype = None
    margin_of_error = 81231 / 1514041.44

    args = [
        str(expected_dir),
        str(actual_dir),
        "--margin-of-error",
        str(margin_of_error),
    ]
    if dtype is not None:
        args.extend(["--dtype", dtype])
    if include_html:
        args.extend(["--html", str(html_file)])

    num_diff_files = main(args)
    have_files = actual_file_func is not None and expected_file_func is not None
    if not have_files:
        assert num_diff_files == 0
    elif actual_file_func is not expected_file_func:
        assert num_diff_files != 0
    else:
        assert num_diff_files == exp_num_diff

    _check_html_output(include_html, html_file, have_files)


def _check_html_output(include_html, html_file, have_files):
    if include_html:
        assert os.path.isfile(html_file)
        base_dir = os.path.dirname(html_file)
        img_glob = os.path.join(base_dir, "_images", "*.png")
        if have_files:
            assert len(glob(img_glob)) != 0
        else:
            assert len(glob(img_glob)) == 0
    else:
        assert not os.path.isfile(html_file)
