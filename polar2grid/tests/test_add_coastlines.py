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
import os
from unittest import mock

import numpy as np
import pytest
import rasterio
from PIL import Image

REDS_CMAP = {
    0: (0, 0, 0, 255),
    128: (128, 0, 0, 255),
    255: (255, 0, 0, 255),
}


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


def _create_fake_l_geotiff(fp):
    kwargs = _shared_fake_geotiff_kwargs(1)
    with rasterio.open(fp, "w", **kwargs) as ds:
        ds.write(_shared_fake_l_geotiff_data(), 1)


def _create_fake_rgb_geotiff(fp):
    kwargs = _shared_fake_geotiff_kwargs(3)
    with rasterio.open(fp, "w", **kwargs) as ds:
        r_data = _shared_fake_l_geotiff_data()
        ds.write(r_data, 1)
        ds.write(np.zeros_like(r_data), 2)
        ds.write(np.zeros_like(r_data), 3)


def _create_fake_rgb_geotiff_with_factor_offset(fp):
    kwargs = _shared_fake_geotiff_kwargs(3)
    with rasterio.open(fp, "w", **kwargs) as ds:
        r_data = _shared_fake_l_geotiff_data()
        ds.write(r_data, 1)
        ds.write(np.zeros_like(r_data), 2)
        ds.write(np.zeros_like(r_data), 3)
        ds.update_tags(scale=0.5, offset=0.0)


def _create_fake_l_geotiff_colormap(fp):
    kwargs = _shared_fake_geotiff_kwargs(1)
    with rasterio.open(fp, "w", **kwargs) as ds:
        ds.write(_shared_fake_l_geotiff_data(), 1)
        ds.write_colormap(1, REDS_CMAP)


def _create_ondisk_cmap_and_extra_args(tmp_path):
    cmap_fn = str(tmp_path / "reds.cmap")
    with open(cmap_fn, "w") as cmap_file:
        cmap_csv = [",".join(str(x) for x in [v] + list(color)) for v, color in REDS_CMAP.items()]
        cmap_file.write("\n".join(cmap_csv))
    return ["--colorbar-colormap-file", cmap_fn]


@pytest.mark.parametrize(
    ("gen_func", "has_colors", "create_cmap_file"),
    [
        (_create_fake_l_geotiff, False, False),
        (_create_fake_l_geotiff_colormap, True, False),
        (_create_fake_rgb_geotiff, True, True),
        (_create_fake_rgb_geotiff_with_factor_offset, True, True),
    ],
)
@mock.patch("polar2grid.add_coastlines.ContourWriterAGG.add_overlay_from_dict")
def test_add_coastlines_basic(add_overlay_mock, tmp_path, gen_func, has_colors, create_cmap_file):
    from polar2grid.add_coastlines import main

    fp = str(tmp_path / "test.tif")
    gen_func(fp)
    extra_args = []
    if create_cmap_file:
        extra_args.extend(_create_ondisk_cmap_and_extra_args(tmp_path))
    ret = main(["--add-coastlines", "--add-colorbar", fp] + extra_args)
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
    g_colors = [0] if has_colors else [0, 128, 255]
    g_uniques = np.unique(image_arr[:, :, 1])
    np.testing.assert_allclose(g_uniques, g_colors)
    b_colors = [0] if has_colors else [0, 128, 255]
    b_uniques = np.unique(image_arr[:, :, 2])
    np.testing.assert_allclose(b_uniques, b_colors)
    assert (arr[940:] != 0).any()
