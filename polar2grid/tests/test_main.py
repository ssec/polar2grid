#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2022 Space Science and Engineering Center (SSEC),
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
"""Tests for the __main__.py script."""

import pytest

from polar2grid.__main__ import g2g_main, p2g_main


@pytest.mark.parametrize(
    ("main_func", "exp_reader"),
    [
        (p2g_main, "viirs_sdr"),
        (g2g_main, "abi_l1b"),
    ],
)
def test_main_call(main_func, exp_reader, capsys):
    with pytest.raises(SystemExit) as e:
        main_func(["-h"])
    assert e.value.code == 0
    sout = capsys.readouterr()
    assert exp_reader in sout.out


def test_call_main_script():
    import subprocess

    subprocess.check_call(["python3", "-m", "polar2grid", "-h"])
