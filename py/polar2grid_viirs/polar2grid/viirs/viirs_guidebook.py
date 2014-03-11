#!/usr/bin/env python
# encoding: utf-8
"""
Provide information about ADL product files for a variety of uses.

:author:       David Hoese (davidh)
:author:       Ray Garcia (rayg)
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

from polar2grid.core import UTC
from polar2grid.core.constants import *
import h5py as h5
import numpy as np

import sys, os
import re
import logging
from glob import glob
from datetime import datetime,timedelta

log = logging.getLogger(__name__)
UTC= UTC()

K_LATITUDE             = "LatitudeVar"
K_LONGITUDE            = "LongitudeVar"
K_RADIANCE             = "RadianceVar"
K_REFLECTANCE          = "ReflectanceVar"
K_BTEMP                = "BrightnessTemperatureVar"
K_SOLARZENITH          = "SolarZenithVar"
K_LUNARZENITH          = "LunarZenithVar"
K_MOONILLUM            = "LunarIllumination"
K_ALTITUDE             = "AltitudeVar"
K_RADIANCE_FACTORS     = "RadianceFactorsVar"
K_REFLECTANCE_FACTORS  = "ReflectanceFactorsVar"
K_BTEMP_FACTORS        = "BrightnessTemperatureFactorsVar"
K_STARTTIME            = "StartTimeVar"
K_AGGR_STARTTIME       = "AggrStartTimeVar"
K_AGGR_STARTDATE       = "AggrStartDateVar"
K_AGGR_ENDTIME         = "AggrEndTimeVar"
K_AGGR_ENDDATE         = "AggrEndDateVar"
K_MODESCAN             = "ModeScanVar"
K_MODEGRAN             = "ModeGranVar"
K_QF3                  = "QF3Var"
K_LAT_G_RING           = "LatGRingAttr"
K_LON_G_RING           = "LonGRingAttr"
K_WEST_COORD           = "WestCoordinateAttr"
K_EAST_COORD           = "EastCoordinateAttr"
K_NORTH_COORD          = "NorthCoordinateAttr"
K_SOUTH_COORD          = "SouthCoordinateAttr"
K_NAVIGATION           = "NavigationFilenameGlob"  # glob to search for to find navigation file that corresponds
K_GEO_REF              = "CdfcbGeolocationFileGlob" # glob which would match the N_GEO_Ref attribute

NAV_SET_GUIDE = {
        BKIND_M   : MBAND_NAV_UID,
        BKIND_I   : IBAND_NAV_UID,
        BKIND_DNB : DNB_NAV_UID,
        }

# Non-TC vs Terrain Corrected
GEO_GUIDE = {
        BKIND_M : ('GMODO','GMTCO'),
        BKIND_I : ('GIMGO','GITCO'),
        BKIND_DNB : ('GDNBO','GDNBO'),
        }

FACTORS_GUIDE = {
        DKIND_REFLECTANCE : K_REFLECTANCE_FACTORS,
        DKIND_RADIANCE    : K_RADIANCE_FACTORS,
        DKIND_BTEMP       : K_BTEMP_FACTORS
        }

GEO_FILE_GUIDE = {
            r'GITCO.*' : {
                            K_LATITUDE:    '/All_Data/VIIRS-IMG-GEO-TC_All/Latitude',
                            K_LONGITUDE:   '/All_Data/VIIRS-IMG-GEO-TC_All/Longitude',
                            K_ALTITUDE:    '/All_Data/VIIRS-IMG-GEO-TC_All/Height',
                            K_STARTTIME:   '/All_Data/VIIRS-IMG-GEO-TC_All/StartTime',
                            K_AGGR_STARTTIME: '/Data_Products/VIIRS-IMG-GEO-TC/VIIRS-IMG-GEO-TC_Aggr.AggregateBeginningTime',
                            K_AGGR_STARTDATE: '/Data_Products/VIIRS-IMG-GEO-TC/VIIRS-IMG-GEO-TC_Aggr.AggregateBeginningDate',
                            K_AGGR_ENDTIME: '/Data_Products/VIIRS-IMG-GEO-TC/VIIRS-IMG-GEO-TC_Aggr.AggregateEndingTime',
                            K_AGGR_ENDDATE: '/Data_Products/VIIRS-IMG-GEO-TC/VIIRS-IMG-GEO-TC_Aggr.AggregateEndingDate',
                            K_SOLARZENITH: '/All_Data/VIIRS-IMG-GEO-TC_All/SolarZenithAngle',
                            K_LUNARZENITH: '/All_Data/VIIRS-IMG-GEO-TC_All/LunarZenithAngle',
                            K_MOONILLUM:   '/All_Data/VIIRS-IMG-GEO-TC_All/MoonIllumFraction',
                            K_LAT_G_RING:  '/Data_Products/VIIRS-IMG-GEO-TC/VIIRS-IMG-GEO-TC_Gran_0.G-Ring_Latitude',
                            K_LON_G_RING:  '/Data_Products/VIIRS-IMG-GEO-TC/VIIRS-IMG-GEO-TC_Gran_0.G-Ring_Longitude',
                            K_WEST_COORD:  '/Data_Products/VIIRS-IMG-GEO-TC/VIIRS-IMG-GEO-TC_Gran_0.West_Bounding_Coordinate',
                            K_EAST_COORD:  '/Data_Products/VIIRS-IMG-GEO-TC/VIIRS-IMG-GEO-TC_Gran_0.East_Bounding_Coordinate',
                            K_NORTH_COORD: '/Data_Products/VIIRS-IMG-GEO-TC/VIIRS-IMG-GEO-TC_Gran_0.North_Bounding_Coordinate',
                            K_SOUTH_COORD: '/Data_Products/VIIRS-IMG-GEO-TC/VIIRS-IMG-GEO-TC_Gran_0.South_Bounding_Coordinate',
                            },
            r'GIMGO.*' : {
                            K_LATITUDE:    '/All_Data/VIIRS-IMG-GEO_All/Latitude',
                            K_LONGITUDE:   '/All_Data/VIIRS-IMG-GEO_All/Longitude',
                            K_ALTITUDE:    '/All_Data/VIIRS-IMG-GEO_All/Height',
                            K_STARTTIME:   '/All_Data/VIIRS-IMG-GEO_All/StartTime',
                            K_AGGR_STARTTIME: '/Data_Products/VIIRS-IMG-GEO/VIIRS-IMG-GEO_Aggr.AggregateBeginningTime',
                            K_AGGR_STARTDATE: '/Data_Products/VIIRS-IMG-GEO/VIIRS-IMG-GEO_Aggr.AggregateBeginningDate',
                            K_AGGR_ENDTIME: '/Data_Products/VIIRS-IMG-GEO/VIIRS-IMG-GEO_Aggr.AggregateEndingTime',
                            K_AGGR_ENDDATE: '/Data_Products/VIIRS-IMG-GEO/VIIRS-IMG-GEO_Aggr.AggregateEndingDate',
                            K_SOLARZENITH: '/All_Data/VIIRS-IMG-GEO_All/SolarZenithAngle',
                            K_LUNARZENITH: '/All_Data/VIIRS-IMG-GEO_All/LunarZenithAngle',
                            K_MOONILLUM:   '/All_Data/VIIRS-IMG-GEO_All/MoonIllumFraction',
                            K_LAT_G_RING:  '/Data_Products/VIIRS-IMG-GEO/VIIRS-IMG-GEO_Gran_0.G-Ring_Latitude',
                            K_LON_G_RING:  '/Data_Products/VIIRS-IMG-GEO/VIIRS-IMG-GEO_Gran_0.G-Ring_Longitude',
                            K_WEST_COORD:  '/Data_Products/VIIRS-IMG-GEO/VIIRS-IMG-GEO_Gran_0.West_Bounding_Coordinate',
                            K_EAST_COORD:  '/Data_Products/VIIRS-IMG-GEO/VIIRS-IMG-GEO_Gran_0.East_Bounding_Coordinate',
                            K_NORTH_COORD: '/Data_Products/VIIRS-IMG-GEO/VIIRS-IMG-GEO_Gran_0.North_Bounding_Coordinate',
                            K_SOUTH_COORD: '/Data_Products/VIIRS-IMG-GEO/VIIRS-IMG-GEO_Gran_0.South_Bounding_Coordinate',
                            },
            r'GMTCO.*' : {
                            K_LATITUDE:    '/All_Data/VIIRS-MOD-GEO-TC_All/Latitude',
                            K_LONGITUDE:   '/All_Data/VIIRS-MOD-GEO-TC_All/Longitude',
                            K_ALTITUDE:    '/All_Data/VIIRS-MOD-GEO-TC_All/Height',
                            K_STARTTIME:   '/All_Data/VIIRS-MOD-GEO-TC_All/StartTime',
                            K_AGGR_STARTTIME: '/Data_Products/VIIRS-MOD-GEO-TC/VIIRS-MOD-GEO-TC_Aggr.AggregateBeginningTime',
                            K_AGGR_STARTDATE: '/Data_Products/VIIRS-MOD-GEO-TC/VIIRS-MOD-GEO-TC_Aggr.AggregateBeginningDate',
                            K_AGGR_ENDTIME: '/Data_Products/VIIRS-MOD-GEO-TC/VIIRS-MOD-GEO-TC_Aggr.AggregateEndingTime',
                            K_AGGR_ENDDATE: '/Data_Products/VIIRS-MOD-GEO-TC/VIIRS-MOD-GEO-TC_Aggr.AggregateEndingDate',
                            K_SOLARZENITH: '/All_Data/VIIRS-MOD-GEO-TC_All/SolarZenithAngle',
                            K_LUNARZENITH: '/All_Data/VIIRS-MOD-GEO-TC_All/LunarZenithAngle',
                            K_MOONILLUM:   '/All_Data/VIIRS-MOD-GEO-TC_All/MoonIllumFraction',
                            K_LAT_G_RING:  '/Data_Products/VIIRS-MOD-GEO-TC/VIIRS-MOD-GEO-TC_Gran_0.G-Ring_Latitude',
                            K_LON_G_RING:  '/Data_Products/VIIRS-MOD-GEO-TC/VIIRS-MOD-GEO-TC_Gran_0.G-Ring_Longitude',
                            K_WEST_COORD:  '/Data_Products/VIIRS-MOD-GEO-TC/VIIRS-MOD-GEO-TC_Gran_0.West_Bounding_Coordinate',
                            K_EAST_COORD:  '/Data_Products/VIIRS-MOD-GEO-TC/VIIRS-MOD-GEO-TC_Gran_0.East_Bounding_Coordinate',
                            K_NORTH_COORD: '/Data_Products/VIIRS-MOD-GEO-TC/VIIRS-MOD-GEO-TC_Gran_0.North_Bounding_Coordinate',
                            K_SOUTH_COORD: '/Data_Products/VIIRS-MOD-GEO-TC/VIIRS-MOD-GEO-TC_Gran_0.South_Bounding_Coordinate',
                            },
            r'GMODO.*' : {
                            K_LATITUDE:    '/All_Data/VIIRS-MOD-GEO_All/Latitude',
                            K_LONGITUDE:   '/All_Data/VIIRS-MOD-GEO_All/Longitude',
                            K_ALTITUDE:    '/All_Data/VIIRS-MOD-GEO_All/Height',
                            K_STARTTIME:   '/All_Data/VIIRS-MOD-GEO_All/StartTime',
                            K_AGGR_STARTTIME: '/Data_Products/VIIRS-MOD-GEO/VIIRS-MOD-GEO_Aggr.AggregateBeginningTime',
                            K_AGGR_STARTDATE: '/Data_Products/VIIRS-MOD-GEO/VIIRS-MOD-GEO_Aggr.AggregateBeginningDate',
                            K_AGGR_ENDTIME: '/Data_Products/VIIRS-MOD-GEO/VIIRS-MOD-GEO_Aggr.AggregateEndingTime',
                            K_AGGR_ENDDATE: '/Data_Products/VIIRS-MOD-GEO/VIIRS-MOD-GEO_Aggr.AggregateEndingDate',
                            K_SOLARZENITH: '/All_Data/VIIRS-MOD-GEO_All/SolarZenithAngle',
                            K_LUNARZENITH: '/All_Data/VIIRS-MOD-GEO_All/LunarZenithAngle',
                            K_MOONILLUM:   '/All_Data/VIIRS-MOD-GEO_All/MoonIllumFraction',
                            K_LAT_G_RING:  '/Data_Products/VIIRS-MOD-GEO/VIIRS-MOD-GEO_Gran_0.G-Ring_Latitude',
                            K_LON_G_RING:  '/Data_Products/VIIRS-MOD-GEO/VIIRS-MOD-GEO_Gran_0.G-Ring_Longitude',
                            K_WEST_COORD:  '/Data_Products/VIIRS-MOD-GEO/VIIRS-MOD-GEO_Gran_0.West_Bounding_Coordinate',
                            K_EAST_COORD:  '/Data_Products/VIIRS-MOD-GEO/VIIRS-MOD-GEO_Gran_0.East_Bounding_Coordinate',
                            K_NORTH_COORD: '/Data_Products/VIIRS-MOD-GEO/VIIRS-MOD-GEO_Gran_0.North_Bounding_Coordinate',
                            K_SOUTH_COORD: '/Data_Products/VIIRS-MOD-GEO/VIIRS-MOD-GEO_Gran_0.South_Bounding_Coordinate',
                            },
            r'GDNBO.*' : {
                            K_LATITUDE:    '/All_Data/VIIRS-DNB-GEO_All/Latitude',
                            K_LONGITUDE:   '/All_Data/VIIRS-DNB-GEO_All/Longitude',
                            K_ALTITUDE:    '/All_Data/VIIRS-DNB-GEO_All/Height',
                            K_STARTTIME:   '/All_Data/VIIRS-DNB-GEO_All/StartTime',
                            K_AGGR_STARTTIME: '/Data_Products/VIIRS-DNB-GEO/VIIRS-DNB-GEO_Aggr.AggregateBeginningTime',
                            K_AGGR_STARTDATE: '/Data_Products/VIIRS-DNB-GEO/VIIRS-DNB-GEO_Aggr.AggregateBeginningDate',
                            K_AGGR_ENDTIME: '/Data_Products/VIIRS-DNB-GEO/VIIRS-DNB-GEO_Aggr.AggregateEndingTime',
                            K_AGGR_ENDDATE: '/Data_Products/VIIRS-DNB-GEO/VIIRS-DNB-GEO_Aggr.AggregateEndingDate',
                            K_SOLARZENITH: '/All_Data/VIIRS-DNB-GEO_All/SolarZenithAngle',
                            K_LUNARZENITH: '/All_Data/VIIRS-DNB-GEO_All/LunarZenithAngle',
                            K_MOONILLUM:   '/All_Data/VIIRS-DNB-GEO_All/MoonIllumFraction',
                            K_LAT_G_RING:  '/Data_Products/VIIRS-DNB-GEO/VIIRS-DNB-GEO_Gran_0.G-Ring_Latitude',
                            K_LON_G_RING:  '/Data_Products/VIIRS-DNB-GEO/VIIRS-DNB-GEO_Gran_0.G-Ring_Longitude',
                            K_WEST_COORD:  '/Data_Products/VIIRS-DNB-GEO/VIIRS-DNB-GEO_Gran_0.West_Bounding_Coordinate',
                            K_EAST_COORD:  '/Data_Products/VIIRS-DNB-GEO/VIIRS-DNB-GEO_Gran_0.East_Bounding_Coordinate',
                            K_NORTH_COORD: '/Data_Products/VIIRS-DNB-GEO/VIIRS-DNB-GEO_Gran_0.North_Bounding_Coordinate',
                            K_SOUTH_COORD: '/Data_Products/VIIRS-DNB-GEO/VIIRS-DNB-GEO_Gran_0.South_Bounding_Coordinate',
                            }
            }
SV_FILE_GUIDE = {
            r'SV(?P<file_kind>[IM])(?P<file_band>\d\d).*': { 
                            K_RADIANCE: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/Radiance',
                            K_REFLECTANCE: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/Reflectance',
                            K_BTEMP: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/BrightnessTemperature',
                            K_RADIANCE_FACTORS: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/RadianceFactors',
                            K_REFLECTANCE_FACTORS: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/ReflectanceFactors',
                            K_BTEMP_FACTORS: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/BrightnessTemperatureFactors',
                            K_MODESCAN: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/ModeScan',
                            K_MODEGRAN: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/ModeGran',
                            K_QF3: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/QF3_SCAN_RDR',
                            K_GEO_REF: r'%(GEO_GUIDE[kind])s_%(sat)s_d%(date)s_t%(file_start_time_str)s_e%(file_end_time_str)s_b%(orbit)s_*_%(site)s_%(domain)s.h5',
                            K_NAVIGATION: r'%%(geo_kind)s_%(sat)s_d%(date)s_t%(file_start_time_str)s_e%(file_end_time_str)s_b%(orbit)s_*_%(site)s_%(domain)s.h5' },
            r'SVDNB.*': { K_RADIANCE: '/All_Data/VIIRS-DNB-SDR_All/Radiance',
                            K_REFLECTANCE: None,
                            K_BTEMP: None,
                            K_RADIANCE_FACTORS: '/All_Data/VIIRS-DNB-SDR_All/RadianceFactors',
                            K_REFLECTANCE_FACTORS: None,
                            K_BTEMP_FACTORS: None,
                            K_MODESCAN: '/All_Data/VIIRS-DNB-SDR_All/ModeScan',
                            K_MODEGRAN: '/All_Data/VIIRS-DNB-SDR_All/ModeGran',
                            K_QF3: '/All_Data/VIIRS-DNB-SDR_All/QF3_SCAN_RDR',
                            K_GEO_REF: r'GDNBO_%(sat)s_d%(date)s_t%(file_start_time_str)s_e%(file_end_time_str)s_b%(orbit)s_*_%(site)s_%(domain)s.h5',
                            K_NAVIGATION: r'%%(geo_kind)s_%(sat)s_d%(date)s_t%(file_start_time_str)s_e%(file_end_time_str)s_b%(orbit)s_*_%(site)s_%(domain)s.h5'}
            }

ROWS_PER_SCAN = {
        BKIND_M  : 16,
        "GMTCO" : 16,
        "GMODO" : 16,
        BKIND_I  : 32,
        "GITCO" : 32,
        "GIMGO" : 32,
        BKIND_DNB : 16,
        "GDNBO" : 16
        }

COLS_PER_ROW = {
        BKIND_M   : 3200,
        BKIND_I   : 6400,
        BKIND_DNB : 4064
        }

DATA_KINDS = {
        (BKIND_M,BID_01) : DKIND_REFLECTANCE,
        (BKIND_M,BID_02) : DKIND_REFLECTANCE,
        (BKIND_M,BID_03) : DKIND_REFLECTANCE,
        (BKIND_M,BID_04) : DKIND_REFLECTANCE,
        (BKIND_M,BID_05) : DKIND_REFLECTANCE,
        (BKIND_M,BID_06) : DKIND_REFLECTANCE,
        (BKIND_M,BID_07) : DKIND_REFLECTANCE,
        (BKIND_M,BID_08) : DKIND_REFLECTANCE,
        (BKIND_M,BID_09) : DKIND_REFLECTANCE,
        (BKIND_M,BID_10) : DKIND_REFLECTANCE,
        (BKIND_M,BID_11) : DKIND_REFLECTANCE,
        (BKIND_M,BID_12) : DKIND_BTEMP,
        (BKIND_M,BID_13) : DKIND_BTEMP,
        (BKIND_M,BID_14) : DKIND_BTEMP,
        (BKIND_M,BID_15) : DKIND_BTEMP,
        (BKIND_M,BID_16) : DKIND_BTEMP,
        (BKIND_I,BID_01) : DKIND_REFLECTANCE,
        (BKIND_I,BID_02) : DKIND_REFLECTANCE,
        (BKIND_I,BID_03) : DKIND_REFLECTANCE,
        (BKIND_I,BID_04) : DKIND_BTEMP,
        (BKIND_I,BID_05) : DKIND_BTEMP,
        (BKIND_I,BID_06) : DKIND_REFLECTANCE,
        (BKIND_DNB,NOT_APPLICABLE) : DKIND_RADIANCE
        }

ENHANCED_IR_BAND_KIND = {
        (BKIND_M,BID_12) : BKIND_M_ENHANCED,
        (BKIND_M,BID_13) : BKIND_M_ENHANCED,
        (BKIND_M,BID_14) : BKIND_M_ENHANCED,
        (BKIND_M,BID_15) : BKIND_M_ENHANCED,
        (BKIND_I,BID_04) : BKIND_I_ENHANCED,
        (BKIND_I,BID_05) : BKIND_I_ENHANCED,
        }

VAR_PATHS = {
        (BKIND_M,BID_01) : K_REFLECTANCE,
        (BKIND_M,BID_02) : K_REFLECTANCE,
        (BKIND_M,BID_03) : K_REFLECTANCE,
        (BKIND_M,BID_04) : K_REFLECTANCE,
        (BKIND_M,BID_05) : K_REFLECTANCE,
        (BKIND_M,BID_06) : K_REFLECTANCE,
        (BKIND_M,BID_07) : K_REFLECTANCE,
        (BKIND_M,BID_08) : K_REFLECTANCE,
        (BKIND_M,BID_09) : K_REFLECTANCE,
        (BKIND_M,BID_10) : K_REFLECTANCE,
        (BKIND_M,BID_11) : K_REFLECTANCE,
        (BKIND_M,BID_12) : K_BTEMP,
        (BKIND_M,BID_13) : K_BTEMP,
        (BKIND_M,BID_14) : K_BTEMP,
        (BKIND_M,BID_15) : K_BTEMP,
        (BKIND_M,BID_16) : K_BTEMP,
        (BKIND_I,BID_01) : K_REFLECTANCE,
        (BKIND_I,BID_02) : K_REFLECTANCE,
        (BKIND_I,BID_03) : K_REFLECTANCE,
        (BKIND_I,BID_04) : K_BTEMP,
        (BKIND_I,BID_05) : K_BTEMP,
        (BKIND_I,BID_06) : K_REFLECTANCE,
        (BKIND_DNB,NOT_APPLICABLE) : K_RADIANCE
        }

band2const = {
        "01" : BID_01,
        "02" : BID_02,
        "03" : BID_03,
        "04" : BID_04,
        "05" : BID_05,
        "06" : BID_06,
        "07" : BID_07,
        "08" : BID_08,
        "09" : BID_09,
        "10" : BID_10,
        "11" : BID_11,
        "12" : BID_12,
        "13" : BID_13,
        "14" : BID_14,
        "15" : BID_15,
        "16" : BID_16
        }

# missing value sentinels for different datasets
# 0 if scaling exists, 1 if scaling is None
MISSING_GUIDE = {
                DKIND_REFLECTANCE : ( lambda A: A>=65528, lambda A: A <  -999.0 ),
                DKIND_RADIANCE    : ( lambda A: A>=65528, lambda A: A <  -999.0 ),
                DKIND_BTEMP       : ( lambda A: A>=65528, lambda A: A <  -999.0 ),
                K_SOLARZENITH     : ( lambda A: A>=65528, lambda A: A <  -999.0 ),
                K_LUNARZENITH     : ( lambda A: A>=65528, lambda A: A <  -999.0 ),
                K_MODESCAN        : ( lambda A: A>1,      lambda A: A >  1      ),
                K_LATITUDE        : ( lambda A: A>=65528, lambda A: A <= -999   ),
                K_LONGITUDE       : ( lambda A: A>=65528, lambda A: A <= -999   )
                }


# a regular expression to split up granule names into dictionaries
RE_NPP = re.compile('(?P<file_kindnband>[A-Z0-9]+)_(?P<sat>[A-Za-z0-9]+)_d(?P<date>\d+)_t(?P<file_start_time_str>\d+)_e(?P<file_end_time_str>\d+)_b(?P<orbit>\d+)_c(?P<created_time>\d+)_(?P<site>[a-zA-Z0-9]+)_(?P<domain>[a-zA-Z0-9]+)\.h5')
# format string to turn it back into a filename
FMT_NPP = r'%(file_kindnband)s_%(sat)s_d%(date)s_t%(file_start_time_str)s_e%(file_end_time_str)s_b%(orbit)s_c%(created_time)s_%(site)s_%(domain)s.h5'

class evaluator(object):
    """
    evaluate expressions in format statements
    e.g. '%(4*2)d %(", ".join([c]*b))s' % evaluator(a=2,b=3,c='foo')
    """
    def __init__(self,**argd):
        vars(self).update(argd)
    def __getitem__(self, expr):
        return eval(expr, globals(), vars(self))

def make_polygon_tuple(lon_ring, lat_ring):
    return tuple(tuple(x) for x in zip(lon_ring,lat_ring))

def _glob_file(pat):
    """Globs for a single file based on the provided pattern.

    :raises ValueError: if more than one file matches pattern
    """
    tmp = glob(pat)
    if len(tmp) != 1:
        log.error("There were no files or more than one fitting the pattern %s" % pat)
        raise ValueError("There were no files or more than one fitting the pattern %s" % pat)
    return tmp[0]

def calculate_bbox_bounds(wests, easts, norths, souths, fill_value=DEFAULT_FILL_VALUE):
    """Given a list of west most points, east-most, north-most, and
    south-most points, calculate the bounds for the overall aggregate
    granule. This is needed since we don't no if the last granule
    or the first granule in an aggregate SDR file is south-most, east-most,
    etc.
    """
    wests  = np.array(wests)
    wests  = wests[ (wests >= -180) & (wests <= 180) ]
    easts  = np.array(easts)
    easts  = easts[ (easts >= -180) & (easts <= 180) ]
    norths = np.array(norths)
    norths = norths[ (norths >= -90) & (norths <= 90) ]
    souths = np.array(souths)
    souths = souths[ (souths >= -90) & (souths <= 90) ]

    if norths.shape[0] == 0: nbound = fill_value
    else: nbound = norths.max()
    if souths.shape[0] == 0: sbound = fill_value
    else: sbound = souths.min()

    if wests.shape[0] == 0:
        # If we didn't have any valid coordinates, its just a fill value
        wbound = fill_value
    elif wests.max() - wests.min() > 180:
        # We are crossing the dateline
        wbound = wests[ wests > 0 ].min()
    else:
        # We aren't crossing the dateline so simple calculation
        wbound = min(wests)

    if easts.shape[0] == 0:
        # If we didn't have any valid coordinates, its just a fill value
        ebound = fill_value
    elif easts.max() - easts.min() > 180:
        # We are crossing the dateline
        ebound = easts[ easts < 0 ].max()
    else:
        ebound = max(easts)


    return float(wbound),float(ebound),float(nbound),float(sbound)

def sort_files_by_nav_uid(filepaths):
    """Logic is duplicated from file_info-like method because it has less
    overhead and this function was required a different way of accessing the
    data.
    """
    # Create the dictionary structure to hold the filepaths
    nav_dict = {}
    for band_kind,band_id in DATA_KINDS.keys():
        nav_uid = NAV_SET_GUIDE[band_kind]
        if nav_uid not in nav_dict: nav_dict[nav_uid] = {}
        nav_dict[nav_uid][band_id] = []

    for fp in filepaths:
        fn = os.path.split(fp)[-1]
        if fn.startswith("SVI") and fn.endswith(".h5"):
            nav_uid = NAV_SET_GUIDE[BKIND_I]
            if fn[3:5] in nav_dict[nav_uid]:
                nav_dict[nav_uid][fn[3:5]].append(fp)
                continue
        if fn.startswith("SVM") and fn.endswith(".h5"):
            nav_uid = NAV_SET_GUIDE[BKIND_M]
            if fn[3:5] in nav_dict[nav_uid]:
                nav_dict[nav_uid][fn[3:5]].append(fp)
                continue
        if fn.startswith("SVDNB") and fn.endswith(".h5"):
            nav_uid = NAV_SET_GUIDE[BKIND_DNB]
            nav_dict[nav_uid][NOT_APPLICABLE].append(fp)
            continue

        # Ignore the file that we don't understand

    # Make unique and sort
    for nav_uid,nav_uid_dict in nav_dict.items():
        num_files_for_set = 0
        for file_id in nav_uid_dict.keys():
            # If we don't have any files for this file set, remove the file set
            if not nav_uid_dict[file_id]:
                del nav_uid_dict[file_id]
                continue

            nav_uid_dict[file_id] = sorted(set(nav_uid_dict[file_id]), key=lambda f: os.path.split(f)[-1])

            num_files = len(nav_uid_dict[file_id])
            num_files_for_set = num_files_for_set or num_files # previous value or set it for the first time
            if num_files != num_files_for_set:
                # We weren't given the same number of files for this nav_set
                log.error("Nav. set %s did not have the same number of files for every band (%s), expected %d got %d files" % (nav_uid,file_id,num_files_for_set,num_files))
                raise ValueError("Nav. set %s did not have the same number of files for every band (%s), expected %d got %d files" % (nav_uid,file_id,num_files_for_set,num_files))

        # If we don't have any files for this navigation set, remove the file set
        if not nav_dict[nav_uid]:
            del nav_dict[nav_uid]
            continue

    return nav_dict


def _time_string_to_datetime(d, st):
    s_us = int(st[-1])*100000
    s_dt = datetime.strptime(d + st[:-1], "%Y%m%d%H%M%S").replace(tzinfo=UTC, microsecond=s_us)
    return s_dt

def _time_attr_to_datetime(d, st):
    # The last character is a Z (as in Zulu/UTC)
    whole_sec,s_us = st[:-1].split(".")
    s_us = int(s_us)
    s_dt = datetime.strptime(d + whole_sec, "%Y%m%d%H%M%S").replace(tzinfo=UTC, microsecond=s_us)
    return s_dt

def get_datetimes(finfo):
    """Takes a file info dictionary and creates a datetime object for the
    start of the granule and the end of the granule.
    """
    d = finfo["date"]
    st = finfo["file_start_time_str"]
    et = finfo["file_end_time_str"]
    finfo["file_start_time"] = _time_string_to_datetime(d, st)
    finfo["file_end_time"] = _time_string_to_datetime(d, et)


def h5path(hp, path, h5_path, required=False, quiet=False):
    """traverse an hdf5 path to return a nested data object

    Attributes can be retreived by using "/var/path.attr".

    Quiet says to not log any messages (does not effect required check).
    """
    if not quiet: log.debug('fetching %s from %s' % (path, h5_path))
    x = hp
    for a in path.split('/'):
        if a:
            # Check if they used a '.' to describe an attribute
            parts = a.split(".")
            attr_name = None
            if len(parts) != 1:
                a,attr_name = a.split(".")[:2]

            if a in x:
                x = x[a]
                if attr_name:
                    if attr_name in x.attrs:
                        x = x.attrs[attr_name]
                        # We have the attribute so we're done
                        break
                    else:
                        if not quiet: log.debug("Couldn't find attribute %s of path %s" % (attr_name,path))
                        x = None
                        break
            else:
                if not quiet: log.debug("Couldn't find %s (or its parent) in %s" % (a,path))
                x = None
                break
        else:
            # If they put a / at the end of the var path
            continue
    if x is hp:
        if not quiet: log.error("Could not get %s from h5 file" % path)
        x = None

    if x is None and required:
        log.error("Couldn't get data %s from %s" % (path, h5_path))
        raise ValueError("Couldn't get data %s from %s" % (path, h5_path))

    return x

def _st_to_datetime(st):
    """Convert a VIIRS StartTime which is in microseconds since 1958-01-01 to
    a datetime object.
    """
    base = datetime(1958, 1, 1, 0, 0, 0)
    return base + timedelta(microseconds=int(st))

def file_info(fn):
    """Given a filename, returns a dictionary of information that could
    be derived.

    :postcondition:
        The returned ``finfo`` will have the following keys:
            - kind
            - band
            - data_kind
            - rows_per_scan
            - cols_per_row
            - factors
            - geo_glob
            - img_path

    :attention:
        This method does not require that the file actually exists.

    :Parameters:
        fn : str
            Filename of image data to be analyzed

    :raises ValueError:
        if filename matches 1 regular expression for a data file, but not of a generic NPP filename
    """
    fn = os.path.abspath(fn)
    finfo = {}
    finfo["img_path"] = fn
    finfo["base_path"],finfo["filename"] = base_path,filename = os.path.split(fn)

    for pat, nfo in SV_FILE_GUIDE.items():
        # Find what type of file we have
        m = re.match(pat, filename)
        if not m:
            continue

        # collect info from filename
        pat_match = RE_NPP.match(filename)
        if not pat_match:
            log.error("Filename matched initial pattern, but not full name pattern")
            raise ValueError("Filename matched initial pattern, but not full name pattern")
        pat_info = dict(pat_match.groupdict())

        minfo = m.groupdict()
        # Translate band info into constants for rest of polar2grid processing
        if "file_kind" not in minfo:
            # For dnb
            minfo["kind"] = BKIND_DNB
            minfo["band"] = NOT_APPLICABLE
        elif minfo["file_kind"] == "M":
            minfo["kind"] = BKIND_M
        elif minfo["file_kind"] == "I":
            minfo["kind"] = BKIND_I
        else:
            log.error("Band kind not known '%s'" % minfo["kind"])
            raise ValueError("Band kind not known '%s'" % minfo["kind"])

        # Translate band identifier/number into constants
        if "file_band" in minfo:
            if minfo["file_band"] not in band2const:
                log.error("Band number not known '%s'" % (minfo["file_band"],))
                raise ValueError("Band number not known '%s'" % (minfo["file_band"],))
            minfo["band"] = band2const[minfo["file_band"]]

        # merge the guide info
        finfo.update(pat_info)
        finfo.update(minfo)

        # Figure out what type of data we want to use
        dkind = (finfo["kind"],finfo["band"])
        if dkind not in DATA_KINDS:
            log.error("Data kind not known (Kind: %s; Band: %s)" % dkind)
            raise ValueError("Data kind not known (Kind: %s; Band: %s)" % dkind)
        finfo["data_kind"] = DATA_KINDS[dkind]
        finfo["rows_per_scan"] = ROWS_PER_SCAN[finfo["kind"]]
        finfo["cols_per_row"] = COLS_PER_ROW[finfo["kind"]]
        finfo["factors"] = FACTORS_GUIDE[finfo["data_kind"]]

        # Convert time information to datetime objects
        get_datetimes(finfo)
        finfo.update(**nfo)
        eva = evaluator(GEO_GUIDE=GEO_GUIDE, **finfo)
        for k,v in finfo.items():
            if isinstance(v,str):
                finfo[k] = v % eva

        # Geonav file exists
        file_glob = finfo[K_NAVIGATION] % {"geo_kind":GEO_GUIDE[finfo["kind"]][1]}
        geo_glob = os.path.join(base_path, file_glob)
        try:
            # First try terrain corrected
            finfo["geo_path"] = _glob_file(geo_glob)
            log.info("Using terrain corrected navigation %s " % (finfo["geo_path"],))
        except ValueError:
            log.debug("Couldn't identify terrain corrected geonav file for file %s" % (fn,))
            # Try the non-terrain corrected
            file_glob = finfo[K_NAVIGATION] % {"geo_kind":GEO_GUIDE[finfo["kind"]][0]}
            geo_glob = os.path.join(base_path, file_glob)
            try:
                # First try terrain corrected
                finfo["geo_path"] = _glob_file(geo_glob)
                log.info("Using non-TC navigation %s " % (finfo["geo_path"],))
            except ValueError:
                log.error("Could not find TC or non-TC navigation files for %s" % (fn,))
                raise ValueError("Could not find TC or non-TC navigation files for %s" % (fn,))

        return finfo
    log.warning('unable to find %s in guidebook' % filename)
    return finfo

def read_file_info(finfo, extra_mask=None, fill_value=-999, dtype=np.float32):
    """Reads the hdf file associated with the file info dictionary provided
    and returns all of the information that could be useful outside of this
    function.

    :precondition:
        ``finfo`` was returned from `file_info` or meets the post
        condition of `file_info`.
    :precondition:
        ``finfo`` is allowed to be changed/updated/added to in place.
    :postcondition:
        ``finfo`` will have the following new keys:
            - image_data
            - image_mask
            - mode_mask

    :Parameters:
        finfo : dict
            File info dictionary returned from `file_info`.
    :Keywords:
        extra_mask : ``numpy.ndarray``
            An additional mask that will be used to fill the data.
        fill_value : int or float
            Fill value to be used for all bad data found.
        dtype : ``numpy.dtype``
            The data type that the returned data array will be forced to.
    """
    hp = h5.File(finfo["img_path"], 'r')

    data_kind = finfo["data_kind"]
    data_var_path = finfo[VAR_PATHS[(finfo["kind"],finfo["band"])]]
    factors_var_path = finfo[finfo["factors"]]
    qf3_var_path = finfo[K_QF3]

    # Get image data
    h5v = h5path(hp, data_var_path, finfo["img_path"], required=True)
    image_data = h5v[:,:]
    image_data = image_data.astype(dtype)
    del h5v

    # Get QF3 data
    h5v = h5path(hp, qf3_var_path, finfo["img_path"], required=True)
    qf3_data = h5v[:]
    del h5v

    # Get scaling function (also reads scaling factors from hdf)
    factvar = h5path(hp, factors_var_path, finfo["img_path"], required=False)   # FUTURE: make this more elegant please
    if factvar is None:
        log.debug("No scaling factors found for %s at %s (this is OK)" % (data_var_path, factors_var_path))
        def scaler(image_data):
            return image_data,np.zeros(image_data.shape).astype(np.bool)
        needs_scaling = False
    else:
        factor_list = list(factvar[:])
        log.debug("scaling factors for %s are %s" % (data_var_path, str(factor_list)))
        if len(factor_list) % 2 != 0:
            log.error("There are an odd number of scaling factors for %s" % (data_var_path,))
            raise ValueError("There are an odd number of scaling factors for %s" % (data_var_path,))

        # Figure out how data should be scaled
        def scaler(image_data, scaling_factors=factor_list):
            num_grans = len(scaling_factors)/2
            gran_size = image_data.shape[0]/num_grans
            scaling_mask = np.zeros(image_data.shape)
            for i in range(num_grans):
                start_idx = i * gran_size
                end_idx = start_idx + gran_size
                m = scaling_factors[i*2]
                b = scaling_factors[i*2 + 1]
                if m <= -999 or b <= -999:
                    scaling_mask[start_idx : end_idx] = 1
                else:
                    image_data[start_idx : end_idx] = m * image_data[start_idx : end_idx] + b

            scaling_mask = scaling_mask.astype(np.bool)
            return image_data,scaling_mask

        needs_scaling = True

    # Calculate mask
    mask = MISSING_GUIDE[data_kind][not needs_scaling](image_data) if data_kind in MISSING_GUIDE else None
    if extra_mask is not None:
        mask = mask | extra_mask

    # Scale image data
    image_data,scaling_mask = scaler(image_data)
    mask = mask | scaling_mask

    # Create scan_quality array
    scan_quality = np.nonzero(np.repeat(qf3_data > 0, finfo["rows_per_scan"]))

    # Mask off image data
    image_data[mask] = fill_value

    finfo["image_data"] = image_data
    finfo["image_mask"] = mask
    finfo["mode_mask"] = None
    finfo["scan_quality"] = scan_quality

    return finfo

def geo_info(fn):
    """Will return a dictionary of information that could be derived from the
    provided geo-navigation filename.

    :postcondition:
        The returned ``finfo`` (or ginfo) will contain the following keys:
            - geo_path
            - kind
            - rows_per_scan

    :Parameters:
        fn : str
            Geo-navigation filename to be analyzed

    :raises ValueError:
        if filename matches 1 regular expression for a geonav, but not of a generic NPP filename
    """
    fn = os.path.abspath(fn)
    finfo = {}
    finfo["geo_path"] = fn
    finfo["filename"] = filename = os.path.split(fn)[1]
    for pat, nfo in GEO_FILE_GUIDE.items():
        # Find what type of file we have
        m = re.match(pat, filename)
        if not m:
            continue

        # collect info from filename
        pat_match = RE_NPP.match(filename)
        if not pat_match:
            log.error("Filename matched initial pattern, but not full name pattern")
            raise ValueError("Filename matched initial pattern, but not full name pattern")
        pat_info = dict(pat_match.groupdict())
        minfo = m.groupdict()

        # merge the guide info
        finfo.update(pat_info)
        finfo.update(minfo)

        # Get constant/known information from mappings
        finfo["rows_per_scan"] = ROWS_PER_SCAN[finfo["file_kindnband"]]

        # Fill any information if needed
        finfo.update(**nfo)
        eva = evaluator(GEO_GUIDE=GEO_GUIDE, **finfo)
        for k,v in finfo.items():
            if isinstance(v,str):
                finfo[k] = v % eva
        return finfo
    log.warning('unable to find %s in guidebook' % filename)
    return finfo

def read_geo_bbox_coordinates(hp, finfo, fill_value=DEFAULT_FILL_VALUE):
    wbound_path    = finfo[K_WEST_COORD]
    ebound_path    = finfo[K_EAST_COORD]
    nbound_path    = finfo[K_NORTH_COORD]
    sbound_path    = finfo[K_SOUTH_COORD]

    # Get the bounding box coordinates (special cased for aggregate files)
    wests,easts,norths,souths = [],[],[],[]
    w_h5v = h5path(hp, wbound_path, finfo["geo_path"], required=False)
    e_h5v = h5path(hp, ebound_path, finfo["geo_path"], required=False)
    n_h5v = h5path(hp, nbound_path, finfo["geo_path"], required=False)
    s_h5v = h5path(hp, sbound_path, finfo["geo_path"], required=False)
    count = 0
    while w_h5v is not None:
        # Get the data and add it to the list of bounds
        wests.append(  w_h5v[0] )
        easts.append(  e_h5v[0] )
        norths.append( n_h5v[0] )
        souths.append( s_h5v[0] )

        # Update the h5paths for other granules if they exist (aggregate files)
        count += 1
        wbound_path_tmp = wbound_path.replace("Gran_0", "Gran_%d" % count)
        ebound_path_tmp = ebound_path.replace("Gran_0", "Gran_%d" % count)
        nbound_path_tmp = nbound_path.replace("Gran_0", "Gran_%d" % count)
        sbound_path_tmp = sbound_path.replace("Gran_0", "Gran_%d" % count)
        w_h5v = h5path(hp, wbound_path_tmp, finfo["geo_path"], required=False)
        e_h5v = h5path(hp, ebound_path_tmp, finfo["geo_path"], required=False)
        n_h5v = h5path(hp, nbound_path_tmp, finfo["geo_path"], required=False)
        s_h5v = h5path(hp, sbound_path_tmp, finfo["geo_path"], required=False)

    # Check that we got some bounds information
    if len(wests) == 0:
        log.error("Could not find any bounding coordinates: '%s'" % (ebound_path,))
        raise ValueError("Could not find any bounding coordinates: '%s'" % (ebound_path,))

    # Find the actual bounding box of these values
    wbound,ebound,nbound,sbound = calculate_bbox_bounds(wests, easts, norths, souths, fill_value=fill_value)

    return wbound,ebound,nbound,sbound

def load_geo_variable(hp, finfo, variable_key, dtype=np.float32, required=False):
    var_path = finfo[variable_key]
    h5v = h5path(hp, var_path, finfo["geo_path"], required=required)
    if h5v is None:
        log.debug("Variable '%s' was not found in '%s'" % (var_path, finfo["geo_path"]))
        data = None
    else:
        data = h5v[:,:]
        data = data.astype(dtype)

    return data

def get_geo_variable_fill_mask(data_array, variable_key):
    mask = MISSING_GUIDE[K_LATITUDE][1](data_array) if K_LATITUDE in MISSING_GUIDE else None
    return mask

def read_geo_info(finfo, fill_value=-999, dtype=np.float32):
    """Will fill in finfo with the data that is assumed to
    be necessary for future processing.

    :precondition:
        ``finfo`` is allowed to be changed/updated/added to in place.
    :precondition:
        ``finfo`` cam from `geo_info` or at least meets the post
        condition of `geo_info`.
    :postcondition:
        ``finfo`` will have the following keys added:
            - lat_data
            - lon_data
            - lat_mask
            - lon_mask
            - mode_mask
            - start_time
            - scan_quality

    :Parameters:
        finfo : dict
            Dictionary of information from `geo_info`.
    :Keywords:
        fill_value : int or float
            Fill value for any bad data found.
        dtype : ``numpy.dtype``
            Data type that the returned data is forced to.
    """

    hp = h5.File(finfo["geo_path"], 'r')

    st_var_path    = finfo[K_STARTTIME]
    iet_st_var_path = finfo[K_AGGR_STARTTIME]
    iet_sd_var_path = finfo[K_AGGR_STARTDATE]
    iet_et_var_path = finfo[K_AGGR_ENDTIME]
    iet_ed_var_path = finfo[K_AGGR_ENDDATE]
    mia_var_path   = finfo[K_MOONILLUM]
    lat_gring_path = finfo[K_LAT_G_RING]
    lon_gring_path = finfo[K_LON_G_RING]

    # Get latitude data
    lat_data = load_geo_variable(hp, finfo, K_LATITUDE, dtype=dtype, required=True)

    # Get longitude data
    lon_data = load_geo_variable(hp, finfo, K_LONGITUDE, dtype=dtype, required=True)

    # Get solar zenith angle
    sza_data = load_geo_variable(hp, finfo, K_SOLARZENITH)
    
    # Get the lunar zenith angle
    lza_data = load_geo_variable(hp, finfo, K_LUNARZENITH)
    
    # Get start time
    h5v = h5path(hp, st_var_path, finfo["geo_path"], required=True)
    start_time = _st_to_datetime(h5v[0])
    st = h5path(hp, iet_st_var_path, finfo["geo_path"], required=True)[0][0]
    sd = h5path(hp, iet_sd_var_path, finfo["geo_path"], required=True)[0][0]
    iet_start_time = _time_attr_to_datetime(sd, st)

    # Get end time
    et = h5path(hp, iet_et_var_path, finfo["geo_path"], required=True)[0][0]
    ed = h5path(hp, iet_ed_var_path, finfo["geo_path"], required=True)[0][0]
    iet_end_time = _time_attr_to_datetime(ed, et)
    end_time = start_time + (iet_end_time - iet_start_time)

    # Get the G Ring information
    h5v = h5path(hp, lon_gring_path, finfo["geo_path"], required=True)
    lon_gring = h5v[:,:]
    h5v = h5path(hp, lat_gring_path, finfo["geo_path"], required=True)
    lat_gring = h5v[:,:]
    swath_polygon = make_polygon_tuple(lon_gring, lat_gring)

    # Get the bounding box coordinates (special cased for aggregate files)
    wbound,ebound,nbound,sbound = read_geo_bbox_coordinates(hp, finfo, fill_value=fill_value)

    # Get the moon illumination information
    h5v = h5path(hp, mia_var_path, finfo["geo_path"], required=False)
    if h5v is None:
        log.debug("Variable '%s' was not found in '%s'" % (mia_var_path, finfo["geo_path"]))
        moon_illum = None
    else:
        moon_illum = h5v[0] / 100.0
        log.debug("moon illumination fraction: " + str(moon_illum))

    # Calculate latitude mask
    lat_mask = get_geo_variable_fill_mask(lat_data, K_LATITUDE)

    # Calculate longitude mask
    lon_mask = get_geo_variable_fill_mask(lon_data, K_LONGITUDE)

    # Calculate solar zenith angle mask
    sza_mask = get_geo_variable_fill_mask(sza_data, K_SOLARZENITH)
    
    # Calculate the lunar zenith angle mask
    if lza_data is not None:
        lza_mask = get_geo_variable_fill_mask(lza_data, K_LUNARZENITH)
    
    # Mask off bad data
    # NOTE: There could still be missing image data to account for
    sza_data[ lat_mask | lon_mask | sza_mask ] = fill_value
    if lza_data is not None:
        lza_data[ lat_mask | lon_mask | lza_mask ] = fill_value
    lat_data[ lat_mask ] = fill_value
    lon_data[ lon_mask ] = fill_value

    finfo["lat_data"]   = lat_data
    finfo["lon_data"]   = lon_data
    finfo["lat_mask"]   = lat_mask
    finfo["lon_mask"]   = lon_mask
    finfo["swath_polygon"] = swath_polygon # Not used yet
    finfo["lon_west"]   = wbound
    finfo["lon_east"]   = ebound
    finfo["lat_north"]  = nbound
    finfo["lat_south"]  = sbound
    finfo["mode_mask"]  = sza_data
    finfo["moon_angle"] = lza_data
    finfo["moon_illum"] = moon_illum
    finfo["start_time"] = start_time
    finfo["end_time"] = end_time
    # Rows only
    finfo["scan_quality"] = (np.unique(np.nonzero(lat_mask)[0]),)
    return finfo

def generic_info(fn):
    """Wrapper function that tells what function should be called based
    on the first letter of the filename passed.

    'S' for data files, 'G' for geo files

    :raises ValueError: if `fn` doesn't start with 'S' or 'G'
    """
    if os.path.split(fn)[1].startswith("S"):
        return file_info(fn)
    elif os.path.split(fn)[1].startswith("G"):
        return geo_info(fn)
    else:
        log.error("Unknown file type for %s" % fn)
        raise ValueError("Unknown file type for %s" % fn)

def generic_read(fn, finfo):
    """Wrapper function that tells what read function should be called based
    on the first letter of the filename passed.

    'S' for data files, 'G' for geo files

    :raises ValueError: if `fn` doesn't start with 'S' or 'G'
    """
    if os.path.split(fn)[1].startswith("S"):
        return read_file_info(finfo)
    elif os.path.split(fn)[1].startswith("G"):
        return read_geo_info(finfo)
    else:
        log.error("Unknown file type for %s" % fn)
        raise ValueError("Unknown file type for %s" % fn)

def main():
    import optparse
    from pprint import pprint
    usage = """
%prog [options] filename1.h5

"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
            help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_option('-r', '--no-read', dest='read_h5', action='store_false', default=True,
            help="don't read or look for the h5 file, only analyze the filename")
    (options, args) = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])

    if not args:
        parser.error( 'must specify 1 filename, try -h or --help.' )
        return -1

    for fn in args:
        try:
            finfo = generic_info(fn)
        except:
            log.error("Failed to get info from filename '%s'" % fn, exc_info=1)
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

if __name__ == '__main__':
    sys.exit(main())
