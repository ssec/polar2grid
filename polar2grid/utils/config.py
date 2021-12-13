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
import os
import sys

import pkg_resources
import satpy


def get_polar2grid_etc():
    dist = pkg_resources.get_distribution("polar2grid")
    if dist_is_editable(dist):
        p2g_etc = os.path.join(dist.module_path, "etc")
    else:
        p2g_etc = os.path.join(sys.prefix, "etc", "polar2grid")
    return p2g_etc


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


def dist_is_editable(dist) -> bool:
    """Determine if the current installation is an editable/dev install."""
    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.project_name + ".egg-link")
        if os.path.isfile(egg_link):
            return True
    return False
