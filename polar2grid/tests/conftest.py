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
"""Test initialization and fixtures."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

PKG_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
root_logger = logging.getLogger()

pytest_plugins = [
    "polar2grid.tests._abi_fixtures",
    "polar2grid.tests._viirs_fixtures",
    "polar2grid.tests._avhrr_fixtures",
]


def pytest_configure(config):
    from polar2grid.utils.config import add_polar2grid_config_paths

    add_polar2grid_config_paths()


@pytest.fixture(autouse=True)
def clear_cached_functions():
    from polar2grid.filters._utils import polygon_for_area
    from polar2grid.filters.day_night import _get_sunlight_coverage

    _get_sunlight_coverage.cache_clear()
    polygon_for_area.cache_clear()


@pytest.fixture
def chtmpdir(tmp_path: Path):
    lwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(lwd)


@pytest.fixture(scope="session")
def builtin_grids_yaml() -> list[str]:
    return [os.path.join(PKG_ROOT, "grids", "grids.yaml")]


@pytest.fixture(scope="session")
def builtin_test_grids_conf() -> list[str]:
    return [os.path.join(PKG_ROOT, "tests", "etc", "grids.conf")]


@pytest.fixture(autouse=True)
def ensure_logging_framework_not_altered():
    """Protect logger handlers to avoid capsys closing files."""
    before_handlers = list(root_logger.handlers)
    yield
    root_logger.handlers = before_handlers


@pytest.fixture(autouse=True, scope="session")
def _forbid_pyspectral_downloads():
    from pyspectral.testing import forbid_pyspectral_downloads

    with forbid_pyspectral_downloads():
        yield
