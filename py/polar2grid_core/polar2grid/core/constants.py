#!/usr/bin/env python
# encoding: utf-8
"""Module to store all constants.  Any constant needed in more than one
component, or potentially more than one part, of polar2grid should be
defined here.

Rules/Preferences:
    - All values lowercase
    - strings
    - user-legible (assume that they may be printed in log messages)
    - use == for comparison (not 'is' or 'not' or other)

Possible confusions:
    The VIIRS fog product created by polar2grid is a temperature difference of
    2 I bands.  It is classified as an I band for this reason, meaning the
    band is "fog", not the usual number.

Exceptions:
    - Return status constants are not strings so that they can be or'ed and
        can be interpreted by a command line shell.

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

NOT_APPLICABLE = None

# Satellites
SAT_NPP = "npp"

# Instruments
INST_VIIRS = "viirs"

# Band Kinds
BKIND_I = "i"
BKIND_M = "m"
BKIND_DNB = "dnb"

# Band Identifier
BID_01 = "01"
BID_02 = "02"
BID_03 = "03"
BID_04 = "04"
BID_05 = "05"
BID_06 = "06"
BID_07 = "07"
BID_08 = "08"
BID_09 = "09"
BID_10 = "10"
BID_11 = "11"
BID_12 = "12"
BID_13 = "13"
BID_14 = "14"
BID_15 = "15"
BID_16 = "16"
BID_FOG = "fog"
BID_NEW = "new"

# Data kinds
DKIND_LATITUDE = "latitude"
DKIND_LONGITUDE = "longitude"
DKIND_RADIANCE = "radiance"
DKIND_REFLECTANCE = "reflectance"
DKIND_BTEMP = "btemp"
DKIND_FOG = "fog"
SET_DKINDS = set([
    DKIND_RADIANCE,
    DKIND_REFLECTANCE,
    DKIND_BTEMP,
    DKIND_FOG
    ])

# Data types (int,float,#bits,etc.)
DTYPE_UINT8   = "uint1"
DTYPE_UINT16  = "uint2"
DTYPE_UINT32  = "uint4"
DTYPE_UINT64  = "uint8"
DTYPE_INT8    = "int1"
DTYPE_INT16   = "int2"
DTYPE_INT32   = "int4"
DTYPE_INT64   = "int8"
DTYPE_FLOAT32 = "real4"
DTYPE_FLOAT64 = "real8"

# Grid Constants
GRIDS_ANY = "any_grid"
GRIDS_ANY_GPD = "any_gpd_grid"
GRIDS_ANY_PROJ4 = "any_proj4_grid"
GRID_KIND_GPD = "gpd"
GRID_KIND_PROJ4 = "proj4"

### Return Status Values ###
STATUS_SUCCESS       = 0
# the frontend failed
STATUS_FRONTEND_FAIL = 1
# the backend failed
STATUS_BACKEND_FAIL  = 2
# either ll2cr or fornav failed (4 + 8)
STATUS_REMAP_FAIL    = 12
# ll2cr failed
STATUS_LL2CR_FAIL    = 4
# fornav failed
STATUS_FORNAV_FAIL   = 8
# grid determination or grid jobs creation failed
STATUS_GDETER_FAIL   = 16
# not sure why we failed, not an expected failure
STATUS_UNKNOWN_FAIL  = -1

# Other
DEFAULT_FILL_VALUE=-999.0

