#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2021 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
"""Tests for the convert_grids_conf_to_yaml.py script."""

from io import StringIO

import pytest
from pyresample import parse_area_file
from pyresample.geometry import AreaDefinition, DynamicAreaDefinition


@pytest.mark.parametrize(
    ("conf_content", "num_areas", "area_types"),
    [
        (
            """
wgs84_fit, proj4, +proj=latlong +datum=WGS84 +no_defs, None, None, 0.0057, -0.0057, None, None
""",
            1,
            [DynamicAreaDefinition],
        ),
        (
            """
211e, proj4, +proj=lcc +a=6371200 +b=6371200 +lat_0=25 +lat_1=25 +lon_0=-95 +units=m +no_defs, 5120, 5120, 1015.9, -1015.9, -123.044deg, 59.844deg
211e_10km, proj4, +proj=lcc +a=6371200 +b=6371200 +lat_0=25 +lat_1=25 +lon_0=-95 +units=m +no_defs, 512, 512, 10159, -10159, -123.044deg, 59.844deg
211e_hi, proj4, +proj=lcc +a=6371200 +b=6371200 +lat_0=25 +lat_1=25 +lon_0=-95 +units=m +no_defs, 10000, 10000, 500, -500, -123.044deg, 59.844deg
""",  # noqa
            3,
            [AreaDefinition] * 3,
        ),
    ],
)
def test_conf_conversion(tmpdir, capsys, conf_content, num_areas, area_types):
    from polar2grid.utils.convert_grids_conf_to_yaml import main

    grids_fn = tmpdir.join("test_grids.conf")
    with open(grids_fn, "w") as grids_file:
        grids_file.write(conf_content)

    main([str(grids_fn)])
    sout = capsys.readouterr()
    s = StringIO()
    s.write(sout.out)
    s.seek(0)
    areas = parse_area_file([s])
    assert len(areas) == num_areas
    for area_obj, area_type in zip(areas, area_types):
        assert isinstance(area_obj, area_type)
