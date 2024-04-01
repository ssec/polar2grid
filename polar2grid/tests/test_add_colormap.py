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
"""Basic usability tests for the add_colormap script."""

from __future__ import annotations

import os

import pytest
import rasterio
import satpy

from polar2grid.tests import TEST_ETC_DIR

from .test_add_coastlines import _create_fake_l_geotiff


def test_add_colormap_help():
    from polar2grid.add_colormap import main

    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0


@pytest.mark.parametrize(
    ("cmap_path", "exp_first_color", "exp_middle_color", "exp_last_color"),
    [
        (
            os.path.join(TEST_ETC_DIR, "colormaps", "amsr2_36h.cmap"),
            (0, 0, 0, 255),
            (128, 255, 130, 255),
            (128, 0, 0, 255),
        ),
        (os.path.join("colormaps", "amsr2_36h.cmap"), (0, 0, 0, 255), (128, 255, 130, 255), (128, 0, 0, 255)),
        (
            os.path.join(TEST_ETC_DIR, "colormaps", "WV_Chile_Short.cmap"),
            (0, 0, 0, 255),
            (0, 47, 144, 255),
            (127, 127, 127, 255),
        ),
        (os.path.join(TEST_ETC_DIR, "colormaps", "reds.cmap"), (0, 0, 0, 255), (129, 3, 39, 255), (255, 0, 0, 255)),
    ],
)
def test_add_colormap_basic_l(tmp_path, cmap_path, exp_first_color, exp_middle_color, exp_last_color):
    from polar2grid.add_colormap import main

    fp = str(tmp_path / "test.tif")
    _create_fake_l_geotiff(fp)
    with satpy.config.set(config_path=[TEST_ETC_DIR]):
        ret = main([cmap_path, fp])
    assert ret in [None, 0]

    with rasterio.open(fp, "r") as ds:
        cmap = ds.colormap(1)
        assert len(cmap) == 256
        assert cmap[0] == exp_first_color
        assert cmap[127] == exp_middle_color
        assert cmap[255] == exp_last_color
