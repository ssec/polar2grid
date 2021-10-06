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
"""Test grid config helper script."""

import pytest

from polar2grid.grids.config_helper import main as ch_main


def test_help_usage(capsys):
    with pytest.raises(SystemExit) as e:
        ch_main(["--help"])
    assert e.value.code == 0
    sout = capsys.readouterr()
    assert "positional arguments" in sout.out

    # you must provide some parameters
    with pytest.raises(SystemExit) as e:
        ch_main([])
    assert e.value.code != 0
    sout = capsys.readouterr()
    assert "the following arguments are required" in sout.err


@pytest.mark.parametrize(
    ("lon", "lat", "exp"),
    [
        (
            "-95.0",
            "10.0",
            """my_grid:
  projection:
    proj: eqc
    lat_ts: 10
    lat_0: 0
    lon_0: -95
    datum: WGS84
    units: m
    no_defs: null
    type: crs
  shape:
    height: 1500
    width: 1500
  center:
    x: -95.0
    y: 10.0
    units: degrees
  resolution:
    dx: 1000.0
    dy: 1000.0

""",
        ),
        (
            "-95.0",
            "35.0",
            """my_grid:
  projection:
    proj: lcc
    lat_1: 35
    lat_0: 35
    lon_0: -95
    datum: WGS84
    units: m
    no_defs: null
    type: crs
  shape:
    height: 1500
    width: 1500
  center:
    x: -95.0
    y: 35.0
    units: degrees
  resolution:
    dx: 1000.0
    dy: 1000.0

""",
        ),
        (
            "-95.0",
            "80.0",
            """my_grid:
  projection:
    proj: stere
    lat_0: 90
    lat_ts: 80
    lon_0: -95
    datum: WGS84
    units: m
    no_defs: null
    type: crs
  shape:
    height: 1500
    width: 1500
  center:
    x: -95.0
    y: 80.0
    units: degrees
  resolution:
    dx: 1000.0
    dy: 1000.0

""",
        ),
    ],
)
def test_yaml_format(lon, lat, exp, capsys):
    ret = ch_main(["my_grid", lon, lat, "1000", "1000", "1500", "1500"])
    assert ret is None or ret == 0
    sout = capsys.readouterr()
    assert sout.out == exp
