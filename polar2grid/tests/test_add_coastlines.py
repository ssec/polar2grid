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
"""Basic usability tests for the add_coastlines script."""
import contextlib
import os
from unittest import mock

import numpy as np
import pytest
import rasterio
from PIL import Image


def test_add_coastlines_help():
    from polar2grid.add_coastlines import main

    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0


def _shared_fake_geotiff_kwargs(num_bands):
    kwargs = {
        "driver": "GTiff",
        "height": 1000,
        "width": 500,
        "count": num_bands,
        "dtype": np.uint8,
        "crs": "+proj=latlong",
        "transform": (0.033, 0.0, 0.0, 0.0, 0.033, 0.0),
    }
    return kwargs


def _shared_fake_l_geotiff_data():
    data = np.zeros((500, 1000), dtype=np.uint8)
    data[200:300, :] = 128
    data[300:, :] = 255
    return data


@contextlib.contextmanager
def _create_fake_geotiff(fp, num_bands):
    kwargs = _shared_fake_geotiff_kwargs(num_bands)
    with rasterio.open(fp, "w", **kwargs) as ds:
        for band_num in range(1, num_bands + 1):
            ds.write(_shared_fake_l_geotiff_data(), band_num)
        yield ds


@contextlib.contextmanager
def _create_fake_l_geotiff(fp):
    with _create_fake_geotiff(fp, 1) as ds:
        yield ds


@contextlib.contextmanager
def _create_fake_rgb_geotiff(fp):
    with _create_fake_geotiff(fp, num_bands=3) as ds:
        yield ds


@contextlib.contextmanager
def _create_fake_l_geotiff_colormap(fp):
    with _create_fake_l_geotiff(fp) as ds:
        ds.write_colormap(
            1,
            {
                0: (0, 0, 0, 255),
                128: (128, 0, 0, 255),
                255: (255, 0, 0, 255),
            },
        )
        yield ds


@pytest.mark.parametrize(
    "gen_func",
    [_create_fake_l_geotiff, _create_fake_l_geotiff_colormap],
)
@mock.patch("polar2grid.add_coastlines.ContourWriterAGG.add_overlay_from_dict")
def test_add_coastlines_basic_l(add_overlay_mock, tmp_path, gen_func):
    from polar2grid.add_coastlines import main

    fp = str(tmp_path / "test.tif")
    with gen_func(fp):
        pass
    ret = main(["--add-coastlines", "--add-colorbar", fp])
    assert ret in [None, 0]
    assert os.path.isfile(tmp_path / "test.png")
    add_overlay_mock.assert_called_once()
    assert "coasts" in add_overlay_mock.call_args.args[0]
    img = Image.open(tmp_path / "test.png")
    arr = np.asarray(img)
    # bottom of the image is a colorbar
    image_arr = arr[:940]
    r_uniques = np.unique(image_arr[:, :, 0])
    np.testing.assert_allclose(r_uniques, [0, 128, 255])
    g_colors = [0, 128, 255] if "colormap" not in gen_func.__name__ else [0]
    g_uniques = np.unique(image_arr[:, :, 1])
    np.testing.assert_allclose(g_uniques, g_colors)
    b_colors = [0, 128, 255] if "colormap" not in gen_func.__name__ else [0]
    b_uniques = np.unique(image_arr[:, :, 2])
    np.testing.assert_allclose(b_uniques, b_colors)
    assert (arr[940:] != 0).any()
