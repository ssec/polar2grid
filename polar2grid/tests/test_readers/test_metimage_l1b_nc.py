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
"""Tests for the METimage L1B reader's product loading and command line arguments."""

from __future__ import annotations

import os
from unittest import mock

import pytest
from satpy import DataQuery
from satpy.tests.utils import make_dataid

from polar2grid.readers.metimage_l1b_nc import (
    ALL_BANDS,
    BT_BANDS,
    COMPOSITES,
    REFLECTANCE_BANDS,
    ReaderProxy,
)

SUNZ = ("sunz_corrected",)


def _fake_scene():
    scn = mock.MagicMock()
    scn.all_dataset_names.return_value = ALL_BANDS + COMPOSITES
    return scn


@pytest.mark.parametrize(
    ("user_products", "exp_modifiers"),
    [
        (["vii_443", "vii_10690"], SUNZ),
        (["vii_443", "vii_10690", "normalized_radiances"], ()),
        (["normalized_radiances", "vii_443", "normalized_radiances", "vii_10690"], ()),
    ],
)
def test_reflectance_modifiers(user_products, exp_modifiers):
    """Test that reflectance bands are sun zenith corrected unless normalized radiances are requested."""
    orig_user_products = user_products.copy()
    reader_proxy = ReaderProxy(_fake_scene(), user_products)

    to_load = reader_proxy.get_satpy_products_to_load()

    assert to_load == [DataQuery(name="vii_443", modifiers=exp_modifiers), "vii_10690"]
    assert user_products == orig_user_products


@pytest.mark.parametrize(
    ("user_products", "exp_modifiers"),
    [
        ([], SUNZ),
        (["normalized_radiances"], ()),
    ],
)
def test_default_products(user_products, exp_modifiers):
    """Test that the flag alone still loads the default products, with the requested modifiers."""
    reader_proxy = ReaderProxy(_fake_scene(), user_products)

    to_load = reader_proxy.get_satpy_products_to_load()

    exp_to_load = [DataQuery(name=band, modifiers=exp_modifiers) for band in REFLECTANCE_BANDS]
    exp_to_load += BT_BANDS + COMPOSITES
    assert to_load == exp_to_load


@pytest.mark.parametrize("modifiers", [SUNZ, ()])
def test_loaded_reflectance_keeps_p2g_name(modifiers):
    """Test that a loaded reflectance band maps back to its plain product name."""
    user_products = ["vii_443"] if modifiers else ["vii_443", "normalized_radiances"]
    reader_proxy = ReaderProxy(_fake_scene(), user_products)
    loaded_id = make_dataid(name="vii_443", resolution=500, calibration="reflectance", modifiers=modifiers)

    p2g_names = list(reader_proxy._alias_handler.convert_satpy_to_p2g_name([loaded_id]))

    assert p2g_names == ["vii_443"]


@pytest.mark.parametrize(
    ("extra_flags", "exp_products"),
    [
        ([], []),
        (["--normalized-radiances"], ["normalized_radiances"]),
        (["-p", "vii_443", "--normalized-radiances"], ["vii_443", "normalized_radiances"]),
    ],
)
def test_normalized_radiances_flag(tmp_path, extra_flags, exp_products):
    """Test that the command line flag is passed to the reader proxy through the product list."""
    from polar2grid._glue_argparser import GlueArgumentParser

    with mock.patch.dict(os.environ, {"USE_POLAR2GRID_DEFAULTS": "1"}):
        arg_parser = GlueArgumentParser(
            ["-r", "metimage_l1b_nc", "-w", "geotiff", "-f", str(tmp_path)] + extra_flags, True
        )
    assert arg_parser._load_args["products"] == exp_products
