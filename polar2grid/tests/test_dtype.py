#!/usr/bin/env python3
# Copyright (C) 2025 Space Science and Engineering Center (SSEC),
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
"""Test dtype conversions."""

import numpy as np
import pytest

from polar2grid.core.dtype import dtype_to_str, str_to_dtype


@pytest.mark.parametrize(
    ("input_arg", "exp_str"),
    [
        (np.uint8, "uint8"),
        ("uint8", "uint8"),
        ("u1", "uint8"),
        (np.dtype("uint8"), "uint8"),
        (np.float32, "float32"),
        ("float32", "float32"),
        ("f4", "float32"),
        (np.dtype("float32"), "float32"),
        (np.float64, "float64"),
        ("float64", "float64"),
        ("f8", "float64"),
        (np.dtype("float64"), "float64"),
        (np.int8, "int8"),
        ("int8", "int8"),
        ("i1", "int8"),
        (np.dtype("int8"), "int8"),
    ],
)
def test_dtype_to_str(input_arg, exp_str):
    """Test conversion from dtype to string."""
    dtype_str = dtype_to_str(input_arg)
    assert dtype_str == exp_str


@pytest.mark.parametrize(
    ("input_arg", "exp_dtype"),
    [
        ("uint8", np.uint8),
        ("int8", np.int8),
        ("float32", np.float32),
    ],
)
def test_str_to_dtype(input_arg, exp_dtype):
    """Test conversion from string to dtype."""
    np_dtype = str_to_dtype(input_arg)
    assert np_dtype == exp_dtype
