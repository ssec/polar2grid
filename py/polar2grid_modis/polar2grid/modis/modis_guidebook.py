#!/usr/bin/env python
# encoding: utf-8
"""
Provide information about MODIS product files for a variety of uses.

:author:       Eva Schiffer (evas)
:contact:      evas@ssec.wisc.edu
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

from polar2grid.core.constants import *
from polar2grid.core.time_utils import UTC

import sys
import re
import os
import logging

from datetime import datetime
from collections import defaultdict

LOG = logging.getLogger(__name__)
UTC = UTC()

LATITUDE_GEO_VARIABLE_NAME   = 'Latitude'
LONGITUDE_GEO_VARIABLE_NAME  = 'Longitude'

# 1KM products
VISIBLE_CH_1_VARIABLE_NAME   = 'EV_250_Aggr1km_RefSB'
VISIBLE_CH_1_VARIABLE_IDX    = 0
VISIBLE_CH_7_VARIABLE_NAME   = 'EV_500_Aggr1km_RefSB'
VISIBLE_CH_7_VARIABLE_IDX    = 4
VISIBLE_CH_26_VARIABLE_NAME  = 'EV_Band26'
VISIBLE_CH_26_VARIABLE_IDX   = None
INFRARED_CH_20_VARIABLE_NAME = 'EV_1KM_Emissive'
INFRARED_CH_20_VARIABLE_IDX  = 0
INFRARED_CH_27_VARIABLE_NAME = 'EV_1KM_Emissive'
INFRARED_CH_27_VARIABLE_IDX  = 6
INFRARED_CH_31_VARIABLE_NAME = 'EV_1KM_Emissive'
INFRARED_CH_31_VARIABLE_IDX  = 10

# 500m products
# FUTURE

# 250m products
VISIBLE_250_CH_1_VARIABLE_NAME    = 'EV_250_RefSB'
VISIBLE_250_CH_1_VARIABLE_IDX     = 0
VISIBLE_250_CH_2_VARIABLE_NAME    = 'EV_250_RefSB'
VISIBLE_250_CH_2_VARIABLE_IDX     = 1

CLOUD_MASK_NAME              = 'MODIS_Cloud_Mask'
CLOUD_MASK_IDX               = None
LAND_SEA_MASK_NAME           = 'MODIS_Simple_LandSea_Mask'
LAND_SEA_MASK_IDX            = None

SOLAR_ZENITH_ANGLE_NAME      = "SolarZenith"
SOLAR_ZENITH_ANGLE_IDX       = None

SEA_SURFACE_TEMP_NAME        = 'Sea_Surface_Temperature'
SEA_SURFACE_TEMP_IDX         = None
LAND_SURFACE_TEMP_NAME       = "LST"
LAND_SURFACE_TEMP_IDX        = None
NDVI_NAME                    = "NDVI"
NDVI_IDX                     = None

ICE_SURFACE_TEMP_NAME        = "Ice_Surface_Temperature"
ICE_SURFACE_TEMP_IDX         = None
INVERSION_STRENGTH_NAME      = "Inversion_Strength"
INVERSION_STRENGTH_IDX       = None
INVERSION_DEPTH_NAME         = "Inversion_Depth"
INVERSION_DEPTH_IDX          = None
ICE_CONCENTRATION_NAME       = "Ice_Concentration"
ICE_CONCENTRATION_IDX        = None

CLOUD_TOP_TEMP_NAME          = "Cloud_Top_Temperature"
CLOUD_TOP_TEMP_IDX           = None
TOTAL_PRECIP_WATER_NAME      = "Water_Vapor"
TOTAL_PRECIP_WATER_IDX       = None

VISIBLE_SCALE_ATTR_NAME      = "reflectance_scales"
VISIBLE_OFFSET_ATTR_NAME     = "reflectance_offsets"
INFRARED_SCALE_ATTR_NAME     = "radiance_scales"
INFRARED_OFFSET_ATTR_NAME    = "radiance_offsets"

GENERIC_SCALE_ATTR_NAME      = "scale_factor"
GENERIC_OFFSET_ATTR_NAME     = "add_offset"
GENERIC_VALID_RANGE_NAME     = "valid_range"

FILL_VALUE_ATTR_NAME         = "_FillValue"
MISSING_VALUE_ATTR_NAME      = "missing_value"

GEO_FILE_SUFFIX              = ".geo.hdf"

NAV_SETS_TO_INTERPOLATE_GEO          = [GEO_250M_NAV_UID]

# this is true for the 1km data, FUTURE: when we get to other kinds, this will need to be more sophisicated
ROWS_PER_SCAN = defaultdict(lambda: 10)
ROWS_PER_SCAN[GEO_NAV_UID]      = 10
ROWS_PER_SCAN[GEO_250M_NAV_UID] = 40

# Special values (not verified, but this is what I was told)
# these are used in reflectance band 1 and 2
SATURATION_VALUE = 65535
# if a value couldn't be aggregated from 250m/500m to 1km then we should clip those too
CANT_AGGR_VALUE  = 65528
# we only want to clip the saturation fill values for certain bands, otherwise night time becomes max valid
CLIP_SATURATION_VARIABLES = [VISIBLE_250_CH_2_VARIABLE_NAME]

# the cloud values that correspond to areas we should clear; this came from William so it's probably more right than my guessing ;)
CLOUDS_VALUES_TO_CLEAR       = [1, 2]

# a regular expression that will match files containing the visible and infrared bands
VIS_INF_FILE_PATTERN           = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.1000m\.hdf'
# a regular expression that will match files containing the 250m visible bands
VIS_250M_FILE_PATTERN          = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.250m\.hdf'
# a regular expression that will match files containing the cloud mask
CLOUD_MASK_FILE_PATTERN        = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.mask_byte1\.hdf'
# a regular expression that will match files containing sea surface temperature
SEA_SURFACE_TEMP_FILE_PATTERN  = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.mod28\.hdf'
# a regular expression that will match files containing land surface temperature
LAND_SURFACE_TEMP_FILE_PATTERN = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.modlst\.hdf'
# a regular expression that will match files containing the nav data (including lon/lat and solar zenith angle)
GEO_FILE_PATTERN               = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.geo\.hdf'
# a regular expression that will match files that have some clouds related data in them
CLOUDS_06_FILE_PATTERN         = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.mod06ct\.hdf'
# a regular file pattern that will match files taht contain total precipitable water
CLOUDS_07_FILE_PATTERN         = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.mod07\.hdf'
# a regular expression that will match files containing ice surface temperature
ICE_SURFACE_TEMP_FILE_PATTERN  = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.ist\.hdf'
# a regular expression that will match files containing several inversion products
INVERSION_FILE_PATTERN         = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.inversion\.hdf'
# a regular expression that will match files containing ice concentration
ICE_CONCENTRATION_FILE_PATTERN = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.icecon\.hdf'
# a regular expression that will match files containing NDVI data
NDVI_FILE_PATTERN              = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.ndvi\.1000m\.hdf'

BANDS_REQUIRED_TO_CALCULATE_FOG_BAND = [(BKIND_IR,  BID_20), (BKIND_IR,  BID_31), (BKIND_SZA, NOT_APPLICABLE)]

# a mapping between which navigation groups contain which data files
GEO_FILE_GROUPING = {
                      GEO_NAV_UID:      [VIS_INF_FILE_PATTERN, CLOUD_MASK_FILE_PATTERN,
                                         SEA_SURFACE_TEMP_FILE_PATTERN, LAND_SURFACE_TEMP_FILE_PATTERN, NDVI_FILE_PATTERN,
                                         ICE_SURFACE_TEMP_FILE_PATTERN, INVERSION_FILE_PATTERN, ICE_CONCENTRATION_FILE_PATTERN],
                      GEO_250M_NAV_UID: [VIS_250M_FILE_PATTERN],
                      MOD06_NAV_UID:    [CLOUDS_06_FILE_PATTERN],
                      MOD07_NAV_UID:    [CLOUDS_07_FILE_PATTERN],
                    }

# a mapping of what navigation groups required geolocation auxiliary data
# the file pattern is used in the filepaths dictionary passed to the frontend
NAV_SETS_REQUIRE_GEO = {
                      GEO_NAV_UID      : GEO_FILE_PATTERN,
                    }

# a mapping between the geo file group and the name of the fill value attribute for the longitude and latitude
# FUTURE, if the lon/lat have different fill values in the future this may need to be more complex
LON_LAT_FILL_VALUE_NAMES = \
                    {
                      GEO_NAV_UID:   FILL_VALUE_ATTR_NAME,
                      GEO_250M_NAV_UID:   FILL_VALUE_ATTR_NAME,
                      MOD06_NAV_UID: None,
                      MOD07_NAV_UID: None,
                    }

# a mapping between regular expressions to match files and their band_kind and band_id contents
FILE_CONTENTS_GUIDE = {
                        VIS_INF_FILE_PATTERN:                       {
                                                                     BKIND_VIS:   [BID_01, BID_07, BID_26],
                                                                     BKIND_IR:    [BID_20, BID_27, BID_31]
                                                                    },
                        VIS_250M_FILE_PATTERN:                      {
                                                                     BKIND_VIS:   [BID_01, BID_02]
                                                                    },
                        CLOUD_MASK_FILE_PATTERN:                    {
                                                                     BKIND_CMASK: [NOT_APPLICABLE],
                                                                     BKIND_LSMSK: [NOT_APPLICABLE],
                                                                    },
                        SEA_SURFACE_TEMP_FILE_PATTERN:              {
                                                                     BKIND_SST:   [NOT_APPLICABLE]
                                                                    },
                        LAND_SURFACE_TEMP_FILE_PATTERN:             {
                                                                     BKIND_LST:   [NOT_APPLICABLE],
                                                                     BKIND_SLST:  [NOT_APPLICABLE]
                                                                    },
                        NDVI_FILE_PATTERN:                          {
                                                                     BKIND_NDVI:  [NOT_APPLICABLE]
                                                                    },
                        GEO_FILE_PATTERN:                           {
                                                                     BKIND_SZA:   [NOT_APPLICABLE]
                                                                    },
                        ICE_SURFACE_TEMP_FILE_PATTERN:              {
                                                                     BKIND_IST:   [NOT_APPLICABLE]
                                                                    },
                        INVERSION_FILE_PATTERN:                     {
                                                                     BKIND_INV:   [NOT_APPLICABLE],
                                                                     BKIND_IND:   [NOT_APPLICABLE]
                                                                    },
                        ICE_CONCENTRATION_FILE_PATTERN:             {
                                                                     BKIND_ICON:  [NOT_APPLICABLE]
                                                                    },
                        
                        
                        CLOUDS_06_FILE_PATTERN:                     {
                                                                     BKIND_CTT:   [NOT_APPLICABLE],
                                                                    },
                        CLOUDS_07_FILE_PATTERN:                     {
                                                                     BKIND_TPW:   [NOT_APPLICABLE],
                                                                    },
                      }

# a mapping between bands and their fill value attribute names
# XXX: this may require finer grain keys, like including nav set id if things
# get complicated
FILL_VALUE_ATTR_NAMES = \
            {
              (BKIND_VIS, BID_01):           FILL_VALUE_ATTR_NAME,
              (BKIND_VIS, BID_02):           FILL_VALUE_ATTR_NAME,
              (BKIND_VIS, BID_07):           FILL_VALUE_ATTR_NAME,
              (BKIND_VIS, BID_26):           FILL_VALUE_ATTR_NAME,
              (BKIND_IR,  BID_20):           FILL_VALUE_ATTR_NAME,
              (BKIND_IR,  BID_27):           FILL_VALUE_ATTR_NAME,
              (BKIND_IR,  BID_31):           FILL_VALUE_ATTR_NAME,
              
              (BKIND_CMASK, NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
              (BKIND_LSMSK, NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
              (BKIND_SZA,   NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
              
              (BKIND_SST,   NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
              (BKIND_LST,   NOT_APPLICABLE): MISSING_VALUE_ATTR_NAME,
              (BKIND_SLST,  NOT_APPLICABLE): MISSING_VALUE_ATTR_NAME,
              (BKIND_NDVI,  NOT_APPLICABLE): None,
              
              (BKIND_IST,   NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
              (BKIND_INV,   NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
              (BKIND_IND,   NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
              (BKIND_ICON,  NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
              
              (BKIND_CTT,   NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
              (BKIND_TPW,   NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
            }

# a list of the bands that are auxiliary bands (non-image data)
AUX_BANDS = [
              (BKIND_CMASK, NOT_APPLICABLE),
              (BKIND_LSMSK, NOT_APPLICABLE),
              (BKIND_SZA,   NOT_APPLICABLE),
            ]

# a mapping between the bands and their data kinds (in the file)
DATA_KINDS = {
              (BKIND_VIS, BID_01): DKIND_REFLECTANCE,
              (BKIND_VIS, BID_02): DKIND_REFLECTANCE,
              (BKIND_VIS, BID_07): DKIND_REFLECTANCE,
              (BKIND_VIS, BID_26): DKIND_REFLECTANCE,
              (BKIND_IR,  BID_20): DKIND_RADIANCE,
              (BKIND_IR,  BID_27): DKIND_RADIANCE,
              (BKIND_IR,  BID_31): DKIND_RADIANCE,
              
              (BKIND_CMASK, NOT_APPLICABLE): DKIND_CATEGORY,
              (BKIND_LSMSK, NOT_APPLICABLE): DKIND_CATEGORY,
              (BKIND_SZA,   NOT_APPLICABLE): DKIND_ANGLE,
              
              (BKIND_SST,   NOT_APPLICABLE): DKIND_BTEMP,
              (BKIND_LST,   NOT_APPLICABLE): DKIND_BTEMP,
              (BKIND_SLST,  NOT_APPLICABLE): DKIND_BTEMP,
              (BKIND_NDVI,  NOT_APPLICABLE): DKIND_C_INDEX,
              
              (BKIND_IST,   NOT_APPLICABLE): DKIND_BTEMP,
              (BKIND_INV,   NOT_APPLICABLE): DKIND_BTEMP,
              (BKIND_IND,   NOT_APPLICABLE): DKIND_DISTANCE,
              (BKIND_ICON,  NOT_APPLICABLE): DKIND_PERCENT,
              
              (BKIND_CTT,   NOT_APPLICABLE): DKIND_BTEMP,
              (BKIND_TPW,   NOT_APPLICABLE): DKIND_DISTANCE,
             }

# a mapping between the bands and the variable names used in the files to hold them
VAR_NAMES  = {
            VIS_INF_FILE_PATTERN:           {
                                             (BKIND_IR,  BID_20): INFRARED_CH_20_VARIABLE_NAME,
                                             (BKIND_IR,  BID_27): INFRARED_CH_27_VARIABLE_NAME,
                                             (BKIND_IR,  BID_31): INFRARED_CH_31_VARIABLE_NAME,
                                             (BKIND_VIS, BID_01): VISIBLE_CH_1_VARIABLE_NAME,
                                             (BKIND_VIS, BID_07): VISIBLE_CH_7_VARIABLE_NAME,
                                             (BKIND_VIS, BID_26): VISIBLE_CH_26_VARIABLE_NAME,
                                            },
            CLOUD_MASK_FILE_PATTERN:        {
                                             (BKIND_CMASK, NOT_APPLICABLE): CLOUD_MASK_NAME,
                                             (BKIND_LSMSK, NOT_APPLICABLE): LAND_SEA_MASK_NAME,
                                            },
            SEA_SURFACE_TEMP_FILE_PATTERN:  {
                                             (BKIND_SST,   NOT_APPLICABLE): SEA_SURFACE_TEMP_NAME,
                                            },
            LAND_SURFACE_TEMP_FILE_PATTERN: {
                                             (BKIND_LST,   NOT_APPLICABLE): LAND_SURFACE_TEMP_NAME,
                                             (BKIND_SLST,  NOT_APPLICABLE): LAND_SURFACE_TEMP_NAME,
                                            },
            NDVI_FILE_PATTERN:              {
                                             (BKIND_NDVI,  NOT_APPLICABLE): NDVI_NAME,
                                            },
            GEO_FILE_PATTERN:               {
                                             (BKIND_SZA,   NOT_APPLICABLE): SOLAR_ZENITH_ANGLE_NAME,
                                            },
            ICE_SURFACE_TEMP_FILE_PATTERN:  {
                                             (BKIND_IST,   NOT_APPLICABLE): ICE_SURFACE_TEMP_NAME,
                                            },
            INVERSION_FILE_PATTERN:         {
                                             (BKIND_INV,   NOT_APPLICABLE): INVERSION_STRENGTH_NAME,
                                             (BKIND_IND,   NOT_APPLICABLE): INVERSION_DEPTH_NAME,
                                            },
            ICE_CONCENTRATION_FILE_PATTERN: {
                                             (BKIND_ICON,  NOT_APPLICABLE): ICE_CONCENTRATION_NAME,
                                            },
            CLOUDS_06_FILE_PATTERN:         {
                                             (BKIND_CTT,   NOT_APPLICABLE): CLOUD_TOP_TEMP_NAME,
                                            },
            CLOUDS_07_FILE_PATTERN:         {
                                             (BKIND_TPW,   NOT_APPLICABLE): TOTAL_PRECIP_WATER_NAME,
                                            },
            VIS_250M_FILE_PATTERN:          {
                                             (BKIND_VIS, BID_01): VISIBLE_250_CH_1_VARIABLE_NAME,
                                             (BKIND_VIS, BID_02): VISIBLE_250_CH_2_VARIABLE_NAME,
                                            },
            }


# a mapping between the bands and any index needed to access the data in the variable (for slicing)
# if no slicing is needed the index will be None
VAR_IDX    = {
            VIS_INF_FILE_PATTERN:           {
                                             (BKIND_IR,  BID_20): INFRARED_CH_20_VARIABLE_IDX,
                                             (BKIND_IR,  BID_27): INFRARED_CH_27_VARIABLE_IDX,
                                             (BKIND_IR,  BID_31): INFRARED_CH_31_VARIABLE_IDX,
                                             (BKIND_VIS, BID_01): VISIBLE_CH_1_VARIABLE_IDX,
                                             (BKIND_VIS, BID_07): VISIBLE_CH_7_VARIABLE_IDX,
                                             (BKIND_VIS, BID_26): VISIBLE_CH_26_VARIABLE_IDX,
                                            },
            CLOUD_MASK_FILE_PATTERN:        {
                                             (BKIND_CMASK, NOT_APPLICABLE): CLOUD_MASK_IDX,
                                             (BKIND_LSMSK, NOT_APPLICABLE): LAND_SEA_MASK_IDX,
                                            },
            SEA_SURFACE_TEMP_FILE_PATTERN:  {
                                             (BKIND_SST,   NOT_APPLICABLE): SEA_SURFACE_TEMP_IDX,
                                            },
            LAND_SURFACE_TEMP_FILE_PATTERN: {
                                             (BKIND_LST,   NOT_APPLICABLE): LAND_SURFACE_TEMP_IDX,
                                             (BKIND_SLST,  NOT_APPLICABLE): LAND_SURFACE_TEMP_IDX,
                                            },
            NDVI_FILE_PATTERN:              {
                                             (BKIND_NDVI,  NOT_APPLICABLE): NDVI_IDX,
                                            },
            GEO_FILE_PATTERN:               {
                                             (BKIND_SZA,   NOT_APPLICABLE): SOLAR_ZENITH_ANGLE_IDX,
                                            },
            ICE_SURFACE_TEMP_FILE_PATTERN:  {
                                             (BKIND_IST,   NOT_APPLICABLE): ICE_SURFACE_TEMP_IDX,
                                            },
            INVERSION_FILE_PATTERN:         {
                                             (BKIND_INV,   NOT_APPLICABLE): INVERSION_STRENGTH_IDX,
                                             (BKIND_IND,   NOT_APPLICABLE): INVERSION_DEPTH_IDX,
                                            },
            ICE_CONCENTRATION_FILE_PATTERN: {
                                             (BKIND_ICON,  NOT_APPLICABLE): ICE_CONCENTRATION_IDX,
                                            },
            CLOUDS_06_FILE_PATTERN:         {
                                             (BKIND_CTT,   NOT_APPLICABLE): CLOUD_TOP_TEMP_IDX,
                                            },
            CLOUDS_07_FILE_PATTERN:         {
                                             (BKIND_TPW,   NOT_APPLICABLE): TOTAL_PRECIP_WATER_IDX,
                                            },
            VIS_250M_FILE_PATTERN:          {
                                             (BKIND_VIS, BID_01): VISIBLE_250_CH_1_VARIABLE_IDX,
                                             (BKIND_VIS, BID_02): VISIBLE_250_CH_2_VARIABLE_IDX,
                                            },
        }

# a mapping between bands and the names of their scale and offset attributes
RESCALING_ATTRS = \
             {
              (BKIND_VIS, BID_01): (VISIBLE_SCALE_ATTR_NAME,  VISIBLE_OFFSET_ATTR_NAME),
              (BKIND_VIS, BID_02): (VISIBLE_SCALE_ATTR_NAME,  VISIBLE_OFFSET_ATTR_NAME),
              (BKIND_VIS, BID_07): (VISIBLE_SCALE_ATTR_NAME,  VISIBLE_OFFSET_ATTR_NAME),
              (BKIND_VIS, BID_26): (VISIBLE_SCALE_ATTR_NAME,  VISIBLE_OFFSET_ATTR_NAME),
              (BKIND_IR,  BID_20): (INFRARED_SCALE_ATTR_NAME, INFRARED_OFFSET_ATTR_NAME),
              (BKIND_IR,  BID_27): (INFRARED_SCALE_ATTR_NAME, INFRARED_OFFSET_ATTR_NAME),
              (BKIND_IR,  BID_31): (INFRARED_SCALE_ATTR_NAME, INFRARED_OFFSET_ATTR_NAME),
              
              (BKIND_CMASK, NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
              (BKIND_LSMSK, NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
              (BKIND_SZA,   NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, None),
              
              (BKIND_SST,   NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
              (BKIND_LST,   NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, None),
              (BKIND_SLST,  NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, None),
              (BKIND_NDVI,  NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
              
              (BKIND_IST,   NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
              (BKIND_INV,   NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
              (BKIND_IND,   NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
              (BKIND_ICON,  NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
              
              (BKIND_CTT,   NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
              (BKIND_TPW,   NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
             }

# a mapping between bands and the names of their valid range attributes
# None means there is no valid range attribute
VALID_RANGE_ATTR_NAMES = \
             {
              (BKIND_VIS, BID_01): GENERIC_VALID_RANGE_NAME,
              (BKIND_VIS, BID_02): GENERIC_VALID_RANGE_NAME,
              (BKIND_VIS, BID_03): GENERIC_VALID_RANGE_NAME,
              (BKIND_VIS, BID_07): GENERIC_VALID_RANGE_NAME,
              (BKIND_VIS, BID_26): GENERIC_VALID_RANGE_NAME,
              (BKIND_IR,  BID_20): GENERIC_VALID_RANGE_NAME,
              (BKIND_IR,  BID_27): GENERIC_VALID_RANGE_NAME,
              (BKIND_IR,  BID_31): GENERIC_VALID_RANGE_NAME,
              
              (BKIND_CMASK, NOT_APPLICABLE): GENERIC_VALID_RANGE_NAME,
              (BKIND_LSMSK, NOT_APPLICABLE): GENERIC_VALID_RANGE_NAME,
              (BKIND_SZA,   NOT_APPLICABLE): GENERIC_VALID_RANGE_NAME,
              
              (BKIND_SST,   NOT_APPLICABLE): None,
              (BKIND_LST,   NOT_APPLICABLE): None,
              (BKIND_SLST,  NOT_APPLICABLE): None,
              (BKIND_NDVI,  NOT_APPLICABLE): None,
              
              (BKIND_IST,   NOT_APPLICABLE): GENERIC_VALID_RANGE_NAME,
              (BKIND_INV,   NOT_APPLICABLE): GENERIC_VALID_RANGE_NAME,
              (BKIND_IND,   NOT_APPLICABLE): GENERIC_VALID_RANGE_NAME,
              (BKIND_ICON,  NOT_APPLICABLE): GENERIC_VALID_RANGE_NAME,
              
              (BKIND_CTT,   NOT_APPLICABLE): GENERIC_VALID_RANGE_NAME,
              (BKIND_TPW,   NOT_APPLICABLE): GENERIC_VALID_RANGE_NAME,
             }

# whether or not each band should be cloud cleared
IS_CLOUD_CLEARED = \
             {
              (BKIND_VIS, BID_01): False,
              (BKIND_VIS, BID_02): False,
              (BKIND_VIS, BID_07): False,
              (BKIND_VIS, BID_26): False,
              (BKIND_IR,  BID_20): False,
              (BKIND_IR,  BID_27): False,
              (BKIND_IR,  BID_31): False,
              
              (BKIND_CMASK, NOT_APPLICABLE): False,
              (BKIND_LSMSK, NOT_APPLICABLE): False,
              (BKIND_SZA,   NOT_APPLICABLE): False,
              
              (BKIND_SST,   NOT_APPLICABLE): True,
              (BKIND_LST,   NOT_APPLICABLE): True,
              (BKIND_SLST,  NOT_APPLICABLE): True,
              (BKIND_NDVI,  NOT_APPLICABLE): True,
              
              (BKIND_IST,   NOT_APPLICABLE): False,
              (BKIND_INV,   NOT_APPLICABLE): False,
              (BKIND_IND,   NOT_APPLICABLE): False,
              (BKIND_ICON,  NOT_APPLICABLE): False,
              
              (BKIND_CTT,   NOT_APPLICABLE): False,
              (BKIND_TPW,   NOT_APPLICABLE): False,
             }

# whether or not each band should be converted to brightness temperature
SHOULD_CONVERT_TO_BT = \
             {
              (BKIND_VIS, BID_01): False,
              (BKIND_VIS, BID_02): False,
              (BKIND_VIS, BID_07): False,
              (BKIND_VIS, BID_26): False,
              (BKIND_IR,  BID_20): True,
              (BKIND_IR,  BID_27): True,
              (BKIND_IR,  BID_31): True,
              
              (BKIND_CMASK, NOT_APPLICABLE): False,
              (BKIND_LSMSK, NOT_APPLICABLE): False,
              (BKIND_SZA,   NOT_APPLICABLE): False,
              
              (BKIND_SST,   NOT_APPLICABLE): False,
              (BKIND_LST,   NOT_APPLICABLE): False,
              (BKIND_SLST,  NOT_APPLICABLE): False,
              (BKIND_NDVI,  NOT_APPLICABLE): False,
              
              (BKIND_IST,   NOT_APPLICABLE): False,
              (BKIND_INV,   NOT_APPLICABLE): False,
              (BKIND_IND,   NOT_APPLICABLE): False,
              (BKIND_ICON,  NOT_APPLICABLE): False,
              
              (BKIND_CTT,   NOT_APPLICABLE): False,
              (BKIND_TPW,   NOT_APPLICABLE): False,
             }

# a list land sea mask values to keep when clearing or None if
# that variable's data won't be cleared using this mask
CLEAR_ALL_LANDSEA_VALUES_EXCEPT = \
             {
              (BKIND_VIS, BID_01): None,
              (BKIND_VIS, BID_02): None,
              (BKIND_VIS, BID_07): None,
              (BKIND_VIS, BID_26): None,
              (BKIND_IR,  BID_20): None,
              (BKIND_IR,  BID_27): None,
              (BKIND_IR,  BID_31): None,
              
              (BKIND_CMASK, NOT_APPLICABLE): None,
              (BKIND_LSMSK, NOT_APPLICABLE): None,
              (BKIND_SZA,   NOT_APPLICABLE): None,
              
              (BKIND_SST,   NOT_APPLICABLE): [1, 2],
              (BKIND_LST,   NOT_APPLICABLE): [2, 3, 4],
              (BKIND_SLST,  NOT_APPLICABLE): [2, 3, 4],
              (BKIND_NDVI,  NOT_APPLICABLE): [2, 3, 4],
              
              (BKIND_IST,   NOT_APPLICABLE): None,
              (BKIND_INV,   NOT_APPLICABLE): None,
              (BKIND_IND,   NOT_APPLICABLE): None,
              (BKIND_ICON,  NOT_APPLICABLE): None,
              
              (BKIND_CTT,   NOT_APPLICABLE): None,
              (BKIND_TPW,   NOT_APPLICABLE): None,
             }

def parse_datetime_from_filename (file_name_string) :
    """parse the given file_name_string and create an appropriate datetime object
    that represents the datetime indicated by the file name; if the file name does
    not represent a pattern that is understood as a MODIS file, None will be returned
    """
    
    datetime_to_return = None
    
    # there are at least two file name formats to parse here
    if (file_name_string.startswith('a1') or file_name_string.startswith('t1')) :
        temp = file_name_string.split('.')
        datetime_to_return = datetime.strptime(temp[1] + temp[2], "%y%j%H%M").replace(tzinfo=UTC)
    
    return datetime_to_return

def get_satellite_from_filename (data_file_name_string) :
    """given a file name, figure out which satellite it's from
    if the file does not represent a known MODIS satellite name
    configuration None will be returned
    """
    
    satellite_to_return = None
    
    if   data_file_name_string.find("Aqua")  >= 0 or data_file_name_string.find("a1") == 0 :
        satellite_to_return = SAT_AQUA
    elif data_file_name_string.find("Terra") >= 0 or data_file_name_string.find("t1") == 0 :
        satellite_to_return = SAT_TERRA
    
    return satellite_to_return

def get_equivalent_geolocation_filename (data_file_name_string) :
    """given the name of a MODIS file, figure out the expected
    name for it's equivalent geolocation file; no checks into
    the existence or formatting of the geolocation file are made,
    this is just the name of the theoretical file where we would
    expect to find the geolocation for the given data file; if
    the given file name is not a pattern we understand as a MODIS
    file, None will be returned
    """
    
    filename_to_return = None
    
    # file correspondances are handled here, but clumbsily; FUTURE make a better reverse index to handle this
    
    if   re.match(VIS_INF_FILE_PATTERN,           data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.1000m.hdf'     )[0] + GEO_FILE_SUFFIX
    elif re.match(VIS_250M_FILE_PATTERN,           data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.250m.hdf'      )[0] + GEO_FILE_SUFFIX
    elif re.match(CLOUD_MASK_FILE_PATTERN,        data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.mask_byte1.hdf')[0] + GEO_FILE_SUFFIX
    elif re.match(SEA_SURFACE_TEMP_FILE_PATTERN,  data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.mod28.hdf'     )[0] + GEO_FILE_SUFFIX
    elif re.match(LAND_SURFACE_TEMP_FILE_PATTERN, data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.modlst.hdf'    )[0] + GEO_FILE_SUFFIX
    elif re.match(GEO_FILE_PATTERN,               data_file_name_string) is not None :
        filename_to_return = data_file_name_string
    elif re.match(CLOUDS_06_FILE_PATTERN,         data_file_name_string) is not None :
        filename_to_return = data_file_name_string
    elif re.match(CLOUDS_07_FILE_PATTERN,         data_file_name_string) is not None :
        filename_to_return = data_file_name_string
    elif re.match(ICE_SURFACE_TEMP_FILE_PATTERN,  data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.ist.hdf'       )[0] + GEO_FILE_SUFFIX
    elif re.match(ICE_CONCENTRATION_FILE_PATTERN, data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.icecon.hdf'    )[0] + GEO_FILE_SUFFIX
    elif re.match(INVERSION_FILE_PATTERN,         data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.inversion.hdf' )[0] + GEO_FILE_SUFFIX
    elif re.match(NDVI_FILE_PATTERN,              data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.ndvi.1000m.hdf')[0] + GEO_FILE_SUFFIX
    
    return filename_to_return

def sort_files_by_nav_uid (filepaths) :
    """
    given a list of filepaths, sort them into a dictionary by the nav sets they belong to
    """
    
    # some useful data structures
    nav_file_type_sets = defaultdict(dict) # this will be our return sorted dictionary
    
    # for each of the possible navigation sets
    for nav_group_uid in GEO_FILE_GROUPING.keys() :
        # for each file pattern that uses that navigation set
        for file_pattern in GEO_FILE_GROUPING[nav_group_uid] :
            # add the files matching that pattern to the appropriate set (ignore any that don't match)
            nav_file_type_sets[nav_group_uid][file_pattern] = set([ ]) if file_pattern not in nav_file_type_sets[nav_group_uid] else nav_file_type_sets[nav_group_uid][file_pattern]
            nav_file_type_sets[nav_group_uid][file_pattern].update(set([ x for x in filepaths if re.match(file_pattern, os.path.split(x)[-1]) ]))
    
    # removing empty nav patterns
    for nav_group_uid in nav_file_type_sets.keys() :
        for file_pattern in nav_file_type_sets[nav_group_uid].keys() :
            if not nav_file_type_sets[nav_group_uid][file_pattern] :
                LOG.debug("Removing empty file pattern '%s':'%s'" % (nav_group_uid, file_pattern))
                del nav_file_type_sets[nav_group_uid][file_pattern]
            else :
                # if there is stuff in this nav group / file pattern, make it into a list instead of a set
                nav_file_type_sets[nav_group_uid][file_pattern] = list(nav_file_type_sets[nav_group_uid][file_pattern])
        
        # if the entire nav pattern has no matches
        if not nav_file_type_sets[nav_group_uid] :
            LOG.debug("Removing empty nav file set '%s'" % (nav_group_uid,))
            del nav_file_type_sets[nav_group_uid]
    
    # add navigation file patterns (if needed)
    for nav_group_uid in nav_file_type_sets.keys():
        # does this nav set need geonavigation aux. data?
        if nav_group_uid not in NAV_SETS_REQUIRE_GEO:
            continue

        # get a band representative to get the corresponding geo filename
        file_pattern = nav_file_type_sets[nav_group_uid].keys()[0]
        file_paths_for_pattern = nav_file_type_sets[nav_group_uid][file_pattern]
        # add navigation file pattern to the dictionary
        geo_file_pattern = NAV_SETS_REQUIRE_GEO[nav_group_uid]
        nav_file_type_sets[nav_group_uid][geo_file_pattern] = set([ ])

        # get the geolocation filepath for each data filepath
        for fp in file_paths_for_pattern:
            base_dir,fn = os.path.split(fp)
            geo_path = os.path.join( base_dir, get_equivalent_geolocation_filename(fn) )
            LOG.debug("Adding geolocation file '%s'" % (geo_path,))
            nav_file_type_sets[nav_group_uid][geo_file_pattern].update([geo_path])

        # turn the set into a list
        nav_file_type_sets[nav_group_uid][geo_file_pattern] = list(nav_file_type_sets[nav_group_uid][geo_file_pattern])

    return nav_file_type_sets


def main():
    import optparse
    from pprint import pprint
    usage = """
