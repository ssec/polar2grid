#!/usr/bin/env python
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
#
# Written by David Hoese    October 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""
Provide information about ADL product files for a variety of uses.

:author:       David Hoese (davidh)
:author:       Ray Garcia (rayg)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Oct 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

from polar2grid.core import UTC
from polar2grid.core.constants import *
import numpy as np

import os
import sys
import logging
from collections import namedtuple

log = logging.getLogger(__name__)
UTC = UTC()


# TODO: Move this to a more appropriate place
# We define the types of files we know about to organize the files
FILE_TYPE_I01 = "FT_I01"
FILE_TYPE_I02 = "FT_I02"
FILE_TYPE_I03 = "FT_I03"
FILE_TYPE_I04 = "FT_I04"
FILE_TYPE_I05 = "FT_I05"
FILE_TYPE_M01 = "FT_M01"
FILE_TYPE_M02 = "FT_M02"
FILE_TYPE_M03 = "FT_M03"
FILE_TYPE_M04 = "FT_M04"
FILE_TYPE_M05 = "FT_M05"
FILE_TYPE_M06 = "FT_M06"
FILE_TYPE_M07 = "FT_M07"
FILE_TYPE_M08 = "FT_M08"
FILE_TYPE_M09 = "FT_M09"
FILE_TYPE_M10 = "FT_M10"
FILE_TYPE_M11 = "FT_M11"
FILE_TYPE_M12 = "FT_M12"
FILE_TYPE_M13 = "FT_M13"
FILE_TYPE_M14 = "FT_M14"
FILE_TYPE_M15 = "FT_M15"
FILE_TYPE_M16 = "FT_M16"
FILE_TYPE_DNB = "FT_DNB"
FILE_TYPE_GDNBO = "FT_GDNBO"
FILE_TYPE_GITCO = "FT_GITCO"
FILE_TYPE_GMTCO = "FT_GMTCO"
FILE_TYPE_GIMGO = "FT_GIMGO"
FILE_TYPE_GMODO = "FT_GMODO"

# For future use:
# FILE_TYPE_SST = "FT_SST"
# TODO: Copy information from guidebook or move this to the guidebook
FILE_TYPES = {
    FILE_TYPE_I01: None,
    FILE_TYPE_I02: None,
    FILE_TYPE_I03: None,
    FILE_TYPE_I04: None,
    FILE_TYPE_I05: None,
    FILE_TYPE_M01: None,
    FILE_TYPE_M02: None,
    FILE_TYPE_M03: None,
    FILE_TYPE_M04: None,
    FILE_TYPE_M05: None,
    FILE_TYPE_M06: None,
    FILE_TYPE_M07: None,
    FILE_TYPE_M08: None,
    FILE_TYPE_M09: None,
    FILE_TYPE_M10: None,
    FILE_TYPE_M11: None,
    FILE_TYPE_M12: None,
    FILE_TYPE_M13: None,
    FILE_TYPE_M14: None,
    FILE_TYPE_M15: None,
    FILE_TYPE_M16: None,
    FILE_TYPE_DNB: None,
    FILE_TYPE_GDNBO: None,
    FILE_TYPE_GITCO: None,
    FILE_TYPE_GMTCO: None,
    FILE_TYPE_GIMGO: None,
    FILE_TYPE_GMODO: None,
}







K_LATITUDE = "latitude"
K_LONGITUDE = "longitude"
# Special case for TC DNB:
K_TCLATITUDE = "tclatitude"
K_TCLONGITUDE = "tclongitude"
K_RADIANCE = "radiance"
K_REFLECTANCE = "reflectance"
K_BTEMP = "brightness_temperature"
K_SOLARZENITH = "solar_zenith_angle"
K_LUNARZENITH = "lunar_zenith_angle"
K_MOONILLUM = "lunar_illumination"
K_ALTITUDE = "altitude"
K_RADIANCE_FACTORS = "radiance_factors"
K_REFLECTANCE_FACTORS = "reflectance_factors"
K_BTEMP_FACTORS = "brightness_temperature_factors"
K_SST_FACTORS = "sea_surface_temperature_factors"
K_STARTTIME = "begin_time"
K_AGGR_STARTTIME = "aggr_begin_time"
K_AGGR_STARTDATE = "aggr_begin_date"
K_AGGR_ENDTIME = "aggr_end_time"
K_AGGR_ENDDATE = "aggr_end_date"
K_NUMSCANS = "number_of_scans"
K_ROWSPERSCAN = "rows_per_scan"
K_MODESCAN = "mode_scan"
K_MODEGRAN = "mode_granule"
K_QF1 = "qf1"
K_QF3 = "qf3"
K_LAT_G_RING = "latitude_gring"
K_LON_G_RING = "longitude_gring"
K_WEST_COORD = "west_coordinate"
K_EAST_COORD = "east_coordinate"
K_NORTH_COORD = "north_coordinate"
K_SOUTH_COORD = "south_coordinate"
K_SATELLITE = "satellite_name"
K_DATA_PATH = "data_path"

