#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
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
"""Functions that handle polar2grid data types."""

import logging

import numpy as np

log = logging.getLogger(__name__)

NUMPY_DTYPE_STRS = [
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "int8",
    "int16",
    "int32",
    "int64",
    "float32",
    "float64",
]


def str_to_dtype(dtype_str: str) -> np.dtype:
    try:
        return getattr(np, dtype_str)
    except AttributeError:
        raise ValueError("Not a valid data type string: %s" % (dtype_str,)) from err


def dtype_to_str(numpy_dtype: np.dtype | str) -> str:
    if isinstance(numpy_dtype, str) or not hasattr(numpy_dtype, "name"):
        numpy_dtype = np.dtype(numpy_dtype)

    try:
        return numpy_dtype.name
    except KeyError as err:
        raise ValueError("Unsupported numpy data type: %r" % (numpy_dtype,)) from err


def clip_to_data_type(data, data_type):
    if np.issubdtype(np.dtype(data_type), np.floating):
        return data
    info = np.iinfo(data_type)
    rmin = info.min
    rmax = info.max
    log.debug("Clipping data to a %d - %d data range" % (rmin, rmax))
    return data.clip(rmin, rmax)


def int_or_float(val):
    """Convert a string to integer or float.

    If we can't make it an integer then make it a float.

    """
    try:
        return int(val)
    except ValueError:
        return float(val)
