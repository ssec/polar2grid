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
from __future__ import annotations

import contextlib
import os
from unittest import mock

import numpy as np
import pytest
import rasterio
from PIL import Image

REDS_SPREAD_CMAP = {
    0: (0, 0, 0, 255),
    128: (128, 0, 0, 255),
    255: (255, 0, 0, 255),
}
REDS_MIN_CMAP = {
    0: (0, 0, 0, 255),
    1: (128, 0, 0, 255),
    2: (255, 0, 0, 255),
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


def _shared_fake_l_geotiff_data(colormap: dict[int, tuple]):
    colormap_values = sorted(colormap.keys()) if colormap is not None else [0, 128, 255]
    data = np.zeros((500, 1000), dtype=np.uint8)
    data[:] = colormap_values[0]
    data[200:300, :] = colormap_values[1]
    data[300:, :] = colormap_values[2]
    return data


def _shared_fake_rgb_geotiff_data(colormap: dict[int, tuple]):
    colormap_values = [color[0] for color in colormap.values()]
    data = np.zeros((500, 1000), dtype=np.uint8)
    data[:] = colormap_values[0]
    data[200:300, :] = colormap_values[1]
    data[300:, :] = colormap_values[2]

    r_data = data
    g_data = np.zeros_like(r_data)
    b_data = np.zeros_like(r_data)
    return r_data, g_data, b_data


def _create_fake_l_geotiff(fp, colormap=None, include_scale_offset=False, include_colormap_tag=False):
    kwargs = _shared_fake_geotiff_kwargs(1)
    with rasterio.open(fp, "w", **kwargs) as ds:
        ds.write(_shared_fake_l_geotiff_data(colormap), 1)
        if include_scale_offset:
            ds.update_tags(scale=0.5, offset=0.0)
        # include_colormap_tag is not used because there is no logical way to
        # create a L geotiff that also has no colormap


def _create_fake_rgb_geotiff(fp, colormap=None, include_scale_offset=False, include_colormap_tag=False):
    kwargs = _shared_fake_geotiff_kwargs(3)
    with rasterio.open(fp, "w", **kwargs) as ds:
        r_data, g_data, b_data = _shared_fake_rgb_geotiff_data(colormap)
        ds.write(r_data, 1)
        ds.write(g_data, 2)
        ds.write(b_data, 3)
        if include_scale_offset:
            ds.update_tags(scale=0.5, offset=0.0)
        if include_colormap_tag:
            ds.update_tags(**_create_csv_cmap_and_extra_tags(colormap))


def _create_fake_l_geotiff_colormap(fp, colormap=None, include_scale_offset=False, include_colormap_tag=False):
    kwargs = _shared_fake_geotiff_kwargs(1)
    with rasterio.open(fp, "w", **kwargs) as ds:
        ds.write(_shared_fake_l_geotiff_data(colormap), 1)
        if colormap is not None:
            ds.write_colormap(1, colormap)
        if include_scale_offset:
            ds.update_tags(scale=0.5, offset=0.0)
        if colormap is not None and include_colormap_tag:
            ds.update_tags(**_create_csv_cmap_and_extra_tags(colormap))


def _create_csv_cmap_and_extra_tags(colormap):
    cmap_csv = [",".join(str(x) for x in [v] + list(color)) for v, color in colormap.items()]
    cmap_csv_str = "\n".join(cmap_csv)
    return {"colormap": cmap_csv_str}


@pytest.mark.parametrize(
    ("gen_func", "include_scale_offset", "include_cmap_tag"),
    [
        (_create_fake_l_geotiff, False, False),
        (_create_fake_l_geotiff_colormap, False, False),
        (_create_fake_l_geotiff_colormap, True, False),
        (_create_fake_l_geotiff_colormap, True, True),
        (_create_fake_rgb_geotiff, False, True),
        (_create_fake_rgb_geotiff, True, True),
    ],
)
@pytest.mark.parametrize("colormap", [REDS_SPREAD_CMAP, REDS_MIN_CMAP])
@mock.patch("polar2grid.add_coastlines.ContourWriterAGG.add_overlay_from_dict")
def test_add_coastlines_basic(add_overlay_mock, tmp_path, gen_func, include_scale_offset, include_cmap_tag, colormap):
    from polar2grid.add_coastlines import main

    is_rgb = "rgb" in gen_func.__name__
    has_colormap = "colormap" in gen_func.__name__
    has_colors = colormap is not None and (has_colormap or is_rgb)

    fp = str(tmp_path / "test.tif")
    gen_func(fp, colormap, include_scale_offset=include_scale_offset, include_colormap_tag=include_cmap_tag)
    extra_args = []

    with mocked_pydecorate_add_scale() as add_scale_mock:
        ret = main(["--add-coastlines", "--add-colorbar", fp] + extra_args)

    assert ret in [None, 0]
    assert os.path.isfile(tmp_path / "test.png")
    add_overlay_mock.assert_called_once()
    assert "coasts" in add_overlay_mock.call_args.args[0]
    add_scale_mock.assert_called_once()
    passed_cmap = add_scale_mock.call_args.kwargs["colormap"]
    _check_used_colormap(passed_cmap, has_colors, include_cmap_tag, include_scale_offset)

    img = Image.open(tmp_path / "test.png")
    arr = np.asarray(img)
    # bottom of the image is a colorbar
    image_arr = arr[:940]
    _check_exp_image_colors(image_arr, colormap, 0, has_colors)
    _check_exp_image_colors(image_arr, colormap, 1, has_colors)
    _check_exp_image_colors(image_arr, colormap, 2, has_colors)
    assert (arr[940:] != 0).any()


def _check_used_colormap(passed_cmap, has_colors, include_cmap_tag, include_scale_offset):
    cmin = passed_cmap.values[0]
    cmax = passed_cmap.values[-1]
    cmap_size = passed_cmap.values.size
    exp_cmap_size = 255 if not has_colors or not include_cmap_tag else 3
    exp_cmin = 0.0
    exp_cmax = 255.0 if not has_colors or not include_scale_offset else 127.5
    assert cmap_size == exp_cmap_size
    assert cmin == exp_cmin
    assert cmax == exp_cmax

    if not has_colors:
        # no colormap, pure black colorbar
        np.testing.assert_allclose(passed_cmap.colors[:, :3], 0)


def _check_exp_image_colors(image_arr, colormap, color_idx, has_colors):
    exp_raw_values = list(colormap.keys())
    cmap_colors = list(set(color[color_idx] for color in colormap.values()))
    exp_colors = cmap_colors if has_colors else exp_raw_values
    r_uniques = np.unique(image_arr[:, :, color_idx])
    np.testing.assert_allclose(r_uniques, exp_colors)


@contextlib.contextmanager
def mocked_pydecorate_add_scale():
    from polar2grid.add_coastlines import DecoratorAGG

    add_scale_mock = mock.Mock()
    decorator_mock = mock.Mock()

    def _create_decorator(img):
        dec = DecoratorAGG(img)
        add_scale_mock.side_effect = dec.add_scale
        dec.add_scale = add_scale_mock
        return dec

    decorator_mock.side_effect = _create_decorator
    with mock.patch("polar2grid.add_coastlines.DecoratorAGG", decorator_mock):
        yield add_scale_mock


@mock.patch("polar2grid.add_coastlines.ContourWriterAGG.add_overlay_from_dict")
def test_add_coastlines_bad_output_filenames(add_overlay_mock, tmp_path):
    from polar2grid.add_coastlines import main

    fp = str(tmp_path / "test.tif")
    _create_fake_l_geotiff(fp)
    extra_args = ["-o", "test1.png", "test2.png"]
    ret = main(["--add-coastlines", "--add-colorbar", fp] + extra_args)
    assert ret == -1
    assert not os.path.isfile(tmp_path / "test.png")
    add_overlay_mock.assert_not_called()