# File Regexes
# FUTURE: Put in a config file
I01_REGEX = r'SVI01_(?P<satellite>[^_]*)_.*\.h5'
I02_REGEX = r'SVI02_(?P<satellite>[^_]*)_.*\.h5'
I03_REGEX = r'SVI03_(?P<satellite>[^_]*)_.*\.h5'
I04_REGEX = r'SVI04_(?P<satellite>[^_]*)_.*\.h5'
I05_REGEX = r'SVI05_(?P<satellite>[^_]*)_.*\.h5'
M01_REGEX = r'SVM01_(?P<satellite>[^_]*)_.*\.h5'
M02_REGEX = r'SVM02_(?P<satellite>[^_]*)_.*\.h5'
M03_REGEX = r'SVM03_(?P<satellite>[^_]*)_.*\.h5'
M04_REGEX = r'SVM04_(?P<satellite>[^_]*)_.*\.h5'
M05_REGEX = r'SVM05_(?P<satellite>[^_]*)_.*\.h5'
M06_REGEX = r'SVM06_(?P<satellite>[^_]*)_.*\.h5'
M07_REGEX = r'SVM07_(?P<satellite>[^_]*)_.*\.h5'
M08_REGEX = r'SVM08_(?P<satellite>[^_]*)_.*\.h5'
M09_REGEX = r'SVM09_(?P<satellite>[^_]*)_.*\.h5'
M10_REGEX = r'SVM10_(?P<satellite>[^_]*)_.*\.h5'
M11_REGEX = r'SVM11_(?P<satellite>[^_]*)_.*\.h5'
M12_REGEX = r'SVM12_(?P<satellite>[^_]*)_.*\.h5'
M13_REGEX = r'SVM13_(?P<satellite>[^_]*)_.*\.h5'
M14_REGEX = r'SVM14_(?P<satellite>[^_]*)_.*\.h5'
M15_REGEX = r'SVM15_(?P<satellite>[^_]*)_.*\.h5'
M16_REGEX = r'SVM16_(?P<satellite>[^_]*)_.*\.h5'
DNB_REGEX = r'SVDNB_(?P<satellite>[^_]*)_.*\.h5'
SST_REGEX = r'VSSTO_(?P<satellite>[^_]*)_.*\.h5'
# Geolocation regexes
I_GEO_REGEX = r'GIMGO_(?P<satellite>[^_]*)_.*\.h5'
I_GEO_TC_REGEX = r'GITCO_(?P<satellite>[^_]*)_.*\.h5'
M_GEO_REGEX = r'GMODO_(?P<satellite>[^_]*)_.*\.h5'
M_GEO_TC_REGEX = r'GMTCO_(?P<satellite>[^_]*)_.*\.h5'
DNB_GEO_REGEX = r'GDNBO_(?P<satellite>[^_]*)_.*\.h5'
DNB_GEO_TC_REGEX = r'GDNBO_(?P<satellite>[^_]*)_.*\.h5'  # FUTURE: Fix when TC DNB geolocation is available


# Structure to help with complex variables that require more than just a variable path
class FileVar(namedtuple("FileVar", ["var_path", "scaling_path", "scaling_mask_func", "nonscaling_mask_func"])):
    def __new__(cls, var_path, scaling_path=None,
                scaling_mask_func=lambda a: a >= 65528, nonscaling_mask_func=lambda a: a <= -999.0, **kwargs):
        # add default values
        var_path = var_path.format(**kwargs)
        if scaling_path:
            scaling_path = scaling_path.format(**kwargs)
        return super(FileVar, cls).__new__(cls, var_path, scaling_path, scaling_mask_func, nonscaling_mask_func)


