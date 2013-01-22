#!/usr/bin/env python
# encoding: utf-8
"""
Functions that handle polar2grid data types.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3

Copyright (C) 2013 Space Science and Engineering Center (SSEC),
 University of Wisconsin-Madison.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

This file is part of the polar2grid software package. Polar2grid takes
satellite observation data, remaps it, and writes it to a file format for
input into another program.
Documentation: http://www.ssec.wisc.edu/software/polar2grid/

    Written by David Hoese    January 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

from .constants import *

import numpy

import sys

# Map data type to numpy type for conversion
dtype2np = {
        DTYPE_UINT8   : numpy.uint8,
        DTYPE_UINT16  : numpy.uint16,
        DTYPE_UINT32  : numpy.uint32,
        DTYPE_UINT64  : numpy.uint64,
        DTYPE_INT8    : numpy.int8,
        DTYPE_INT16   : numpy.int16,
        DTYPE_INT32   : numpy.int32,
        DTYPE_INT64   : numpy.int64,
        DTYPE_FLOAT32 : numpy.float32,
        DTYPE_FLOAT64 : numpy.float64
        }

# Map data type to valid data range
# Since float32 is polar2grid's intermediate type, float32 and float64 don't
# get clipped
dtype2range = {
        DTYPE_UINT8   : (0,          2**8-1 ),
        DTYPE_UINT16  : (0,          2**16-1),
        DTYPE_UINT32  : (0,          2**32-1),
        DTYPE_UINT64  : (0,          2**64-1),
        DTYPE_INT8    : (-1*(2**7),  2**7-1 ),
        DTYPE_INT16   : (-1*(2**15), 2**15-1),
        DTYPE_INT32   : (-1*(2**31), 2**31-1),
        DTYPE_INT64   : (-1*(2**63), 2**63-1),
        DTYPE_FLOAT32 : None,
        DTYPE_FLOAT64 : None
        }


# Common alternative names for the constants
str2dtype = {
        "float32" : DTYPE_FLOAT32,
        "float64" : DTYPE_FLOAT64
        }

def str_to_dtype(dtype_str):
    if dtype_str in dtype2np: return dtype_str

    if dtype_str not in str2dtype:
        msg = "Unknown data type string '%s'" % (dtype_str,)
        log.error(msg)
        raise ValueError(msg)

    return str2dtype[dtype_str]

def convert_to_data_type(data, data_type):
    """Convert a numpy array to a different data type represented by a
    polar2grid data type constant.
    """
    if data_type not in dtype2np:
        log.error("Unknown data_type '%s', don't know how to convert data" % (data_type,))
        raise ValueError("Unknown data_type '%s', don't know how to convert data" % (data_type,))

    np_type = dtype2np[data_type]
    return data.astype(np_type)

def clip_to_data_type(data, data_type):
    if data_type not in dtype2np:
        log.error("Unknown data_type '%s', don't know how to convert data" % (data_type,))
        raise ValueError("Unknown data_type '%s', don't know how to convert data" % (data_type,))

    min,max = dtype2range[data_type]
    numpy.clip(data, min, max, out=data)

    return convert_to_data_type(data, data_type)

def main():
    from pprint import pprint
    pprint(dtype2range)

if __name__ == "__main__":
    sys.exit(main())

