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
#     input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
"""Tests for base/shared logic."""

import importlib
import os

import pytest

PKG_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
READER_BASE = os.path.join(PKG_ROOT, "readers")
ALL_READERS = [os.path.splitext(reader_fn)[0] for reader_fn in os.listdir(READER_BASE) if not reader_fn.startswith("_")]


@pytest.mark.parametrize("reader_name", ALL_READERS)
def test_reader_imports(reader_name):
    mod = importlib.import_module(f"polar2grid.readers.{reader_name}")
    assert hasattr(mod, "ReaderProxy")


@pytest.mark.parametrize("reader_name", ALL_READERS)
def test_reader_parser_arguments(reader_name):
    import argparse

    mod = importlib.import_module(f"polar2grid.readers.{reader_name}")
    assert hasattr(mod, "add_reader_argument_groups")

    parser = argparse.ArgumentParser()
    groups = mod.add_reader_argument_groups(parser)
    assert len(groups) == 2
