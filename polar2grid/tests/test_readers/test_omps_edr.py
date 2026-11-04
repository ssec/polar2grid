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
"""Tests for the OMPS EDR reader's command line arguments."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from polar2grid.readers.omps_edr import (
    OZONE_ERROR_FLAG_KEEP,
    OZONE_ERROR_FLAG_PRODUCTS,
    SO2_ERROR_FLAG_KEEP,
    SO2_ERROR_FLAG_PRODUCTS,
    ReaderProxy,
)

OZONE_FILTERS = dict.fromkeys(OZONE_ERROR_FLAG_PRODUCTS, OZONE_ERROR_FLAG_KEEP)
SO2_FILTERS = dict.fromkeys(SO2_ERROR_FLAG_PRODUCTS, SO2_ERROR_FLAG_KEEP)
P2G_ONLY_KWARGS = ("filter_ozone_by_error_flag", "filter_so2_by_error_flag")


def _cli_reader_kwargs(tmp_path, extra_flags: list[str]) -> dict:
    from polar2grid._glue_argparser import GlueArgumentParser

    with mock.patch.dict(os.environ, {"USE_POLAR2GRID_DEFAULTS": "1"}):
        arg_parser = GlueArgumentParser(["-r", "omps_edr", "-w", "geotiff", "-f", str(tmp_path)] + extra_flags, True)
    return arg_parser._scene_creation["reader_kwargs"]


def test_error_flag_product_groups():
    """Test that every product is in at most one error flag group."""
    assert OZONE_ERROR_FLAG_KEEP == [0, 1, 2]
    assert SO2_ERROR_FLAG_KEEP == [0, 1, 5]
    assert not set(OZONE_ERROR_FLAG_PRODUCTS) & set(SO2_ERROR_FLAG_PRODUCTS)
    assert "ColumnAmountO3" in OZONE_ERROR_FLAG_PRODUCTS
    assert "s_ColumnamountSO2_STL" in SO2_ERROR_FLAG_PRODUCTS
    assert "s_STLO3" in SO2_ERROR_FLAG_PRODUCTS


@pytest.mark.parametrize(
    ("extra_flags", "exp_error_flags_to_keep", "exp_eclipse", "exp_negative_so2"),
    [
        ([], OZONE_FILTERS | SO2_FILTERS, True, True),
        (["--no-filter-ozone-by-error-flag"], SO2_FILTERS, True, True),
        (["--no-filter-so2-by-error-flag"], OZONE_FILTERS, True, True),
        (["--no-filter-ozone-by-error-flag", "--no-filter-so2-by-error-flag"], None, True, True),
        (["--no-filter-eclipse"], OZONE_FILTERS | SO2_FILTERS, False, True),
        (["--no-filter-negative-so2"], OZONE_FILTERS | SO2_FILTERS, True, False),
    ],
)
def test_convert_reader_kwargs(tmp_path, extra_flags, exp_error_flags_to_keep, exp_eclipse, exp_negative_so2):
    """Test that command line flags are converted to the Satpy reader's keyword arguments."""
    cli_kwargs = _cli_reader_kwargs(tmp_path, extra_flags)
    orig_cli_kwargs = cli_kwargs.copy()

    satpy_kwargs = ReaderProxy.convert_reader_kwargs(cli_kwargs)

    assert cli_kwargs == orig_cli_kwargs
    assert satpy_kwargs == {
        "error_flags_to_keep": exp_error_flags_to_keep,
        "filter_eclipse": exp_eclipse,
        "filter_negative_so2": exp_negative_so2,
    }


def test_glue_passes_converted_reader_kwargs(chtmpdir):
    """Test that the main glue script creates the Scene with the converted reader keyword arguments."""
    from polar2grid.glue import main

    with (
        mock.patch.dict(os.environ, {"USE_POLAR2GRID_DEFAULTS": "1"}),
        mock.patch("polar2grid.glue._create_scene", return_value=None) as create_scene,
    ):
        ret = main(["-r", "omps_edr", "-w", "geotiff", "-f", str(chtmpdir), "--no-filter-so2-by-error-flag"])

    assert ret == -1
    create_scene.assert_called_once()
    scene_creation = create_scene.call_args.args[0]
    assert scene_creation["reader"] == "omps_edr"
    reader_kwargs = scene_creation["reader_kwargs"]
    assert reader_kwargs["error_flags_to_keep"] == OZONE_FILTERS
    assert reader_kwargs["filter_eclipse"] is True
    for p2g_only_kwarg in P2G_ONLY_KWARGS:
        assert p2g_only_kwarg not in reader_kwargs
