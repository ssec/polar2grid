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


def test_add_coastlines_help():
    from polar2grid.add_coastlines import main

    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0


def _create_fake_l_geotiff(fp):
    import rasterio

    kwargs = {
        "driver": "GTiff",
        "height": 1000,
        "width": 500,
        "count": 1,
        "dtype": np.uint8,
        "crs": "+proj=latlong",
        "transform": (0.033, 0.0, 0.0, 0.0, 0.033, 0.0),
    }
    with rasterio.open(fp, "w", **kwargs) as ds:
        ds.write(np.zeros((500, 1000), dtype=np.uint8), 1)


@mock.patch("polar2grid.add_coastlines.ContourWriterAGG.add_overlay_from_dict")
def test_add_coastlines_basic_l(add_overlay_mock, tmp_path):
    from polar2grid.add_coastlines import main

    fp = str(tmp_path / "test.tif")
    _create_fake_l_geotiff(fp)
    ret = main(["--add-coastlines", "--add-colorbar", fp])
    assert ret in [None, 0]
    assert os.path.isfile(tmp_path / "test.png")
    add_overlay_mock.assert_called_once()
    assert "coasts" in add_overlay_mock.call_args.args[0]