def create_geo_file_info(file_kind, file_band, **kwargs):
    """Return a standard dictionary for an geolocation file.

    Since all of the keys are mostly the same, no need in repeating them.
    """
    kwargs["file_kind"] = file_kind
    kwargs["file_band"] = file_band
    d = {
        K_LATITUDE: FileVar('/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/Latitude', **kwargs),
        K_LONGITUDE: FileVar('/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/Longitude', **kwargs),
        # special case for TC DNB:
        K_TCLATITUDE: FileVar('/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/Latitude_TC', **kwargs),
        K_TCLONGITUDE: FileVar('/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/Longitude_TC', **kwargs),
        # K_NUMSCANS: '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/NumberOfScans',
        K_ALTITUDE: '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/Height',
        K_STARTTIME: '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/StartTime',
        K_AGGR_STARTTIME: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Aggr.AggregateBeginningTime',
        K_AGGR_STARTDATE: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Aggr.AggregateBeginningDate',
        K_AGGR_ENDTIME: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Aggr.AggregateEndingTime',
        K_AGGR_ENDDATE: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Aggr.AggregateEndingDate',
        K_SOLARZENITH: FileVar('/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/SolarZenithAngle', **kwargs),
        K_LUNARZENITH: FileVar('/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/LunarZenithAngle', **kwargs),
        K_MOONILLUM: '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/MoonIllumFraction',
        K_LAT_G_RING: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.G-Ring_Latitude',
        K_LON_G_RING: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.G-Ring_Longitude',
        K_WEST_COORD: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.West_Bounding_Coordinate',
        K_EAST_COORD: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.East_Bounding_Coordinate',
        K_NORTH_COORD: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.North_Bounding_Coordinate',
        K_SOUTH_COORD: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.South_Bounding_Coordinate',
        K_SATELLITE: '.Platform_Short_Name',
        K_DATA_PATH: '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All',
    }

    for k, v in d.items():
        if not isinstance(v, (str, unicode)):
            continue
        d[k] = d[k].format(**kwargs)

    return d


def create_im_file_info(file_kind, file_band, **kwargs):
    """Return a standard dictionary for a SVI or SVM file.

    Since all of the keys are mostly the same, no need in repeating them.
    """
    kwargs["file_kind"] = file_kind
    kwargs["file_band"] = file_band
    d = {
        K_RADIANCE: FileVar('/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/Radiance',
                            '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/RadianceFactors', **kwargs),
        K_REFLECTANCE: FileVar('/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/Reflectance',
                               '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/ReflectanceFactors', **kwargs),
        K_BTEMP: FileVar('/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/BrightnessTemperature',
                         '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/BrightnessTemperatureFactors', **kwargs),
        # K_NUMSCANS: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/NumberOfScans',
        K_MODESCAN: FileVar('/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/ModeScan', None,
                            lambda a: a > 1, lambda a: a > 1, **kwargs),
        K_MODEGRAN: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/ModeGran',
        K_QF3: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/QF3_SCAN_RDR',
        K_AGGR_STARTTIME: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateBeginningTime',
        K_AGGR_STARTDATE: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateBeginningDate',
        K_AGGR_ENDTIME: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateEndingTime',
        K_AGGR_ENDDATE: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateEndingDate',
        K_SATELLITE: ".Platform_Short_Name",
        K_DATA_PATH: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All',
    }
    for k, v in d.items():
        if not isinstance(v, (str, unicode)):
            continue
        d[k] = d[k].format(**kwargs)
    return d


def create_edr_file_info(file_kind, file_band, **kwargs):
    """Return a standard dictionary for an EDR file.
    """
    # FUTURE: We only have SST for now so this will probably need to be more generic in the future.
    kwargs["file_kind"] = file_kind
    kwargs["file_band"] = file_band
    d = {
        K_BTEMP: FileVar('/All_Data/VIIRS-{file_kind}{file_band}-EDR_All/SkinSST',
                         '/All_Data/VIIRS-{file_kind}{file_band}-EDR_All/SkinSSTFactors', **kwargs),
        K_QF3: '/All_Data/VIIRS-{file_kind}{file_band}-EDR_All/QF3_VIIRSSSTEDR',
        K_QF1: '/All_Data/VIIRS-{file_kind}{file_band}-EDR_All/QF1_VIIRSSSTEDR',
        K_AGGR_STARTTIME: '/Data_Products/VIIRS-{file_kind}{file_band}-EDR/VIIRS-{file_kind}{file_band}-EDR_Aggr.AggregateBeginningTime',
        K_AGGR_STARTDATE: '/Data_Products/VIIRS-{file_kind}{file_band}-EDR/VIIRS-{file_kind}{file_band}-EDR_Aggr.AggregateBeginningDate',
        K_AGGR_ENDTIME: '/Data_Products/VIIRS-{file_kind}{file_band}-EDR/VIIRS-{file_kind}{file_band}-EDR_Aggr.AggregateEndingTime',
        K_AGGR_ENDDATE: '/Data_Products/VIIRS-{file_kind}{file_band}-EDR/VIIRS-{file_kind}{file_band}-EDR_Aggr.AggregateEndingDate',
    }
    for k, v in d.items():
        if not isinstance(v, (str, unicode)):
            continue
        d[k] = d[k].format(**kwargs)
    return d


