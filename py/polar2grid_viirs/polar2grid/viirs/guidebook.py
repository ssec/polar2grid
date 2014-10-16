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
from collections import namedtuple

log = logging.getLogger(__name__)
UTC = UTC()

K_LATITUDE = "LatitudeVar"
K_LONGITUDE = "LongitudeVar"
K_RADIANCE = "RadianceVar"
K_REFLECTANCE = "ReflectanceVar"
K_BTEMP = "BrightnessTemperatureVar"
K_SOLARZENITH = "SolarZenithVar"
K_LUNARZENITH = "LunarZenithVar"
K_MOONILLUM = "LunarIlluminationVar"
K_ALTITUDE = "AltitudeVar"
K_RADIANCE_FACTORS = "RadianceFactorsVar"
K_REFLECTANCE_FACTORS = "ReflectanceFactorsVar"
K_BTEMP_FACTORS = "BrightnessTemperatureFactorsVar"
K_SST_FACTORS = "SeaSurfaceTemperatureFactorsVar"
K_STARTTIME = "StartTimeVar"
K_AGGR_STARTTIME = "AggrStartTimeVar"
K_AGGR_STARTDATE = "AggrStartDateVar"
K_AGGR_ENDTIME = "AggrEndTimeVar"
K_AGGR_ENDDATE = "AggrEndDateVar"
K_NUMSCANS = "NumberOfScansVar"
K_ROWSPERSCAN = "RowsPerScanVar"
K_MODESCAN = "ModeScanVar"
K_MODEGRAN = "ModeGranVar"
K_QF1 = "QF1Var"
K_QF3 = "QF3Var"
K_LAT_G_RING = "LatGRingAttr"
K_LON_G_RING = "LonGRingAttr"
K_WEST_COORD = "WestCoordinateAttr"
K_EAST_COORD = "EastCoordinateAttr"
K_NORTH_COORD = "NorthCoordinateAttr"
K_SOUTH_COORD = "SouthCoordinateAttr"

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
    }

    for k, v in d.items():
        if not isinstance(v, (str, unicode)):
            continue
        d[k] = d[k].format(**kwargs)

    return d


GEO_FILE_GUIDE = {
    I_GEO_TC_REGEX: create_geo_file_info("IMG", "-TC"),
    I_GEO_REGEX: create_geo_file_info("IMG", ""),
    M_GEO_TC_REGEX: create_geo_file_info("MOD", "-TC"),
    M_GEO_REGEX: create_geo_file_info("MOD", ""),
    DNB_GEO_REGEX: create_geo_file_info("DNB", ""),
}


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
        K_NUMSCANS: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/NumberOfScans',
        K_MODESCAN: FileVar('/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/ModeScan', None,
                            lambda a: a > 1, lambda a: a > 1, **kwargs),
        K_MODEGRAN: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/ModeGran',
        K_QF3: '/All_Data/VIIRS-{file_kind}{file_band}-SDR_All/QF3_SCAN_RDR',
        K_AGGR_STARTTIME: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateBeginningTime',
        K_AGGR_STARTDATE: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateBeginningDate',
        K_AGGR_ENDTIME: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateEndingTime',
        K_AGGR_ENDDATE: '/Data_Products/VIIRS-{file_kind}{file_band}-SDR/VIIRS-{file_kind}{file_band}-SDR_Aggr.AggregateEndingDate',
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
    SST_REGEX: create_edr_file_info("SST", ""),
}
ALL_FILE_REGEXES = SV_FILE_GUIDE.keys() + GEO_FILE_GUIDE.keys()


def make_polygon_tuple(lon_ring, lat_ring):
    return tuple(tuple(x) for x in zip(lon_ring, lat_ring))


def calculate_bbox_bounds(wests, easts, norths, souths, fill_value=DEFAULT_FILL_VALUE):
    """Given a list of west most points, east-most, north-most, and
    south-most points, calculate the bounds for the overall aggregate
    granule. This is needed since we don't no if the last granule
    or the first granule in an aggregate SDR file is south-most, east-most,
    etc.
    """
    wests = np.array(wests)
    wests = wests[(wests >= -180) & (wests <= 180)]
    easts = np.array(easts)
    easts = easts[(easts >= -180) & (easts <= 180)]
    norths = np.array(norths)
    norths = norths[(norths >= -90) & (norths <= 90)]
    souths = np.array(souths)
    souths = souths[(souths >= -90) & (souths <= 90)]

    if norths.shape[0] == 0:
        nbound = fill_value
    else:
        nbound = norths.max()
    if souths.shape[0] == 0:
        sbound = fill_value
    else:
        sbound = souths.min()

    if wests.shape[0] == 0:
        # If we didn't have any valid coordinates, its just a fill value
        wbound = fill_value
    elif wests.max() - wests.min() > 180:
        # We are crossing the dateline
        wbound = wests[wests > 0].min()
    else:
        # We aren't crossing the dateline so simple calculation
        wbound = min(wests)

    if easts.shape[0] == 0:
        # If we didn't have any valid coordinates, its just a fill value
        ebound = fill_value
    elif easts.max() - easts.min() > 180:
        # We are crossing the dateline
        ebound = easts[easts < 0].max()
    else:
        ebound = max(easts)

    return wbound, ebound, nbound, sbound


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
