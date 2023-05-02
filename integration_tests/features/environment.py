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
"""Configure behave tests."""
import os
import shutil
import sys
import tempfile


def before_all(context):
    context.html_dst = context.config.userdata.get("html_dst", None)
    if context.html_dst is not None:
        context.html_dst = os.path.join(context.html_dst, "test_status")
    context.datapath = context.config.userdata["datapath"]
    if not context.datapath.startswith(os.sep):
        context.datapath = os.path.join(os.getcwd(), context.datapath)
    os.environ["DATA_PATH"] = context.datapath  # for test command replacement
    p2g_home = os.environ.get("POLAR2GRID_HOME")
    # if POLAR2GRID_HOME isn't defined, assume things are installed in the python prefix
    context.p2g_path = os.path.join(p2g_home, "bin") if p2g_home is not None else os.path.join(sys.prefix, "bin")
    if p2g_home is None:
        # assume development/editable install
        import polar2grid

        os.environ["POLAR2GRID_HOME"] = os.path.join(os.path.dirname(polar2grid.__file__), "..", "swbundle")
    tmpdir = tempfile.gettempdir()
    context.base_temp_dir = os.path.join(tmpdir, "p2g_integration_tests")

    # remove any previous test results
    if os.path.isdir(context.base_temp_dir):
        shutil.rmtree(context.base_temp_dir, ignore_errors=True)
    os.mkdir(context.base_temp_dir)


def after_all(context):
    pass
