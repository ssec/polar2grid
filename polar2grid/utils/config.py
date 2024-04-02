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
"""Helpers for setting up the Polar2Grid environment and configuration."""

import importlib.metadata as impm
import importlib.resources as impr
import os
import sys

import satpy


def get_polar2grid_etc():
    p2g_pkg_location = impr.files("polar2grid")
    if _is_editable_installation():
        return str(p2g_pkg_location / "etc")
    return p2g_pkg_location / "etc" / "polar2grid"


def _is_editable_installation():
    for installed_file in impm.files("polar2grid"):
        str_fn = str(installed_file)
        if "__editable__" in str_fn or "pyproject.toml" in str_fn:
            return True
    return False


def get_polar2grid_home():
    p2g_home = os.environ.get("POLAR2GRID_HOME")
    if p2g_home is None:
        # assume development/editable install
        import polar2grid

        os.environ["POLAR2GRID_HOME"] = os.path.join(os.path.dirname(polar2grid.__file__), "..", "swbundle")
    return os.environ["POLAR2GRID_HOME"]


def add_polar2grid_config_paths():
    config_path = satpy.config.get("config_path")
    p2g_etc = get_polar2grid_etc()
    if p2g_etc not in config_path:
        satpy.config.set(config_path=config_path + [p2g_etc])
