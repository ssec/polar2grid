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
import numpy as np

import os
import sys
import logging

log = logging.getLogger(__name__)
UTC = UTC()

K_LATITUDE             = "LatitudeVar"
K_LONGITUDE            = "LongitudeVar"
K_RADIANCE             = "RadianceVar"
K_REFLECTANCE          = "ReflectanceVar"
K_BTEMP                = "BrightnessTemperatureVar"
K_SOLARZENITH          = "SolarZenithVar"
K_LUNARZENITH          = "LunarZenithVar"
K_MOONILLUM            = "LunarIlluminationVar"
K_ALTITUDE             = "AltitudeVar"
K_RADIANCE_FACTORS     = "RadianceFactorsVar"
K_REFLECTANCE_FACTORS  = "ReflectanceFactorsVar"
K_BTEMP_FACTORS        = "BrightnessTemperatureFactorsVar"
K_STARTTIME            = "StartTimeVar"
K_AGGR_STARTTIME       = "AggrStartTimeVar"
K_AGGR_STARTDATE       = "AggrStartDateVar"
K_AGGR_ENDTIME         = "AggrEndTimeVar"
K_AGGR_ENDDATE         = "AggrEndDateVar"
K_NUMSCANS             = "NumberOfScansVar"
K_ROWSPERSCAN          = "RowsPerScanVar"
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
# Geolocation regexes
I_GEO_REGEX = r'GIMGO_(?P<satellite>[^_]*)_.*\.h5'
I_GEO_TC_REGEX = r'GITCO_(?P<satellite>[^_]*)_.*\.h5'
M_GEO_REGEX = r'GMODO_(?P<satellite>[^_]*)_.*\.h5'
M_GEO_TC_REGEX = r'GMTCO_(?P<satellite>[^_]*)_.*\.h5'
DNB_GEO_REGEX = r'GDNBO_(?P<satellite>[^_]*)_.*\.h5'
DNB_GEO_TC_REGEX = r'GDNBO_(?P<satellite>[^_]*)_.*\.h5' # FUTURE: Fix when TC DNB geolocation is available
# Regex organization/grouping
ALL_FILE_REGEXES = [
    I01_REGEX,
    I02_REGEX,
    I03_REGEX,
    I04_REGEX,
    I05_REGEX,
    M01_REGEX,
    M02_REGEX,
    M03_REGEX,
    M04_REGEX,
    M05_REGEX,
    M06_REGEX,
    M07_REGEX,
    M08_REGEX,
    M09_REGEX,
    M10_REGEX,
    M11_REGEX,
    M12_REGEX,
    M13_REGEX,
    M14_REGEX,
    M15_REGEX,
    M16_REGEX,
    DNB_REGEX,
    I_GEO_REGEX,
    I_GEO_TC_REGEX,
    M_GEO_REGEX,
    M_GEO_TC_REGEX,
    DNB_GEO_REGEX
    # FUTURE: DNB_GEO_TC_REGEX
]


def create_geo_file_info(file_kind, file_band, **kwargs):
    """Return a standard dictionary for an geolocation file.

    Since all of the keys are mostly the same, no need in repeating them.
    """
    d = {
        K_LATITUDE:    '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/Latitude',
        K_LONGITUDE:   '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/Longitude',
        K_ALTITUDE:    '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/Height',
        K_STARTTIME:   '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/StartTime',
        K_AGGR_STARTTIME: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Aggr.AggregateBeginningTime',
        K_AGGR_STARTDATE: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Aggr.AggregateBeginningDate',
        K_AGGR_ENDTIME: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Aggr.AggregateEndingTime',
        K_AGGR_ENDDATE: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Aggr.AggregateEndingDate',
        K_SOLARZENITH: '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/SolarZenithAngle',
        K_LUNARZENITH: '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/LunarZenithAngle',
        K_MOONILLUM:   '/All_Data/VIIRS-{file_kind}-GEO{file_band}_All/MoonIllumFraction',
        K_LAT_G_RING:  '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.G-Ring_Latitude',
        K_LON_G_RING:  '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.G-Ring_Longitude',
        K_WEST_COORD:  '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.West_Bounding_Coordinate',
        K_EAST_COORD:  '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.East_Bounding_Coordinate',
        K_NORTH_COORD: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.North_Bounding_Coordinate',
        K_SOUTH_COORD: '/Data_Products/VIIRS-{file_kind}-GEO{file_band}/VIIRS-{file_kind}-GEO{file_band}_Gran_0.South_Bounding_Coordinate',
    }

    for k, v in d.items():
        d[k] = d[k].format(file_kind=file_kind, file_band=file_band, **kwargs)

    if K_NUMSCANS in kwargs:
        d[K_NUMSCANS] = kwargs.pop(K_NUMSCANS)
    if K_ROWSPERSCAN in kwargs:
        d[K_ROWSPERSCAN] = kwargs.pop(K_ROWSPERSCAN)

    return d