FILE_TYPES[FILE_TYPE_GITCO] = create_geo_file_info("IMG", "-TC")
FILE_TYPES[FILE_TYPE_GIMGO] = create_geo_file_info("IMG", "")
FILE_TYPES[FILE_TYPE_GMTCO] = create_geo_file_info("MOD", "-TC")
FILE_TYPES[FILE_TYPE_GMODO] = create_geo_file_info("MOD", "")
FILE_TYPES[FILE_TYPE_GDNBO] = create_geo_file_info("DNB", "")
# TODO:
# FILE_TYPES[FILE_TYPE_GDNBO_TC] = create_geo_file_info("DNB", "")

FILE_TYPES[FILE_TYPE_I01] = create_im_file_info("I", "1")
FILE_TYPES[FILE_TYPE_I02] = create_im_file_info("I", "2")
FILE_TYPES[FILE_TYPE_I03] = create_im_file_info("I", "3")
FILE_TYPES[FILE_TYPE_I04] = create_im_file_info("I", "4")
FILE_TYPES[FILE_TYPE_I05] = create_im_file_info("I", "5")
FILE_TYPES[FILE_TYPE_M01] = create_im_file_info("M", "1")
FILE_TYPES[FILE_TYPE_M02] = create_im_file_info("M", "2")
FILE_TYPES[FILE_TYPE_M03] = create_im_file_info("M", "3")
FILE_TYPES[FILE_TYPE_M04] = create_im_file_info("M", "4")
FILE_TYPES[FILE_TYPE_M05] = create_im_file_info("M", "5")
FILE_TYPES[FILE_TYPE_M06] = create_im_file_info("M", "6")
FILE_TYPES[FILE_TYPE_M07] = create_im_file_info("M", "7")
FILE_TYPES[FILE_TYPE_M08] = create_im_file_info("M", "8")
FILE_TYPES[FILE_TYPE_M09] = create_im_file_info("M", "9")
FILE_TYPES[FILE_TYPE_M10] = create_im_file_info("M", "10")
FILE_TYPES[FILE_TYPE_M11] = create_im_file_info("M", "11")
FILE_TYPES[FILE_TYPE_M12] = create_im_file_info("M", "12")
FILE_TYPES[FILE_TYPE_M13] = create_im_file_info("M", "13")
FILE_TYPES[FILE_TYPE_M14] = create_im_file_info("M", "14")
FILE_TYPES[FILE_TYPE_M15] = create_im_file_info("M", "15")
FILE_TYPES[FILE_TYPE_M16] = create_im_file_info("M", "16")
FILE_TYPES[FILE_TYPE_DNB] = create_im_file_info("DNB", "")

DATA_PATHS = dict((v[K_DATA_PATH], k) for k, v in FILE_TYPES.items())

# TODO:
# FILE_TYPES[FILE_TYPE_SST] = create_im_file_info("SST", ""),

# GEO_FILE_GUIDE = {
#     I_GEO_TC_REGEX: create_geo_file_info("IMG", "-TC"),
#     I_GEO_REGEX: create_geo_file_info("IMG", ""),
#     M_GEO_TC_REGEX: create_geo_file_info("MOD", "-TC"),
#     M_GEO_REGEX: create_geo_file_info("MOD", ""),
#     DNB_GEO_REGEX: create_geo_file_info("DNB", ""),
# }
#
#
# SV_FILE_GUIDE = {
#     I01_REGEX: create_im_file_info("I", "1"),
#     I02_REGEX: create_im_file_info("I", "2"),
#     I03_REGEX: create_im_file_info("I", "3"),
#     I04_REGEX: create_im_file_info("I", "4"),
#     I05_REGEX: create_im_file_info("I", "5"),
#     M01_REGEX: create_im_file_info("M", "1"),
#     M02_REGEX: create_im_file_info("M", "2"),
#     M03_REGEX: create_im_file_info("M", "3"),
#     M04_REGEX: create_im_file_info("M", "4"),
#     M05_REGEX: create_im_file_info("M", "5"),
#     M06_REGEX: create_im_file_info("M", "6"),
#     M07_REGEX: create_im_file_info("M", "7"),
#     M08_REGEX: create_im_file_info("M", "8"),
#     M09_REGEX: create_im_file_info("M", "9"),
#     M10_REGEX: create_im_file_info("M", "10"),
#     M11_REGEX: create_im_file_info("M", "11"),
#     M12_REGEX: create_im_file_info("M", "12"),
#     M13_REGEX: create_im_file_info("M", "13"),
#     M14_REGEX: create_im_file_info("M", "14"),
#     M15_REGEX: create_im_file_info("M", "15"),
#     M16_REGEX: create_im_file_info("M", "16"),
#     DNB_REGEX: create_im_file_info("DNB", ""),
#     SST_REGEX: create_edr_file_info("SST", ""),
# }


