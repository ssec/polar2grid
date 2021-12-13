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

DTYPE_UINT8 = "uint1"
DTYPE_UINT16 = "uint2"
DTYPE_UINT32 = "uint4"
DTYPE_UINT64 = "uint8"
DTYPE_INT8 = "int1"
DTYPE_INT16 = "int2"
DTYPE_INT32 = "int4"
DTYPE_INT64 = "int8"
DTYPE_FLOAT32 = "real4"
DTYPE_FLOAT64 = "real8"

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

# Map data type to np type for conversion
str2dtype = {
    DTYPE_UINT8: np.uint8,
    DTYPE_UINT16: np.uint16,
    DTYPE_UINT32: np.uint32,
    DTYPE_UINT64: np.uint64,
    DTYPE_INT8: np.int8,
    DTYPE_INT16: np.int16,
    DTYPE_INT32: np.int32,
    DTYPE_INT64: np.int64,
    DTYPE_FLOAT32: np.float32,
    DTYPE_FLOAT64: np.float64,
}
dtype2str = dict((v, k) for k, v in str2dtype.items())

# Map data type to valid data range
# Since float32 is polar2grid's intermediate type, float32 and float64 don't
# get clipped
dtype2range = {
    DTYPE_UINT8: (0, 2 ** 8 - 1),
    DTYPE_UINT16: (0, 2 ** 16 - 1),
    DTYPE_UINT32: (0, 2 ** 32 - 1),
    DTYPE_UINT64: (0, 2 ** 64 - 1),
    DTYPE_INT8: (-1 * (2 ** 7), 2 ** 7 - 1),
    DTYPE_INT16: (-1 * (2 ** 15), 2 ** 15 - 1),
    DTYPE_INT32: (-1 * (2 ** 31), 2 ** 31 - 1),
    DTYPE_INT64: (-1 * (2 ** 63), 2 ** 63 - 1),
    DTYPE_FLOAT32: None,
    DTYPE_FLOAT64: None,
}


def normalize_dtype_string(dtype_str):
    if dtype_str in str2dtype:
        return dtype_str
    else:
        msg = "Unknown data type string '%s'" % (dtype_str,)
        log.error(msg)
        raise ValueError(msg)


def str_to_dtype(dtype_str):
    if np.issubclass_(dtype_str, np.number):
        # if they gave us a np dtype
        return dtype_str
    elif isinstance(dtype_str, str) and hasattr(np, dtype_str):
        # they gave us the np name of the dtype
        return getattr(np, dtype_str)

    try:
        return str2dtype[dtype_str]
    except KeyError:
        raise ValueError("Not a valid data type string: %s" % (dtype_str,))


def dtype_to_str(numpy_dtype):
    if isinstance(numpy_dtype, str):
        # if they gave us a string, make sure it's valid
        return normalize_dtype_string(numpy_dtype)

    try:
        return dtype2str[np.dtype(numpy_dtype).type]
    except KeyError:
        raise ValueError("Unsupported np data type: %r" % (numpy_dtype,))


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