GEO_FILE_GUIDE = {
    I_GEO_TC_REGEX: create_geo_file_info("IMG", "-TC"),
    I_GEO_REGEX: create_geo_file_info("IMG", ""),
    M_GEO_TC_REGEX: create_geo_file_info("MOD", "-TC"),
    M_GEO_REGEX: create_geo_file_info("MOD", ""),
    DNB_GEO_REGEX: create_geo_file_info("DNB", ""),
}


def create_im_file_info(file_kind, file_band, **kwargs):
    """Return a standard dictionary for an SVI or SVM file.

    Since all of the keys are mostly the same, no need in repeating them.
    """
    d = {
        K_RADIANCE: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/Radiance',
        K_REFLECTANCE: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/Reflectance',
        K_BTEMP: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/BrightnessTemperature',
        K_RADIANCE_FACTORS: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/RadianceFactors',
        K_REFLECTANCE_FACTORS: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/ReflectanceFactors',
        K_BTEMP_FACTORS: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/BrightnessTemperatureFactors',
        K_NUMSCANS: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/NumberOfScans',
        K_MODESCAN: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/ModeScan',
        K_MODEGRAN: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/ModeGran',
        K_QF3: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/QF3_SCAN_RDR',
        K_AGGR_STARTTIME: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateBeginningTime',
        K_AGGR_STARTDATE: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateBeginningDate',
        K_AGGR_ENDTIME: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateEndingTime',
        K_AGGR_ENDDATE: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateEndingDate',
    }
    for k, v in d.items():
        d[k] = d[k].format(file_kind=file_kind, file_band=file_band, **kwargs)
    return d

SV_FILE_GUIDE = {
    I01_REGEX: create_im_file_info("I", "1"),
    I02_REGEX: create_im_file_info("I", "2"),
    I03_REGEX: create_im_file_info("I", "3"),
    I04_REGEX: create_im_file_info("I", "4"),
    I05_REGEX: create_im_file_info("I", "5"),
    M01_REGEX: create_im_file_info("M", "1"),
    M02_REGEX: create_im_file_info("M", "2"),
    M03_REGEX: create_im_file_info("M", "3"),
    M04_REGEX: create_im_file_info("M", "4"),
    M05_REGEX: create_im_file_info("M", "5"),
    M06_REGEX: create_im_file_info("M", "6"),
    M07_REGEX: create_im_file_info("M", "7"),
    M08_REGEX: create_im_file_info("M", "8"),
    M09_REGEX: create_im_file_info("M", "9"),
    M10_REGEX: create_im_file_info("M", "10"),
    M11_REGEX: create_im_file_info("M", "11"),
    M12_REGEX: create_im_file_info("M", "12"),
    M13_REGEX: create_im_file_info("M", "13"),
    M14_REGEX: create_im_file_info("M", "14"),
    M15_REGEX: create_im_file_info("M", "15"),
    M16_REGEX: create_im_file_info("M", "16"),
    DNB_REGEX: create_im_file_info("DNB", ""),
}

SCALING_FACTORS = {
    K_REFLECTANCE: K_REFLECTANCE_FACTORS,
    K_RADIANCE: K_RADIANCE_FACTORS,
    K_BTEMP: K_BTEMP_FACTORS,
}

# missing value sentinels for different datasets
# 0 if scaling exists, 1 if scaling is None
MASKING_GUIDE = {
    K_REFLECTANCE: (lambda a: a >= 65528, lambda a: a < -999.0),
    K_RADIANCE: (lambda a: a >= 65528, lambda a: a < -999.0),
    K_BTEMP: (lambda a: a >= 65528, lambda a: a < -999.0),
    K_SOLARZENITH: (lambda a: a >= 65528, lambda a: a < -999.0),
    K_LUNARZENITH: (lambda a: a >= 65528, lambda a: a < -999.0),
    K_MODESCAN: (lambda a: a > 1, lambda a: a > 1),
    K_LATITUDE: (lambda a: a >= 65528, lambda a: a <= -999),
    K_LONGITUDE: (lambda a: a >= 65528, lambda a: a <= -999)
}


def make_polygon_tuple(lon_ring, lat_ring):
    return tuple(tuple(x) for x in zip(lon_ring,lat_ring))


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


    return wbound,ebound,nbound,sbound

def sort_files_by_nav_uid(filepaths):
    """Logic is duplicated from file_info-like method because it has less
    overhead and this function was required a different way of accessing the
    data.
    """
    # FIXME: Uses old BKIND_* keying in NAV_SET_GUIDE
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


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
            help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(3, args.verbosity)])

    # TODO

if __name__ == '__main__':
    sys.exit(main())