%prog [options] filename1.hdf

"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
            help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_option('-r', '--no-read', dest='read_hdf', action='store_false', default=True,
            help="don't read or look for the hdf file, only analyze the filename")
    (options, args) = parser.parse_args()
    
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])
    
    LOG.info("Currently no command line tests are set up for this module.")
    
    """
    if not args:
        parser.error( 'must specify 1 filename, try -h or --help.' )
        return -1
    
    for fn in args:
        try:
            finfo = generic_info(fn)
        except:
            LOG.error("Failed to get info from filename '%s'" % fn, exc_info=1)
            continue
    
        if options.read_h5:
            generic_read(fn, finfo)
            pprint(finfo)
            if finfo["data_kind"] == K_RADIANCE:
                data_shape = str(finfo["data"].shape)
                print "Got Radiance with shape %s" % data_shape
            elif finfo["data_kind"] == K_REFLECTANCE:
                data_shape = str(finfo["data"].shape)
                print "Got Reflectance with shape %s" % data_shape
            elif finfo["data_kind"] == K_BTEMP:
                data_shape = str(finfo["data"].shape)
                print "Got Brightness Temperature with shape %s" % data_shape
            else:
                data_shape = "Unknown data type"
                print "Got %s" % data_shape
            mask_shape = str(finfo["mask"].shape)
            print "Mask was created with shape %s" % mask_shape
        else:
            pprint(finfo)
    
    """

if __name__ == '__main__':
    sys.exit(main())
