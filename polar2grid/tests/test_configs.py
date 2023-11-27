#!/usr/bin/env python3
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
"""Tests for polar2grid configuration files."""

import os
from glob import glob

import yaml


def pytest_generate_tests(metafunc):
    """Generate parametrized tests to run on all YAML files.

    Automatically used by pytest as a hook..

    """
    if "yaml_config_file" in metafunc.fixturenames:
        root_dir = os.path.join(os.path.dirname(__file__), "..")
        glob_pat = os.path.join(root_dir, "etc", "**", "*.yaml")
        p2g_yaml_files = sorted(glob(glob_pat, recursive=True))
        assert len(p2g_yaml_files) != 0
        metafunc.parametrize("yaml_config_file", p2g_yaml_files)


def test_valid_yaml_files(yaml_config_file):
    """Test basic YAML syntax for all config files."""
    with open(yaml_config_file, "r") as yaml_file:
        yaml.load(yaml_file, Loader=yaml.UnsafeLoader)
