#!/usr/bin/env python3
# Copyright (C) 2026 Space Science and Engineering Center (SSEC),
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
"""Tests for the AMSR2 L2 GAASP reader's command line arguments."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from polar2grid.readers.amsr2_l2_gaasp import ReaderProxy


def _cli_reader_kwargs(tmp_path, extra_flags: list[str]) -> dict:
    from polar2grid._glue_argparser import GlueArgumentParser

    with mock.patch.dict(os.environ, {"USE_POLAR2GRID_DEFAULTS": "1"}):
        arg_parser = GlueArgumentParser(
            ["-r", "amsr2_l2_gaasp", "-w", "geotiff", "-f", str(tmp_path)] + extra_flags, True
        )
    return arg_parser._scene_creation["reader_kwargs"]


@pytest.mark.parametrize(
    ("extra_flags", "exp_filter_sea_ice"),
    [
        ([], True),
        (["--no-filter-sea-ice"], False),
    ],
)
def test_sea_ice_filter_flag(tmp_path, extra_flags, exp_filter_sea_ice):
    """Test that sea ice filtering is on by default and can be turned off."""
    reader_kwargs = ReaderProxy.convert_reader_kwargs(_cli_reader_kwargs(tmp_path, extra_flags))
    assert reader_kwargs == {"filter_wind_speed": True, "filter_sea_ice": exp_filter_sea_ice}
