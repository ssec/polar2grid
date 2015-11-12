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
"""The VIIRS Frontend operates on Science Data Record (SDR) and Environmental Data Record (EDR) files from
the Suomi National Polar-orbiting Partnership's (NPP) Visible/Infrared
Imager Radiometer Suite (VIIRS) instrument. The VIIRS frontend ignores filenames and uses internal
file content to determine the type of file being provided, but SDR and EDR HDF5 files are typically named as below
and have corresponding geolocation files::

    SVI01_npp_d20120225_t1801245_e1802487_b01708_c20120226002130255476_noaa_ops.h5

The VIIRS frontend supports all basic SDR bands created by the instrument. These are identified as the products shown
below. It supports terrain corrected or non-terrain corrected navigation files. Geolocation files must be included
when specifying filepaths to frontends and glue scripts. The VIIRS frontend can be specified to the ``p2g_glue`` script
with the frontend name ``viirs``.

    +---------------------------+--------------------------------------------+
    | Product Name              | Description                                |
    +===========================+============================================+
    | i01                       | I01 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | i02                       | I02 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | i03                       | I03 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | i04                       | I04 Brightness Temperature Band            |
    +---------------------------+--------------------------------------------+
    | i05                       | I05 Brightness Temperature Band            |
    +---------------------------+--------------------------------------------+
    | i01_rad                   | I01 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | i02_rad                   | I02 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | i03_rad                   | I03 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | i04_rad                   | I04 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | i05_rad                   | I05 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m01                       | M01 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | m02                       | M02 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | m03                       | M03 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | m04                       | M04 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | m05                       | M05 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | m06                       | M06 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | m07                       | M07 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | m08                       | M08 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | m09                       | M09 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | m10                       | M10 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | m11                       | M11 Reflectance Band                       |
    +---------------------------+--------------------------------------------+
    | m12                       | M12 Brightness Temperature Band            |
    +---------------------------+--------------------------------------------+
    | m13                       | M13 Brightness Temperature Band            |
    +---------------------------+--------------------------------------------+
    | m14                       | M14 Brightness Temperature Band            |
    +---------------------------+--------------------------------------------+
    | m15                       | M15 Brightness Temperature Band            |
    +---------------------------+--------------------------------------------+
    | m16                       | M16 Brightness Temperature Band            |
    +---------------------------+--------------------------------------------+
    | m01_rad                   | M01 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m02_rad                   | M02 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m03_rad                   | M03 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m04_rad                   | M04 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m05_rad                   | M05 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m06_rad                   | M06 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m07_rad                   | M07 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m08_rad                   | M08 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m09_rad                   | M09 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m10_rad                   | M10 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m11_rad                   | M11 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m12_rad                   | M12 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m13_rad                   | M13 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m14_rad                   | M14 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m15_rad                   | M15 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | m16_rad                   | M16 Radiance Band                          |
    +---------------------------+--------------------------------------------+
    | dnb                       | Raw DNB Band (not useful for images)       |
    +---------------------------+--------------------------------------------+
    | histogram_dnb             | Histogram Equalized DNB Band               |
    +---------------------------+--------------------------------------------+
    | adaptive_dnb              | Adaptive Histogram Equalized DNB Band      |
    +---------------------------+--------------------------------------------+
    | dynamic_dnb               | Dynamic DNB Band from Steve Miller and     |
    |                           | Curtis Seaman. Uses erf to scale the data. |
    +---------------------------+--------------------------------------------+
    | ifog                      | Temperature difference between I05 and I04 |
    +---------------------------+--------------------------------------------+
    | i_solar_zenith_angle      | I Band Solar Zenith Angle                  |
    +---------------------------+--------------------------------------------+
    | i_solar_azimuth_angle     | I Band Solar Azimuth Angle                 |
    +---------------------------+--------------------------------------------+
    | i_sat_zenith_angle        | I Band Satellite Zenith Angle              |
    +---------------------------+--------------------------------------------+
    | i_sat_azimuth_angle       | I Band Satellite Azimuth Angle             |
    +---------------------------+--------------------------------------------+
    | m_solar_zenith_angle      | M Band Solar Zenith Angle                  |
    +---------------------------+--------------------------------------------+
    | m_solar_azimuth_angle     | M Band Solar Azimuth Angle                 |
    +---------------------------+--------------------------------------------+
    | m_sat_zenith_angle        | M Band Satellite Zenith Angle              |
    +---------------------------+--------------------------------------------+
    | m_sat_azimuth_angle       | M Band Satellite Azimuth Angle             |
    +---------------------------+--------------------------------------------+
    | dnb_solar_zenith_angle    | DNB Band Solar Zenith Angle                |
    +---------------------------+--------------------------------------------+
    | dnb_solar_azimuth_angle   | DNB Band Solar Azimuth Angle               |
    +---------------------------+--------------------------------------------+
    | dnb_sat_zenith_angle      | DNB Band Satellite Zenith Angle            |
    +---------------------------+--------------------------------------------+
    | dnb_sat_azimuth_angle     | DNB Band Satellite Azimuth Angle           |
    +---------------------------+--------------------------------------------+
    | dnb_lunar_zenith_angle    | DNB Band Lunar Zenith Angle                |
    +---------------------------+--------------------------------------------+
    | dnb_lunar_azimuth_angle   | DNB Band Lunar Azimuth Angle               |
    +---------------------------+--------------------------------------------+


For reflectance/visible products a check is done to make sure that at least
10% of the swath is day time. Data is considered day time where solar zenith
angle is less than 100 degrees.

|

.. note::

    Terrain corrected geolocation for the DNB band has recently been added and is included in the non-TC file (GDNBO).
    This may cause some confusion to users as the VIIRS frontend currently only checks for terrain corrected data. To
    use non-TC data use the ``--no-tc`` flag (described below).

:author:       David Hoese (davidh)
:author:       Ray Garcia (rayg)
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012-2015 University of Wisconsin SSEC. All rights reserved.
:date:         Oct 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

from . import guidebook
# FIXME: Actually use the Geo Readers
from .io import VIIRSSDRMultiReader, HDF5Reader
from polar2grid.core import containers, histogram, roles
from polar2grid.core.frontend_utils import ProductDict, GeoPairDict
from .prescale import adaptive_dnb_scale, dnb_scale
import numpy
from scipy.special import erf

import os
import sys
import logging

LOG = logging.getLogger(__name__)

# XXX: For now anything having to do directly with products is kept in the swath module
# XXX: Stuff about the actual files and what keys are what are kept in the guidebook
### PRODUCT KEYS ###
#   basic SDRs
PRODUCT_I01 = "i01"
PRODUCT_I02 = "i02"
PRODUCT_I03 = "i03"
PRODUCT_I04 = "i04"
PRODUCT_I05 = "i05"
PRODUCT_I01_RAD = "i01_rad"
PRODUCT_I02_RAD = "i02_rad"
PRODUCT_I03_RAD = "i03_rad"
PRODUCT_I04_RAD = "i04_rad"
PRODUCT_I05_RAD = "i05_rad"

PRODUCT_M01 = "m01"
PRODUCT_M02 = "m02"
PRODUCT_M03 = "m03"
PRODUCT_M04 = "m04"
PRODUCT_M05 = "m05"
PRODUCT_M06 = "m06"
PRODUCT_M07 = "m07"
PRODUCT_M08 = "m08"
PRODUCT_M09 = "m09"
PRODUCT_M10 = "m10"
PRODUCT_M11 = "m11"
PRODUCT_M12 = "m12"
PRODUCT_M13 = "m13"
PRODUCT_M14 = "m14"
PRODUCT_M15 = "m15"
PRODUCT_M16 = "m16"
PRODUCT_M01_RAD = "m01_rad"
PRODUCT_M02_RAD = "m02_rad"
PRODUCT_M03_RAD = "m03_rad"
PRODUCT_M04_RAD = "m04_rad"
PRODUCT_M05_RAD = "m05_rad"
PRODUCT_M06_RAD = "m06_rad"
PRODUCT_M07_RAD = "m07_rad"
PRODUCT_M08_RAD = "m08_rad"
PRODUCT_M09_RAD = "m09_rad"
PRODUCT_M10_RAD = "m10_rad"
PRODUCT_M11_RAD = "m11_rad"
PRODUCT_M12_RAD = "m12_rad"
PRODUCT_M13_RAD = "m13_rad"
PRODUCT_M14_RAD = "m14_rad"
PRODUCT_M15_RAD = "m15_rad"
PRODUCT_M16_RAD = "m16_rad"
PRODUCT_DNB = "dnb"
PRODUCT_DNB_SZA = "dnb_solar_zenith_angle"
PRODUCT_DNB_SAA = "dnb_solar_azimuth_angle"
PRODUCT_DNB_SAT_ZA = "dnb_sat_zenith_angle"
PRODUCT_DNB_SAT_AA = "dnb_sat_azimuth_angle"
PRODUCT_DNB_LZA = "dnb_lunar_zenith_angle"
PRODUCT_DNB_LAA = "dnb_lunar_azimuth_angle"
PRODUCT_M_SZA = "m_solar_zenith_angle"
PRODUCT_M_SAA = "m_solar_azimuth_angle"
PRODUCT_M_SAT_ZA = "m_sat_zenith_angle"
PRODUCT_M_SAT_AA = "m_sat_azimuth_angle"
PRODUCT_I_SZA = "i_solar_zenith_angle"
PRODUCT_I_SAA = "i_solar_azimuth_angle"
PRODUCT_I_SAT_ZA = "i_sat_zenith_angle"
PRODUCT_I_SAT_AA = "i_sat_azimuth_angle"
PRODUCT_IFOG = "ifog"
PRODUCT_HISTOGRAM_DNB = "histogram_dnb"
PRODUCT_ADAPTIVE_DNB = "adaptive_dnb"
PRODUCT_DYNAMIC_DNB = "dynamic_dnb"
#   adaptive IR
PRODUCT_ADAPTIVE_I04 = "adaptive_i04"
PRODUCT_ADAPTIVE_I05 = "adaptive_i05"
PRODUCT_ADAPTIVE_M12 = "adaptive_m12"
PRODUCT_ADAPTIVE_M13 = "adaptive_m13"
PRODUCT_ADAPTIVE_M14 = "adaptive_m14"
PRODUCT_ADAPTIVE_M15 = "adaptive_m15"
PRODUCT_ADAPTIVE_M16 = "adaptive_m16"
PRODUCT_SST = "sst"

# Geolocation "Products"
# These products aren't really products at the moment and should only be used as navigation for the above products
PRODUCT_I_LAT = "i_latitude"
PRODUCT_I_LON = "i_longitude"
PRODUCT_M_LAT = "m_latitude"
PRODUCT_M_LON = "m_longitude"
PRODUCT_DNB_LAT = "dnb_latitude"
PRODUCT_DNB_LON = "dnb_longitude"

ADAPTIVE_BT_PRODUCTS = [
    PRODUCT_ADAPTIVE_I04, PRODUCT_ADAPTIVE_I05,
    PRODUCT_ADAPTIVE_M12, PRODUCT_ADAPTIVE_M13, PRODUCT_ADAPTIVE_M14, PRODUCT_ADAPTIVE_M15, PRODUCT_ADAPTIVE_M16
]
I_PRODUCTS = [
    PRODUCT_I01,
    PRODUCT_I02,
    PRODUCT_I03,
    PRODUCT_I04,
    PRODUCT_I05,
]
M_PRODUCTS = [
    PRODUCT_M01,
    PRODUCT_M02,
    PRODUCT_M03,
    PRODUCT_M04,
    PRODUCT_M05,
    PRODUCT_M06,
    PRODUCT_M07,
    PRODUCT_M08,
    PRODUCT_M09,
    PRODUCT_M10,
    PRODUCT_M11,
    PRODUCT_M12,
    PRODUCT_M13,
    PRODUCT_M14,
    PRODUCT_M15,
    PRODUCT_M16,
]
DNB_ANGLE_PRODUCTS = [
    PRODUCT_DNB_SZA,
    PRODUCT_DNB_SAA,
    PRODUCT_DNB_LZA,
    PRODUCT_DNB_LAA,
    PRODUCT_DNB_SAT_ZA,
    PRODUCT_DNB_SAT_AA,
]
I_ANGLE_PRODUCTS = [
    PRODUCT_I_SZA,
    PRODUCT_I_SAA,
    PRODUCT_I_SAT_ZA,
    PRODUCT_I_SAT_AA,
]
M_ANGLE_PRODUCTS = [
    PRODUCT_M_SZA,
    PRODUCT_M_SAA,
    PRODUCT_M_SAT_ZA,
    PRODUCT_M_SAT_AA,
]
I_RAD_PRODUCTS = [
    PRODUCT_I01_RAD,
    PRODUCT_I02_RAD,
    PRODUCT_I03_RAD,
    PRODUCT_I04_RAD,
    PRODUCT_I05_RAD,
]
M_RAD_PRODUCTS = [
    PRODUCT_M01_RAD,
    PRODUCT_M02_RAD,
    PRODUCT_M03_RAD,
    PRODUCT_M04_RAD,
    PRODUCT_M05_RAD,
    PRODUCT_M06_RAD,
    PRODUCT_M07_RAD,
    PRODUCT_M08_RAD,
    PRODUCT_M09_RAD,
    PRODUCT_M10_RAD,
    PRODUCT_M11_RAD,
    PRODUCT_M12_RAD,
    PRODUCT_M13_RAD,
    PRODUCT_M14_RAD,
    PRODUCT_M15_RAD,
    PRODUCT_M16_RAD,
]

PRODUCTS = ProductDict()
GEO_PAIRS = GeoPairDict()

PAIR_INAV = "inav"
PAIR_MNAV = "mnav"
PAIR_DNBNAV = "dnbnav"
# Cool, there's no way to get rows per scan from the file
GEO_PAIRS.add_pair(PAIR_INAV, PRODUCT_I_LON, PRODUCT_I_LAT, 32, solar_zenith_angle=PRODUCT_I_SZA)
GEO_PAIRS.add_pair(PAIR_MNAV, PRODUCT_M_LON, PRODUCT_M_LAT, 16, solar_zenith_angle=PRODUCT_M_SZA)
GEO_PAIRS.add_pair(PAIR_DNBNAV, PRODUCT_DNB_LON, PRODUCT_DNB_LAT, 16)

# TODO: Add description and units
PRODUCTS.add_product(PRODUCT_I_LON, PAIR_INAV, "longitude", (guidebook.FILE_TYPE_GITCO, guidebook.FILE_TYPE_GIMGO), guidebook.K_LONGITUDE)
PRODUCTS.add_product(PRODUCT_I_LAT, PAIR_INAV, "latitude", (guidebook.FILE_TYPE_GITCO, guidebook.FILE_TYPE_GIMGO), guidebook.K_LATITUDE)
PRODUCTS.add_product(PRODUCT_M_LON, PAIR_MNAV, "longitude", (guidebook.FILE_TYPE_GMTCO, guidebook.FILE_TYPE_GMODO), guidebook.K_LONGITUDE)
PRODUCTS.add_product(PRODUCT_M_LAT, PAIR_MNAV, "latitude", (guidebook.FILE_TYPE_GMTCO, guidebook.FILE_TYPE_GMODO), guidebook.K_LATITUDE)
PRODUCTS.add_product(PRODUCT_DNB_LON, PAIR_DNBNAV, "longitude", (guidebook.FILE_TYPE_GDNBO, guidebook.FILE_TYPE_GDNBO), (guidebook.K_TCLONGITUDE, guidebook.K_LONGITUDE))
PRODUCTS.add_product(PRODUCT_DNB_LAT, PAIR_DNBNAV, "latitude", (guidebook.FILE_TYPE_GDNBO, guidebook.FILE_TYPE_GDNBO), (guidebook.K_TCLATITUDE, guidebook.K_LATITUDE))

PRODUCTS.add_product(PRODUCT_DNB_SZA, PAIR_DNBNAV, "solar_zenith_angle", guidebook.FILE_TYPE_GDNBO, guidebook.K_SOLARZENITH)
PRODUCTS.add_product(PRODUCT_DNB_SAA, PAIR_DNBNAV, "solar_azimuth_angle", guidebook.FILE_TYPE_GDNBO, guidebook.K_SOLARAZIMUTH)
PRODUCTS.add_product(PRODUCT_DNB_LZA, PAIR_DNBNAV, "lunar_zenith_angle", guidebook.FILE_TYPE_GDNBO, guidebook.K_LUNARZENITH)
PRODUCTS.add_product(PRODUCT_DNB_LAA, PAIR_DNBNAV, "lunar_azimuth_angle", guidebook.FILE_TYPE_GDNBO, guidebook.K_LUNARAZIMUTH)
PRODUCTS.add_product(PRODUCT_DNB_SAT_ZA, PAIR_DNBNAV, "satellite_zenith_angle", guidebook.FILE_TYPE_GDNBO, guidebook.K_SATZENITH)
PRODUCTS.add_product(PRODUCT_DNB_SAT_AA, PAIR_DNBNAV, "satellite_azimuth_angle", guidebook.FILE_TYPE_GDNBO, guidebook.K_SATAZIMUTH)
PRODUCTS.add_product(PRODUCT_I_SZA, PAIR_INAV, "solar_zenith_angle", (guidebook.FILE_TYPE_GITCO, guidebook.FILE_TYPE_GIMGO), guidebook.K_SOLARZENITH)
PRODUCTS.add_product(PRODUCT_I_SAA, PAIR_INAV, "solar_azimuth_angle", (guidebook.FILE_TYPE_GITCO, guidebook.FILE_TYPE_GIMGO), guidebook.K_SOLARAZIMUTH)
PRODUCTS.add_product(PRODUCT_I_SAT_ZA, PAIR_INAV, "satellite_zenith_angle", (guidebook.FILE_TYPE_GITCO, guidebook.FILE_TYPE_GIMGO), guidebook.K_SATZENITH)
PRODUCTS.add_product(PRODUCT_I_SAT_AA, PAIR_INAV, "satellite_azimuth_angle", (guidebook.FILE_TYPE_GITCO, guidebook.FILE_TYPE_GIMGO), guidebook.K_SATAZIMUTH)
PRODUCTS.add_product(PRODUCT_M_SZA, PAIR_MNAV, "solar_zenith_angle", (guidebook.FILE_TYPE_GMTCO, guidebook.FILE_TYPE_GMODO), guidebook.K_SOLARZENITH)
PRODUCTS.add_product(PRODUCT_M_SAA, PAIR_MNAV, "solar_azimuth_angle", (guidebook.FILE_TYPE_GMTCO, guidebook.FILE_TYPE_GMODO), guidebook.K_SOLARAZIMUTH)
PRODUCTS.add_product(PRODUCT_M_SAT_ZA, PAIR_MNAV, "satellite_zenith_angle", (guidebook.FILE_TYPE_GMTCO, guidebook.FILE_TYPE_GMODO), guidebook.K_SATZENITH)
PRODUCTS.add_product(PRODUCT_M_SAT_AA, PAIR_MNAV, "satellite_azimuth_angle", (guidebook.FILE_TYPE_GMTCO, guidebook.FILE_TYPE_GMODO), guidebook.K_SATAZIMUTH)

PRODUCTS.add_product(PRODUCT_I01, PAIR_INAV, "reflectance", guidebook.FILE_TYPE_I01, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_I_SZA,))
PRODUCTS.add_product(PRODUCT_I02, PAIR_INAV, "reflectance", guidebook.FILE_TYPE_I02, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_I_SZA,))
PRODUCTS.add_product(PRODUCT_I03, PAIR_INAV, "reflectance", guidebook.FILE_TYPE_I03, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_I_SZA,))
PRODUCTS.add_product(PRODUCT_I04, PAIR_INAV, "brightness_temperature", guidebook.FILE_TYPE_I04, guidebook.K_BTEMP)
PRODUCTS.add_product(PRODUCT_I05, PAIR_INAV, "brightness_temperature", guidebook.FILE_TYPE_I05, guidebook.K_BTEMP)
PRODUCTS.add_product(PRODUCT_M01, PAIR_MNAV, "reflectance", guidebook.FILE_TYPE_M01, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_M_SZA,))
PRODUCTS.add_product(PRODUCT_M02, PAIR_MNAV, "reflectance", guidebook.FILE_TYPE_M02, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_M_SZA,))
PRODUCTS.add_product(PRODUCT_M03, PAIR_MNAV, "reflectance", guidebook.FILE_TYPE_M03, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_M_SZA,))
PRODUCTS.add_product(PRODUCT_M04, PAIR_MNAV, "reflectance", guidebook.FILE_TYPE_M04, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_M_SZA,))
PRODUCTS.add_product(PRODUCT_M05, PAIR_MNAV, "reflectance", guidebook.FILE_TYPE_M05, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_M_SZA,))
PRODUCTS.add_product(PRODUCT_M06, PAIR_MNAV, "reflectance", guidebook.FILE_TYPE_M06, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_M_SZA,))
PRODUCTS.add_product(PRODUCT_M07, PAIR_MNAV, "reflectance", guidebook.FILE_TYPE_M07, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_M_SZA,))
PRODUCTS.add_product(PRODUCT_M08, PAIR_MNAV, "reflectance", guidebook.FILE_TYPE_M08, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_M_SZA,))
PRODUCTS.add_product(PRODUCT_M09, PAIR_MNAV, "reflectance", guidebook.FILE_TYPE_M09, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_M_SZA,))
PRODUCTS.add_product(PRODUCT_M10, PAIR_MNAV, "reflectance", guidebook.FILE_TYPE_M10, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_M_SZA,))
PRODUCTS.add_product(PRODUCT_M11, PAIR_MNAV, "reflectance", guidebook.FILE_TYPE_M11, guidebook.K_REFLECTANCE, dependencies=(PRODUCT_M_SZA,))
PRODUCTS.add_product(PRODUCT_M12, PAIR_MNAV, "brightness_temperature", guidebook.FILE_TYPE_M12, guidebook.K_BTEMP)
PRODUCTS.add_product(PRODUCT_M13, PAIR_MNAV, "brightness_temperature", guidebook.FILE_TYPE_M13, guidebook.K_BTEMP)
PRODUCTS.add_product(PRODUCT_M14, PAIR_MNAV, "brightness_temperature", guidebook.FILE_TYPE_M14, guidebook.K_BTEMP)
PRODUCTS.add_product(PRODUCT_M15, PAIR_MNAV, "brightness_temperature", guidebook.FILE_TYPE_M15, guidebook.K_BTEMP)
PRODUCTS.add_product(PRODUCT_M16, PAIR_MNAV, "brightness_temperature", guidebook.FILE_TYPE_M16, guidebook.K_BTEMP)
PRODUCTS.add_product(PRODUCT_DNB, PAIR_DNBNAV, "radiance", guidebook.FILE_TYPE_DNB, guidebook.K_RADIANCE)

# Special Radiance Versions of the products
PRODUCTS.add_product(PRODUCT_I01_RAD, PAIR_INAV, "radiance", guidebook.FILE_TYPE_I01, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_I02_RAD, PAIR_INAV, "radiance", guidebook.FILE_TYPE_I02, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_I03_RAD, PAIR_INAV, "radiance", guidebook.FILE_TYPE_I03, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_I04_RAD, PAIR_INAV, "radiance", guidebook.FILE_TYPE_I04, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_I05_RAD, PAIR_INAV, "radiance", guidebook.FILE_TYPE_I05, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M01_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M01, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M02_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M02, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M03_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M03, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M04_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M04, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M05_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M05, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M06_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M06, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M07_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M07, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M08_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M08, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M09_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M09, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M10_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M10, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M11_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M11, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M12_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M12, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M13_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M13, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M14_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M14, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M15_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M15, guidebook.K_RADIANCE)
PRODUCTS.add_product(PRODUCT_M16_RAD, PAIR_MNAV, "radiance", guidebook.FILE_TYPE_M16, guidebook.K_RADIANCE)

PRODUCTS.add_product(PRODUCT_IFOG, PAIR_INAV, "temperature_difference", dependencies=(PRODUCT_I05, PRODUCT_I04, PRODUCT_I_SZA))
PRODUCTS.add_product(PRODUCT_HISTOGRAM_DNB, PAIR_DNBNAV, "equalized_radiance", dependencies=(PRODUCT_DNB, PRODUCT_DNB_SZA))
PRODUCTS.add_product(PRODUCT_ADAPTIVE_DNB, PAIR_DNBNAV, "equalized_radiance", dependencies=(PRODUCT_DNB, PRODUCT_DNB_SZA, PRODUCT_DNB_LZA))
PRODUCTS.add_product(PRODUCT_DYNAMIC_DNB, PAIR_DNBNAV, "equalized_radiance", dependencies=(PRODUCT_DNB, PRODUCT_DNB_SZA, PRODUCT_DNB_LZA))
PRODUCTS.add_product(PRODUCT_ADAPTIVE_I04, PAIR_INAV, "equalized_brightness_temperature", dependencies=(PRODUCT_I04,))
PRODUCTS.add_product(PRODUCT_ADAPTIVE_I05, PAIR_INAV, "equalized_brightness_temperature", dependencies=(PRODUCT_I05,))
PRODUCTS.add_product(PRODUCT_ADAPTIVE_M12, PAIR_MNAV, "equalized_brightness_temperature", dependencies=(PRODUCT_M12,))
PRODUCTS.add_product(PRODUCT_ADAPTIVE_M13, PAIR_MNAV, "equalized_brightness_temperature", dependencies=(PRODUCT_M13,))
PRODUCTS.add_product(PRODUCT_ADAPTIVE_M14, PAIR_MNAV, "equalized_brightness_temperature", dependencies=(PRODUCT_M14,))
PRODUCTS.add_product(PRODUCT_ADAPTIVE_M15, PAIR_MNAV, "equalized_brightness_temperature", dependencies=(PRODUCT_M15,))
PRODUCTS.add_product(PRODUCT_ADAPTIVE_M16, PAIR_MNAV, "equalized_brightness_temperature", dependencies=(PRODUCT_M16,))


class Frontend(roles.FrontendRole):
    FILE_EXTENSIONS = [".h5"]
    DEFAULT_FILE_READER = VIIRSSDRMultiReader
    PRODUCTS = PRODUCTS
    GEO_PAIRS = GEO_PAIRS

    def __init__(self, use_terrain_corrected=True, day_fraction=0.10, night_fraction=0.10, sza_threshold=100,
                 dnb_saturation_correction=False, **kwargs):
        """Initialize the frontend.

        For each search path, check if it exists and that it is
        a directory. If it is not a valid search path it will be removed
        and a warning will be raised.

        The order of the search paths does not matter. Any duplicate
        directories in the search path will be removed. This frontend
        does *not* recursively search directories.

        :param search_paths: A list of paths to search for usable files
        :param use_terrain_corrected: Look for terrain-corrected files instead of non-TC files (default True)
        """
        self.use_terrain_corrected = use_terrain_corrected
        LOG.debug("Day fraction set to %f", day_fraction)
        self.day_fraction = day_fraction
        LOG.debug("Night fraction set to %f", night_fraction)
        self.night_fraction = night_fraction
        LOG.debug("SZA threshold set to %f", sza_threshold)
        self.sza_threshold = sza_threshold
        self.dnb_saturation_correction = dnb_saturation_correction
        super(Frontend, self).__init__(**kwargs)

        # Load and sort all files
        self._load_files(self.find_files_with_extensions())

        # Functions to create additional products
        self.secondary_product_functions = {
            PRODUCT_HISTOGRAM_DNB: self.create_histogram_dnb,
            PRODUCT_ADAPTIVE_DNB: self.create_adaptive_dnb,
            PRODUCT_IFOG: self.create_ifog,
            PRODUCT_ADAPTIVE_I04: self.create_adaptive_btemp,
            PRODUCT_ADAPTIVE_I05: self.create_adaptive_btemp,
            PRODUCT_ADAPTIVE_M12: self.create_adaptive_btemp,
            PRODUCT_ADAPTIVE_M13: self.create_adaptive_btemp,
            PRODUCT_ADAPTIVE_M14: self.create_adaptive_btemp,
            PRODUCT_ADAPTIVE_M15: self.create_adaptive_btemp,
            PRODUCT_ADAPTIVE_M16: self.create_adaptive_btemp,
            PRODUCT_DYNAMIC_DNB: self.create_dynamic_dnb,
        }
        for p, p_def in self.PRODUCTS.items():
            if p_def.data_kind == "reflectance" and p_def.dependencies:
                self.secondary_product_functions[p] = self.day_check_reflectance




    def _load_files(self, file_paths):
        """Sort files by 'file type' and create objects to help load the data later.

        This method should not be called by the user.
        """
        self.file_readers = {}
        for file_type, file_type_info in guidebook.FILE_TYPES.items():
            cls = file_type_info.get("file_type_class", self.DEFAULT_FILE_READER)
            self.file_readers[file_type] = cls(file_type_info)
        # Don't modify the passed list (we use in place operations)
        file_paths_left = []
        for fp in file_paths:
            h = HDF5Reader(fp)
            for data_path, file_type in guidebook.DATA_PATHS.items():
                if data_path in h:
                    self.file_readers[file_type].add_file(h)
                    break
            else:
                file_paths_left.append(fp)


        # Log what files we were given that we didn't understand
        for fp in file_paths_left:
            LOG.debug("Unrecognized file: %s", fp)

        # Get rid of the readers we aren't using
        for file_type, file_reader in self.file_readers.items():
            if not len(file_reader):
                del self.file_readers[file_type]
            else:
                self.file_readers[file_type].finalize_files()

        if not self.file_readers:
            LOG.error("No useable files loaded")
            raise ValueError("No useable files loaded")

        first_length = len(self.file_readers[self.file_readers.keys()[0]])
        if not all(len(x) == first_length for x in self.file_readers.values()):
            LOG.error("Corrupt directory: Varying number of files for each type")
            ft_str = "\n\t".join("%s: %d" % (ft, len(fr)) for ft, fr in self.file_readers.items())
            LOG.debug("File types and number of files:\n\t%s", ft_str)
            raise RuntimeError("Corrupt directory: Varying number of files for each type")

    @property
    def begin_time(self):
        return self.file_readers[self.file_readers.keys()[0]].begin_time

    @property
    def end_time(self):
        return self.file_readers[self.file_readers.keys()[0]].end_time

    @property
    def available_product_names(self):
        raw_products = [p for p in self.PRODUCTS.all_raw_products if self.raw_product_available(p)]
        return sorted(self.PRODUCTS.get_product_dependents(raw_products))

    @property
    def all_product_names(self):
        return self.PRODUCTS.keys()

    @property
    def default_products(self):
        if os.getenv("P2G_VIIRS_DEFAULTS", None):
            return os.getenv("P2G_VIIRS_DEFAULTS").split(" ")

        defaults = [
            PRODUCT_I01, PRODUCT_I02, PRODUCT_I03, PRODUCT_I04, PRODUCT_I05,
            PRODUCT_M01,
            PRODUCT_M02,
            PRODUCT_M03,
            PRODUCT_M04,
            PRODUCT_M05,
            PRODUCT_M06,
            PRODUCT_M07,
            PRODUCT_M08,
            PRODUCT_M09,
            PRODUCT_M10,
            PRODUCT_M11,
            PRODUCT_M12,
            PRODUCT_M13,
            PRODUCT_M14,
            PRODUCT_M15,
            PRODUCT_M16,
            PRODUCT_IFOG,
            PRODUCT_HISTOGRAM_DNB,
            PRODUCT_ADAPTIVE_DNB,
            PRODUCT_DYNAMIC_DNB,
        ]
        return defaults

    def create_swath_definition(self, lon_product, lat_product):
        product_def = self.PRODUCTS[lon_product["product_name"]]
        index = 0 if self.use_terrain_corrected else 1
        file_type = product_def.get_file_type(index=index)
        lon_file_reader = self.file_readers[file_type]
        product_def = self.PRODUCTS[lat_product["product_name"]]
        file_type = product_def.get_file_type(index=index)
        lat_file_reader = self.file_readers[file_type]

        # sanity check
        for k in ["data_type", "swath_rows", "swath_columns", "rows_per_scan", "fill_value"]:
            if lon_product[k] != lat_product[k]:
                if k == "fill_value" and numpy.isnan(lon_product[k]) and numpy.isnan(lat_product[k]):
                    # NaN special case: NaNs can't be compared normally
                    continue
                LOG.error("Longitude and latitude products do not have equal attributes: %s", k)
                raise RuntimeError("Longitude and latitude products do not have equal attributes: %s" % (k,))

        swath_name = self.GEO_PAIRS[product_def.geo_pair_name].name
        swath_definition = containers.SwathDefinition(
            swath_name=swath_name, longitude=lon_product["swath_data"], latitude=lat_product["swath_data"],
            data_type=lon_product["data_type"], swath_rows=lon_product["swath_rows"],
            swath_columns=lon_product["swath_columns"], rows_per_scan=lon_product["rows_per_scan"],
            source_filenames=sorted(set(lon_file_reader.filepaths + lat_file_reader.filepaths)),
            # nadir_resolution=lon_file_reader.nadir_resolution, limb_resolution=lat_file_reader.limb_resolution,
            fill_value=lon_product["fill_value"],
        )
        file_key = product_def.get_file_key(index=index)
        swath_definition["orbit_rows"] = lon_file_reader.get_orbit_rows(file_key)

        # Tell the lat and lon products not to delete the data arrays, the swath definition will handle that
        lon_product.set_persist()
        lat_product.set_persist()

        # mmmmm, almost circular
        lon_product["swath_definition"] = swath_definition
        lat_product["swath_definition"] = swath_definition

        return swath_definition

    def create_raw_swath_object(self, product_name, swath_definition):
        product_def = self.PRODUCTS[product_name]
        index = 0 if self.use_terrain_corrected else 1
        file_type = product_def.get_file_type(index=index)
        file_key = product_def.get_file_key(index=index)
        if file_type not in self.file_readers:
            LOG.error("Could not create product '%s' because some data files are missing" % (product_name,))
            raise RuntimeError("Could not create product '%s' because some data files are missing" % (product_name,))
        file_reader = self.file_readers[file_type]
        LOG.debug("Using file type '%s' and getting file key '%s' for product '%s'", file_type, file_key, product_name)

        LOG.debug("Writing product '%s' data to binary file", product_name)
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        try:
            # TODO: Do something with data type
            shape = file_reader.write_var_to_flat_binary(file_key, filename)
            rows_per_scan = self.GEO_PAIRS[product_def.geo_pair_name].rows_per_scan
        except StandardError:
            LOG.error("Could not extract data from file. Use '--no-tc' flag if terrain-corrected data is not available")
            LOG.debug("Extraction exception: ", exc_info=True)
            raise

        one_swath = containers.SwathProduct(
            product_name=product_name, description=product_def.description, units=product_def.units,
            satellite=file_reader.satellite, instrument=file_reader.instrument,
            begin_time=file_reader.begin_time, end_time=file_reader.end_time,
            swath_definition=swath_definition, fill_value=numpy.nan,
            swath_rows=shape[0], swath_columns=shape[1], data_type=numpy.float32, swath_data=filename,
            source_filenames=file_reader.filepaths, data_kind=product_def.data_kind, rows_per_scan=rows_per_scan
        )
        file_key = product_def.get_file_key(index=index)
        one_swath["orbit_rows"] = file_reader.get_orbit_rows(file_key)
        return one_swath

    def create_secondary_swath_object(self, product_name, swath_definition, filename, data_type, products_created):
        product_def = self.PRODUCTS[product_name]
        dep_objects = [products_created[dep_name] for dep_name in product_def.dependencies]
        filepaths = sorted(set([filepath for swath in dep_objects for filepath in swath["source_filenames"]]))

        s = dep_objects[0]
        one_swath = containers.SwathProduct(
            product_name=product_name, description=product_def.description, units=product_def.units,
            satellite=s["satellite"], instrument=s["instrument"],
            begin_time=s["begin_time"], end_time=s["end_time"],
            swath_definition=swath_definition, fill_value=numpy.nan,
            swath_rows=s["swath_rows"], swath_columns=s["swath_columns"], data_type=data_type, swath_data=filename,
            source_filenames=filepaths, data_kind=product_def.data_kind, rows_per_scan=s["rows_per_scan"]
        )
        one_swath["orbit_rows"] = s["orbit_rows"]
        return one_swath

    def raw_product_available(self, product_name):
        """Is it possible to load the provided product with the files provided to the `Frontend`.

        :returns: True if product can be loaded, False otherwise (including if product is not a raw product)
        """
        product_def = self.PRODUCTS[product_name]
        if product_def.is_raw:
            # First element is terrain corrected, second element is non-TC
            file_type = product_def.get_file_type(index=0 if self.use_terrain_corrected else 1)
            return file_type in self.file_readers
        return False

    def create_scene(self, products=None, **kwargs):
        LOG.debug("Loading scene data...")
        # If the user didn't provide the products they want, figure out which ones we can create
        if products is None:
            LOG.debug("No products specified to frontend, will try to load logical defaults products")
            products = self.default_products

        # Do we actually have all of the files needed to create the requested products?
        products = self.loadable_products(products)

        # Needs to be ordered (least-depended product -> most-depended product)
        products_needed = self.PRODUCTS.dependency_ordered_products(products)
        geo_pairs_needed = self.PRODUCTS.geo_pairs_for_products(products_needed)
        # both lists below include raw products that need extra processing/masking
        raw_products_needed = (p for p in products_needed if self.PRODUCTS.is_raw(p, geo_is_raw=False))
        secondary_products_needed = [p for p in products_needed if self.PRODUCTS.needs_processing(p)]
        for p in secondary_products_needed:
            if p not in self.secondary_product_functions:
                LOG.error("Product (secondary or extra processing) required, but not sure how to make it: '%s'", p)
                raise ValueError("Product (secondary or extra processing) required, but not sure how to make it: '%s'" % (p,))

        # final scene object we'll be providing to the caller
        scene = containers.SwathScene()
        # Dictionary of all products created so far (local variable so we don't hold on to any product objects)
        products_created = {}
        swath_definitions = {}

        # Load geolocation files
        for geo_pair_name in geo_pairs_needed:
            ### Lon Product ###
            lon_product_name = self.GEO_PAIRS[geo_pair_name].lon_product
            LOG.info("Creating navigation product '%s'", lon_product_name)
            lon_swath = products_created[lon_product_name] = self.create_raw_swath_object(lon_product_name, None)
            if lon_product_name in products:
                scene[lon_product_name] = lon_swath

            ### Lat Product ###
            lat_product_name = self.GEO_PAIRS[geo_pair_name].lat_product
            LOG.info("Creating navigation product '%s'", lat_product_name)
            lat_swath = products_created[lat_product_name] = self.create_raw_swath_object(lat_product_name, None)
            if lat_product_name in products:
                scene[lat_product_name] = lat_swath

            # Create the SwathDefinition
            swath_def = self.create_swath_definition(lon_swath, lat_swath)
            swath_definitions[swath_def["swath_name"]] = swath_def

        # Create each raw products (products that are loaded directly from the file)
        for product_name in raw_products_needed:
            if product_name in products_created:
                # already created
                continue

            try:
                LOG.info("Creating data product '%s'", product_name)
                swath_def = swath_definitions[self.PRODUCTS[product_name].geo_pair_name]
                one_swath = products_created[product_name] = self.create_raw_swath_object(product_name, swath_def)
            except StandardError:
                LOG.error("Could not create raw product '%s'", product_name)
                if self.exit_on_error:
                    raise
                continue

            if product_name in products:
                # the user wants this product
                scene[product_name] = one_swath

        # Dependent products and Special cases (i.e. non-raw products that need further processing)
        for product_name in reversed(secondary_products_needed):
            product_func = self.secondary_product_functions[product_name]
            swath_def = swath_definitions[self.PRODUCTS[product_name].geo_pair_name]

            try:
                LOG.info("Creating secondary product '%s'", product_name)
                one_swath = product_func(product_name, swath_def, products_created)
            except StandardError:
                LOG.error("Could not create product (unexpected error): '%s'", product_name)
                LOG.debug("Could not create product (unexpected error): '%s'", product_name, exc_info=True)
                if self.exit_on_error:
                    raise
                continue

            if one_swath is None:
                LOG.debug("Secondary product function did not produce a swath product")
                if product_name in scene:
                    LOG.debug("Removing original swath that was created before")
                    del scene[product_name]
                continue
            products_created[product_name] = one_swath
            if product_name in products:
                # the user wants this product
                scene[product_name] = one_swath

        return scene

    ### Secondary Product Functions
    def create_histogram_dnb(self, product_name, swath_definition, products_created, fill=numpy.nan):
        product_def = self.PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) != 2:
            LOG.error("Expected 2 dependencies to create adaptive DNB product, got %d" % (len(deps),))
            raise ValueError("Expected 2 dependencies to create adaptive DNB product, got %d" % (len(deps),))

        dnb_product_name = deps[0]
        sza_product_name = deps[1]
        dnb_product = products_created[dnb_product_name]
        dnb_data = dnb_product.get_data_array("swath_data")
        sza_data = products_created[sza_product_name].get_data_array()
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        try:
            output_data = dnb_product.copy_array(filename=filename, read_only=False)
            dnb_scale(dnb_data, solarZenithAngle=sza_data, fillValue=fill, out=output_data)

            one_swath = self.create_secondary_swath_object(product_name, swath_definition, filename,
                                                           dnb_product["data_type"], products_created)
        except StandardError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        return one_swath

    def create_adaptive_dnb(self, product_name, swath_definition, products_created, fill=numpy.nan):
        product_def = self.PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) != 3:
            LOG.error("Expected 3 dependencies to create adaptive DNB product, got %d" % (len(deps),))
            raise RuntimeError("Expected 3 dependencies to create adaptive DNB product, got %d" % (len(deps),))

        dnb_product_name = deps[0]
        sza_product_name = deps[1]
        lza_product_name = deps[2]
        lon_product_name = self.GEO_PAIRS[product_def.geo_pair_name].lon_product
        index = 0 if self.use_terrain_corrected else 1
        file_type = self.PRODUCTS[lon_product_name].get_file_type(index=index)
        geo_file_reader = self.file_readers[file_type]
        moon_illum_fraction = sum(geo_file_reader[guidebook.K_MOONILLUM]) / (100.0 * len(geo_file_reader))
        dnb_product = products_created[dnb_product_name]
        dnb_data = dnb_product.get_data_array()
        sza_data = products_created[sza_product_name].get_data_array()
        lza_data = products_created[lza_product_name].get_data_array()
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        try:
            output_data = dnb_product.copy_array(filename=filename, read_only=False)
            adaptive_dnb_scale(dnb_data, solarZenithAngle=sza_data, lunarZenithAngle=lza_data,
                               moonIllumFraction=moon_illum_fraction, fillValue=fill, out=output_data)

            one_swath = self.create_secondary_swath_object(product_name, swath_definition, filename,
                                                           dnb_product["data_type"], products_created)
        except StandardError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        return one_swath

    def create_adaptive_btemp(self, product_name, swath_definition, products_created, fill=numpy.nan):
        product_def = self.PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) != 1:
            LOG.error("Expected 1 dependencies to create adaptive BT product, got %d" % (len(deps),))
            raise RuntimeError("Expected 1 dependencies to create adaptive BT product, got %d" % (len(deps),))

        bt_product_name = deps[0]
        bt_product = products_created[bt_product_name]
        bt_data = bt_product.get_data_array()
        bt_mask = bt_product.get_data_mask()
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        try:
            output_data = bt_product.copy_array(filename=filename, read_only=False)
            histogram.local_histogram_equalization(bt_data, ~bt_mask, do_log_scale=False, out=output_data)

            one_swath = self.create_secondary_swath_object(product_name, swath_definition, filename,
                                                           bt_product["data_type"], products_created)
        except StandardError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        return one_swath

    def create_ifog(self, product_name, swath_definition, products_created, fill=numpy.nan):
        product_def = self.PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) != 3:
            LOG.error("Expected 3 dependencies to create FOG/temperature difference product, got %d" % (len(deps),))
            raise RuntimeError("Expected 3 dependencies to create FOG/temperature difference product, got %d" % (len(deps),))

        left_term_name = deps[0]
        right_term_name = deps[1]
        sza_product_name = deps[2]
        left_data = products_created[left_term_name].get_data_array()
        left_mask = products_created[left_term_name].get_data_mask()
        right_data = products_created[right_term_name].get_data_array()
        right_mask = products_created[right_term_name].get_data_mask()
        sza_data = products_created[sza_product_name].get_data_array()
        sza_mask = products_created[sza_product_name].get_data_mask()
        night_mask = sza_data >= self.sza_threshold

        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        try:
            invalid_mask = left_mask | right_mask | sza_mask
            valid_night_mask = night_mask & ~invalid_mask
            # get the fraction of the data that is valid night data from all valid data
            fraction_night = numpy.count_nonzero(valid_night_mask) / (sza_data.size - numpy.count_nonzero(invalid_mask))
            if fraction_night < self.night_fraction:
                LOG.info("Less than 10%% of the data is at night, will not create '%s' product", product_name)
                return None

            fog_data = numpy.memmap(filename, dtype=left_data.dtype, mode="w+", shape=left_data.shape)
            numpy.subtract(left_data, right_data, fog_data)
            fog_data[~valid_night_mask] = fill

            one_swath = self.create_secondary_swath_object(product_name, swath_definition, filename,
                                                           products_created[left_term_name]["data_type"], products_created)
        except StandardError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        return one_swath

    def create_dynamic_dnb(self, product_name, swath_definition, products_created, fill=numpy.nan):
        product_def = self.PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) != 3:
            LOG.error("Expected 3 dependencies to create dynamic DNB product, got %d" % (len(deps),))
            raise RuntimeError("Expected 3 dependencies to create dynamic DNB product, got %d" % (len(deps),))

        dnb_product_name = deps[0]
        sza_product_name = deps[1]
        lza_product_name = deps[2]
        lon_product_name = self.GEO_PAIRS[product_def.geo_pair_name].lon_product
        index = 0 if self.use_terrain_corrected else 1
        file_type = self.PRODUCTS[lon_product_name].get_file_type(index=index)
        geo_file_reader = self.file_readers[file_type]
        # convert to decimal instead of %
        moon_illum_fraction = numpy.mean(geo_file_reader[guidebook.K_MOONILLUM]) * 0.01
        dnb_product = products_created[dnb_product_name]
        dnb_data = dnb_product.get_data_array()
        sza_data = products_created[sza_product_name].get_data_array()
        lza_data = products_created[lza_product_name].get_data_array()
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        try:
            output_data = dnb_product.copy_array(filename=filename, read_only=False)

            ### From Steve Miller and Curtis Seaman
            # maxval = 10.^(-1.7 - (((2.65+moon_factor1+moon_factor2))*(1+erf((solar_zenith-95.)/(5.*sqrt(2.0))))))
            # minval = 10.^(-4. - ((2.95+moon_factor2)*(1+erf((solar_zenith-95.)/(5.*sqrt(2.0))))))
            # scaled_radiance = (radiance - minval) / (maxval - minval)
            # radiance = sqrt(scaled_radiance)

            ### Update to method from Curtis Seaman
            # maxval = 10.^(-1.7 - (((2.65+moon_factor1+moon_factor2))*(1+erf((solar_zenith-95.)/(5.*sqrt(2.0))))))
            # minval = 10.^(-4. - ((2.95+moon_factor2)*(1+erf((solar_zenith-95.)/(5.*sqrt(2.0))))))
            # saturated_pixels = where(radiance gt maxval, nsatpx)
            # saturation_pct = float(nsatpx)/float(n_elements(radiance))
            # print, 'Saturation (%) = ', saturation_pct
            #
            # while saturation_pct gt 0.005 do begin
            #   maxval = maxval*1.1
            #   saturated_pixels = where(radiance gt maxval, nsatpx)
            #   saturation_pct = float(nsatpx)/float(n_elements(radiance))
            #   print, saturation_pct
            # endwhile
            #
            # scaled_radiance = (radiance - minval) / (maxval - minval)
            # radiance = sqrt(scaled_radiance)

            moon_factor1 = 0.7 * (1.0 - moon_illum_fraction)
            moon_factor2 = 0.0022 * lza_data
            erf_portion = 1 + erf((sza_data - 95.0) / (5.0 * numpy.sqrt(2.0)))
            max_val = numpy.power(10, -1.7 - (2.65 + moon_factor1 + moon_factor2) * erf_portion)
            min_val = numpy.power(10, -4.0 - (2.95 + moon_factor2) * erf_portion)

            # Update from Curtis Seaman, increase max radiance curve until less than 0.5% is saturated
            if self.dnb_saturation_correction:
                saturation_pct = float(numpy.count_nonzero(dnb_data > max_val)) / dnb_data.size
                LOG.debug("Dynamic DNB saturation percentage: %f", saturation_pct)
                while saturation_pct > 0.005:
                    max_val *= 1.1
                    saturation_pct = float(numpy.count_nonzero(dnb_data > max_val)) / dnb_data.size
                    LOG.debug("Dynamic DNB saturation percentage: %f", saturation_pct)

            inner_sqrt = (dnb_data - min_val) / (max_val - min_val)
            # clip negative values to 0 before the sqrt
            inner_sqrt[inner_sqrt < 0] = 0
            numpy.sqrt(inner_sqrt, out=output_data)

            one_swath = self.create_secondary_swath_object(product_name, swath_definition, filename,
                                                           dnb_product["data_type"], products_created)
        except StandardError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        return one_swath

    def _get_day_percentage(self, sza_swath):
        if "day_percentage" not in sza_swath:
            sza_data = sza_swath.get_data_array()
            invalid_mask = sza_swath.get_data_mask()
            valid_day_mask = (sza_data < self.sza_threshold) & ~invalid_mask
            fraction_day = numpy.count_nonzero(valid_day_mask) / (float(sza_data.size) - numpy.count_nonzero(invalid_mask))
            sza_swath["day_percentage"] = fraction_day * 100.0
        else:
            LOG.debug("Day percentage found in SZA swath already")
        return sza_swath["day_percentage"]

    def day_check_reflectance(self, product_name, swath_definition, products_created, fill=numpy.nan):
        product_def = self.PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) != 1:
            LOG.error("Expected 1 dependencies to check night mask, got %d" % (len(deps),))
            raise RuntimeError("Expected 1 dependencies to check night mask, got %d" % (len(deps),))

        sza_swath = products_created[deps[0]]
        day_percentage = self._get_day_percentage(sza_swath)
        LOG.debug("Reflectance product's scene has %f%% day data", day_percentage)
        if day_percentage < (self.day_fraction * 100):
            LOG.info("Will not create product '%s' because there is less than 10%% of day data", product_name)
            return None
        return products_created[product_name]


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    from polar2grid.core.script_utils import ExtendAction, ExtendConstAction
    # Set defaults for other components that may be used in polar2grid processing
    parser.set_defaults(fornav_D=40, fornav_d=2)

    # Use the append_const action to handle adding products to the list
    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                       help="List available frontend products and exit")
    group.add_argument("--no-tc", dest="use_terrain_corrected", action="store_false",
                       help="Don't use terrain-corrected navigation")
    group.add_argument("--day-fraction", dest="day_fraction", type=float, default=float(os.environ.get("P2G_DAY_FRACTION", 0.10)),
                       help="Fraction of day required to produce reflectance products (default 0.10)")
    group.add_argument("--night-fraction", dest="night_fraction", type=float, default=float(os.environ.get("P2G_NIGHT_FRACTION", 0.10)),
                       help="Fraction of night required to product products like fog (default 0.10)")
    group.add_argument("--sza-threshold", dest="sza_threshold", type=float, default=float(os.environ.get("P2G_SZA_THRESHOLD", 100)),
                       help="Angle threshold of solar zenith angle used when deciding day or night (default 100)")
    group.add_argument("--dnb-saturation-correction", action="store_true",
                       help="Enable dynamic DNB saturation correction (normally used for aurora scenes)")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    # FIXME: Probably need some proper defaults
    group.add_argument("-p", "--products", dest="products", nargs="+", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    # group.add_argument('--no-pseudo', dest='create_pseudo', default=True, action='store_false',
    #                     help="Don't create pseudo bands")
    # group.add_argument('--adaptive-dnb', dest='products', action="append_const", const=PRODUCT_ADAPTIVE_DNB,
    #                    help="Create DNB output that is pre-scaled using adaptive tile sizes if provided DNB data; " +
    #                         "the normal single-region pre-scaled version of DNB will also be created if you specify this argument")
    group.add_argument('--adaptive-bt', dest='products', action=ExtendConstAction, const=ADAPTIVE_BT_PRODUCTS,
                       help="Create adaptively scaled brightness temperature bands")
    # group.add_argument('--include-dnb', dest='products', action="append_const", const=PRODUCT_DNB,
    #                    help="Add unscaled DNB product to list of products")
    group.add_argument('--i-bands', dest='products', action=ExtendConstAction, const=I_PRODUCTS,
                       help="Add all I-band raw products to list of products")
    group.add_argument('--m-bands', dest='products', action=ExtendConstAction, const=M_PRODUCTS,
                       help="Add all M-band raw products to list of products")
    group.add_argument('--dnb-angle-products', dest='products', action=ExtendConstAction, const=DNB_ANGLE_PRODUCTS,
                       help="Add DNB-band geolocation 'angle' products to list of products")
    group.add_argument('--i-angle-products', dest='products', action=ExtendConstAction, const=I_ANGLE_PRODUCTS,
                       help="Add I-band geolocation 'angle' products to list of products")
    group.add_argument('--m-angle-products', dest='products', action=ExtendConstAction, const=M_ANGLE_PRODUCTS,
                       help="Add M-band geolocation 'angle' products to list of products")
    group.add_argument('--m-rad-products', dest='products', action=ExtendConstAction, const=M_RAD_PRODUCTS,
                       help="Add M-band geolocation radiance products to list of products")
    group.add_argument('--i-rad-products', dest='products', action=ExtendConstAction, const=I_RAD_PRODUCTS,
                       help="Add I-band geolocation radiance products to list of products")
    return ["Frontend Initialization", "Frontend Swath Extraction"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    parser = create_basic_parser(description="Extract VIIRS swath data into binary files")
    subgroup_titles = add_frontend_argument_groups(parser)
    parser.add_argument('-f', dest='data_files', nargs="+", default=[],
                        help="List of data files or directories to extract data from")
    parser.add_argument('-o', dest="output_filename", default=None,
                        help="Output filename for JSON scene (default is to stdout)")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(subgroup_titles=subgroup_titles, global_keywords=global_keywords)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)
    LOG.debug("Starting script with arguments: %s", " ".join(sys.argv))

    list_products = args.subgroup_args["Frontend Initialization"].pop("list_products")
    f = Frontend(search_paths=args.data_files, **args.subgroup_args["Frontend Initialization"])

    if list_products:
        print("\n".join(f.available_product_names))
        return 0

    if args.output_filename and os.path.isfile(args.output_filename):
        LOG.error("JSON file '%s' already exists, will not overwrite." % (args.output_filename,))
        raise RuntimeError("JSON file '%s' already exists, will not overwrite." % (args.output_filename,))

    scene = f.create_scene(**args.subgroup_args["Frontend Swath Extraction"])
    json_str = scene.dumps(persist=True)
    if args.output_filename:
        with open(args.output_filename, 'w') as output_file:
            output_file.write(json_str)
    else:
        print(json_str)
    return 0

if __name__ == '__main__':
    sys.exit(main())
