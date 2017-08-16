#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2012-2015 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    December 2014
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""The MODIS Reader operates on HDF4 Level 1B files from the Moderate Resolution
Imaging Spectroradiometer (MODIS) instruments on the Aqua and Terra
satellites. The reader is designed to work with files created by the IMAPP
direct broadcast processing system (file naming conventions such as 
a1.17006.1855.1000m.hdf), but can support other types of L1B files, including 
the NASA archived files (file naming conventions such as 
MOD021KM.A2017004.1732.005.2017023210017.hdf).  The
reader can be specified to the ``polar2grid.sh`` script by using the reader name ``modis``.

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--fornav-D`` parameter is set to 10 and the
``--fornav-d`` parameter is set to 1. 

It provides the following products:

    +--------------------+--------------------------------------------+
    | Product Name       | Description                                |
    +====================+============================================+
    | vis01              | Visible 1 Band                             |
    +--------------------+--------------------------------------------+
    | vis02              | Visible 2 Band                             |
    +--------------------+--------------------------------------------+
    | vis03              | Visible 3 Band                             |
    +--------------------+--------------------------------------------+
    | vis04              | Visible 4 Band                             |
    +--------------------+--------------------------------------------+
    | vis05              | Visible 5 Band                             |
    +--------------------+--------------------------------------------+
    | vis06              | Visible 6 Band                             |
    +--------------------+--------------------------------------------+
    | vis07              | Visible 7 Band                             |
    +--------------------+--------------------------------------------+
    | vis26              | Visible 26 Band                            |
    +--------------------+--------------------------------------------+
    | bt20               | Brightness Temperature Band 20             |
    +--------------------+--------------------------------------------+
    | bt21               | Brightness Temperature Band 21             |
    +--------------------+--------------------------------------------+
    | bt22               | Brightness Temperature Band 22             |
    +--------------------+--------------------------------------------+
    | bt23               | Brightness Temperature Band 23             |
    +--------------------+--------------------------------------------+
    | bt24               | Brightness Temperature Band 24             |
    +--------------------+--------------------------------------------+
    | bt25               | Brightness Temperature Band 25             |
    +--------------------+--------------------------------------------+
    | bt27               | Brightness Temperature Band 27             |
    +--------------------+--------------------------------------------+
    | bt28               | Brightness Temperature Band 28             |
    +--------------------+--------------------------------------------+
    | bt29               | Brightness Temperature Band 29             |
    +--------------------+--------------------------------------------+
    | bt30               | Brightness Temperature Band 30             |
    +--------------------+--------------------------------------------+
    | bt31               | Brightness Temperature Band 31             |
    +--------------------+--------------------------------------------+
    | bt32               | Brightness Temperature Band 32             |
    +--------------------+--------------------------------------------+
    | bt33               | Brightness Temperature Band 33             |
    +--------------------+--------------------------------------------+
    | bt34               | Brightness Temperature Band 34             |
    +--------------------+--------------------------------------------+
    | bt35               | Brightness Temperature Band 35             |
    +--------------------+--------------------------------------------+
    | bt36               | Brightness Temperature Band 36             |
    +--------------------+--------------------------------------------+
    | ir20               | Radiance Band 20                           |
    +--------------------+--------------------------------------------+
    | ir21               | Radiance Band 21                           |
    +--------------------+--------------------------------------------+
    | ir22               | Radiance Band 22                           |
    +--------------------+--------------------------------------------+
    | ir23               | Radiance Band 23                           |
    +--------------------+--------------------------------------------+
    | ir24               | Radiance Band 24                           |
    +--------------------+--------------------------------------------+
    | ir25               | Radiance Band 25                           |
    +--------------------+--------------------------------------------+
    | ir27               | Radiance Band 27                           |
    +--------------------+--------------------------------------------+
    | ir28               | Radiance Band 28                           |
    +--------------------+--------------------------------------------+
    | ir29               | Radiance Band 29                           |
    +--------------------+--------------------------------------------+
    | ir30               | Radiance Band 30                           |
    +--------------------+--------------------------------------------+
    | ir31               | Radiance Band 31                           |
    +--------------------+--------------------------------------------+
    | ir32               | Radiance Band 32                           |
    +--------------------+--------------------------------------------+
    | ir33               | Radiance Band 33                           |
    +--------------------+--------------------------------------------+
    | ir34               | Radiance Band 34                           |
    +--------------------+--------------------------------------------+
    | ir35               | Radiance Band 35                           |
    +--------------------+--------------------------------------------+
    | ir36               | Radiance Band 36                           |
    +--------------------+--------------------------------------------+
    | cloud_mask         | Cloud Mask                                 |
    +--------------------+--------------------------------------------+
    | land_sea_mask      | Land Sea Mask                              |
    +--------------------+--------------------------------------------+
    | snow_ice_mask      | Snow Ice Mask                              |
    +--------------------+--------------------------------------------+
    | sst                | Sea Surface Temperature                    |
    +--------------------+--------------------------------------------+
    | lst                | Land Surface Temperature                   |
    +--------------------+--------------------------------------------+
    | slst               | Summer Land Surface Temperature            |
    +--------------------+--------------------------------------------+
    | ndvi               | Normalized Difference Vegetation Index     |
    +--------------------+--------------------------------------------+
    | ist                | Ice Surface Temperature                    |
    +--------------------+--------------------------------------------+
    | inversion_strength | Inversion Strength                         |
    +--------------------+--------------------------------------------+
    | inversion_depth    | Inversion Depth                            |
    +--------------------+--------------------------------------------+
    | ice_concentration  | Ice Concentration                          |
    +--------------------+--------------------------------------------+
    | ctt                | Cloud Top Temperature                      |
    +--------------------+--------------------------------------------+
    | tpw                | Total Precipitable Water                   |
    +--------------------+--------------------------------------------+
    | fog                | Temperature Difference between BT31        |
    |                    | and BT20                                   |
    +--------------------+--------------------------------------------+

For reflectance/visible products a check is done to make sure that at least
10% of the swath is day time. Data is considered day time where solar zenith
angle is less than 90 degrees.

"""
__docformat__ = "restructuredtext en"

import sys

import logging
import numpy
import os
import shutil

from polar2grid.core import roles, histogram, containers
from polar2grid.core.frontend_utils import ProductDict, GeoPairDict
from polar2grid.modis import modis_guidebook as guidebook
from polar2grid.modis.bt import bright_shift

LOG = logging.getLogger(__name__)

PRODUCTS = ProductDict()
GEO_PAIRS = GeoPairDict()

### PRODUCT KEYS ###
# PRODUCT_VIS01_1000m = "visible_01_1000m"  # if someone wants to have both the 250m and the 1000m version
PRODUCT_VIS01 = "vis01"
PRODUCT_VIS02 = "vis02"
PRODUCT_VIS03 = "vis03"
PRODUCT_VIS04 = "vis04"
PRODUCT_VIS05 = "vis05"
PRODUCT_VIS06 = "vis06"
PRODUCT_VIS07 = "vis07"
PRODUCT_VIS26 = "vis26"

# need to be converted to BTs:
PRODUCT_IR20 = "ir20"
PRODUCT_IR21 = "ir21"
PRODUCT_IR22 = "ir22"
PRODUCT_IR23 = "ir23"
PRODUCT_IR24 = "ir24"
PRODUCT_IR25 = "ir25"
PRODUCT_IR27 = "ir27"
PRODUCT_IR28 = "ir28"
PRODUCT_IR29 = "ir29"
PRODUCT_IR30 = "ir30"
PRODUCT_IR31 = "ir31"
PRODUCT_IR32 = "ir32"
PRODUCT_IR33 = "ir33"
PRODUCT_IR34 = "ir34"
PRODUCT_IR35 = "ir35"
PRODUCT_IR36 = "ir36"

PRODUCT_BT20 = "bt20"
PRODUCT_BT21 = "bt21"
PRODUCT_BT22 = "bt22"
PRODUCT_BT23 = "bt23"
PRODUCT_BT24 = "bt24"
PRODUCT_BT25 = "bt25"
PRODUCT_BT27 = "bt27"
PRODUCT_BT28 = "bt28"
PRODUCT_BT29 = "bt29"
PRODUCT_BT30 = "bt30"
PRODUCT_BT31 = "bt31"
PRODUCT_BT32 = "bt32"
PRODUCT_BT33 = "bt33"
PRODUCT_BT34 = "bt34"
PRODUCT_BT35 = "bt35"
PRODUCT_BT36 = "bt36"

PRODUCT_CMASK = "cloud_mask"
PRODUCT_LSMASK = "land_sea_mask"
PRODUCT_SIMASK = "snow_ice_mask"
PRODUCT_SZA = "solar_zenith_angle"
PRODUCT_SenZA = "satellite_zenith_angle"

# Need land mask clearing and cloud clearing
PRODUCT_SST = "sst_uncleared"
PRODUCT_LST = "lst_uncleared"
PRODUCT_SLST = "slst_uncleared"
PRODUCT_NDVI = "ndvi_uncleared"
PRODUCT_CLEAR_SST = "sst"
PRODUCT_CLEAR_LST = "lst"
PRODUCT_CLEAR_SLST = "slst"
PRODUCT_CLEAR_NDVI = "ndvi"

PRODUCT_IST = "ist"
PRODUCT_INV = "inversion_strength"
PRODUCT_IND = "inversion_depth"
PRODUCT_ICON = "ice_concentration"
PRODUCT_CTT = "ctt"
PRODUCT_TPW = "tpw"
# secondary products
PRODUCT_FOG = "fog"
# Adaptive BT Products
PRODUCT_ADAPTIVE_BT20 = "adaptive_bt20"
PRODUCT_ADAPTIVE_BT27 = "adaptive_bt27"
PRODUCT_ADAPTIVE_BT31 = "adaptive_bt31"
# Geolocation "Products"
PRODUCT_1000M_LAT = "latitude_1000m"
PRODUCT_1000M_LON = "longitude_1000m"
PRODUCT_500M_LAT = "latitude_500m"
PRODUCT_500M_LON = "longitude_500m"
PRODUCT_250M_LAT = "latitude_250m"
PRODUCT_250M_LON = "longitude_250m"
PRODUCT_MOD06_LAT = "latitude_mod06"
PRODUCT_MOD06_LON = "longitude_mod06"
PRODUCT_MOD07_LAT = "latitude_mod07"
PRODUCT_MOD07_LON = "longitude_mod07"
# we just use the geolocation in the geo file
# PRODUCT_MOD28_LAT = "latitude_mod28"
# PRODUCT_MOD28_LON = "longitude_mod28"
# PRODUCT_MOD35_LAT = "latitude_mod35"
# PRODUCT_MOD35_LON = "longitude_mod35"
# PRODUCT_MODLST_LAT = "latitude_modlst"
# PRODUCT_MODLST_LON = "longitude_modlst"
# PRODUCT_MASKBYTE_LAT = "latitude_mask_byte"
# PRODUCT_MASKBYTE_LON = "longitude_mask_byte"

ADAPTIVE_BT_PRODUCTS = [PRODUCT_ADAPTIVE_BT20, PRODUCT_ADAPTIVE_BT27, PRODUCT_ADAPTIVE_BT31]

PAIR_1000M = "1000m_nav"
PAIR_500M = "500m_nav"
PAIR_250M = "250m_nav"
PAIR_MOD06 = "mod06_nav"
PAIR_MOD07 = "mod07_nav"

GEO_PAIRS.add_pair(PAIR_1000M, PRODUCT_1000M_LON, PRODUCT_1000M_LAT, 10)
GEO_PAIRS.add_pair(PAIR_500M, PRODUCT_500M_LON, PRODUCT_500M_LAT, 20)
GEO_PAIRS.add_pair(PAIR_250M, PRODUCT_250M_LON, PRODUCT_250M_LAT, 40)
GEO_PAIRS.add_pair(PAIR_MOD06, PRODUCT_MOD06_LON, PRODUCT_MOD06_LAT, 2)
GEO_PAIRS.add_pair(PAIR_MOD07, PRODUCT_MOD07_LON, PRODUCT_MOD07_LAT, 2)

# TODO: Add description and units
PRODUCTS.add_product(PRODUCT_1000M_LON, PAIR_1000M, "longitude", guidebook.FT_GEO, guidebook.K_LONGITUDE)
PRODUCTS.add_product(PRODUCT_1000M_LAT, PAIR_1000M, "latitude", guidebook.FT_GEO, guidebook.K_LATITUDE)
# 500M interpolation is not implemented yet
PRODUCTS.add_product(PRODUCT_500M_LON, PAIR_500M, "longitude", guidebook.FT_GEO, guidebook.K_LONGITUDE_500)
PRODUCTS.add_product(PRODUCT_500M_LAT, PAIR_500M, "latitude", guidebook.FT_GEO, guidebook.K_LATITUDE_500)
PRODUCTS.add_product(PRODUCT_250M_LON, PAIR_250M, "longitude", guidebook.FT_GEO, guidebook.K_LONGITUDE_250)
PRODUCTS.add_product(PRODUCT_250M_LAT, PAIR_250M, "latitude", guidebook.FT_GEO, guidebook.K_LATITUDE_250)
PRODUCTS.add_product(PRODUCT_MOD06_LON, PAIR_MOD06, "longitude", guidebook.FT_MOD06CT, guidebook.K_LONGITUDE)
PRODUCTS.add_product(PRODUCT_MOD06_LAT, PAIR_MOD06, "latitude", guidebook.FT_MOD06CT, guidebook.K_LATITUDE)
PRODUCTS.add_product(PRODUCT_MOD07_LON, PAIR_MOD07, "longitude", guidebook.FT_MOD07, guidebook.K_LONGITUDE)
PRODUCTS.add_product(PRODUCT_MOD07_LAT, PAIR_MOD07, "latitude", guidebook.FT_MOD07, guidebook.K_LATITUDE)

PRODUCTS.add_product(PRODUCT_SZA, PAIR_1000M, "solar_zenith_angle", guidebook.FT_GEO, guidebook.K_SZA)
PRODUCTS.add_product(PRODUCT_SenZA, PAIR_1000M, "satellite_zenith_angle", guidebook.FT_GEO, guidebook.K_SenZA)
# if in the future someone needs both the 250M version and the 1000M version add uncomment this line
# PRODUCTS.add_product(PRODUCT_VIS01_1000M, PAIR_1000M, "reflectance", guidebook.FT_1000M, guidebook.K_VIS01)
PRODUCTS.add_product(PRODUCT_VIS01, (PAIR_250M, PAIR_500M, PAIR_1000M), "reflectance", (guidebook.FT_250M, guidebook.FT_500M, guidebook.FT_1000M), guidebook.K_VIS01, dependencies=(PRODUCT_SZA,))
PRODUCTS.add_product(PRODUCT_VIS02, (PAIR_250M, PAIR_500M, PAIR_1000M), "reflectance", (guidebook.FT_250M, guidebook.FT_500M, guidebook.FT_1000M), guidebook.K_VIS02, dependencies=(PRODUCT_SZA,))
PRODUCTS.add_product(PRODUCT_VIS03, (PAIR_500M, PAIR_1000M), "reflectance", (guidebook.FT_500M, guidebook.FT_1000M), guidebook.K_VIS03, dependencies=(PRODUCT_SZA,))
PRODUCTS.add_product(PRODUCT_VIS04, (PAIR_500M, PAIR_1000M), "reflectance", (guidebook.FT_500M, guidebook.FT_1000M), guidebook.K_VIS04, dependencies=(PRODUCT_SZA,))
PRODUCTS.add_product(PRODUCT_VIS05, (PAIR_500M, PAIR_1000M), "reflectance", (guidebook.FT_500M, guidebook.FT_1000M), guidebook.K_VIS05, dependencies=(PRODUCT_SZA,))
PRODUCTS.add_product(PRODUCT_VIS06, (PAIR_500M, PAIR_1000M), "reflectance", (guidebook.FT_500M, guidebook.FT_1000M), guidebook.K_VIS06, dependencies=(PRODUCT_SZA,))
PRODUCTS.add_product(PRODUCT_VIS07, (PAIR_500M, PAIR_1000M), "reflectance", (guidebook.FT_500M, guidebook.FT_1000M), guidebook.K_VIS07, dependencies=(PRODUCT_SZA,))
PRODUCTS.add_product(PRODUCT_VIS26, PAIR_1000M, "reflectance", guidebook.FT_1000M, guidebook.K_VIS26, dependencies=(PRODUCT_SZA,))
PRODUCTS.add_product(PRODUCT_IR20, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR20)
PRODUCTS.add_product(PRODUCT_IR21, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR21)
PRODUCTS.add_product(PRODUCT_IR22, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR22)
PRODUCTS.add_product(PRODUCT_IR23, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR23)
PRODUCTS.add_product(PRODUCT_IR24, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR24)
PRODUCTS.add_product(PRODUCT_IR25, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR25)
PRODUCTS.add_product(PRODUCT_IR27, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR27)
PRODUCTS.add_product(PRODUCT_IR28, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR28)
PRODUCTS.add_product(PRODUCT_IR29, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR29)
PRODUCTS.add_product(PRODUCT_IR30, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR30)
PRODUCTS.add_product(PRODUCT_IR31, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR31)
PRODUCTS.add_product(PRODUCT_IR32, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR32)
PRODUCTS.add_product(PRODUCT_IR33, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR33)
PRODUCTS.add_product(PRODUCT_IR34, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR34)
PRODUCTS.add_product(PRODUCT_IR35, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR35)
PRODUCTS.add_product(PRODUCT_IR36, PAIR_1000M, "radiance", guidebook.FT_1000M, guidebook.K_IR36)
PRODUCTS.add_product(PRODUCT_CMASK, PAIR_1000M, "category", (guidebook.FT_MASK_BYTE1, guidebook.FT_MOD35), guidebook.K_CMASK)
PRODUCTS.add_product(PRODUCT_LSMASK, PAIR_1000M, "category", guidebook.FT_MASK_BYTE1, guidebook.K_LSMASK)
PRODUCTS.add_product(PRODUCT_SIMASK, PAIR_1000M, "category", guidebook.FT_MASK_BYTE1, guidebook.K_SIMASK)
PRODUCTS.add_product(PRODUCT_SST, PAIR_1000M, "sea_surface_temperature", guidebook.FT_MOD28, guidebook.K_SST, units='K')
PRODUCTS.add_product(PRODUCT_LST, PAIR_1000M, "land_surface_temperature", guidebook.FT_MODLST, guidebook.K_LST, units='K')
PRODUCTS.add_product(PRODUCT_NDVI, PAIR_1000M, "ndvi", guidebook.FT_NDVI_1000M, guidebook.K_NDVI)
PRODUCTS.add_product(PRODUCT_IST, PAIR_1000M, "ice_surface_temperature", guidebook.FT_IST, guidebook.K_IST, units='K')
PRODUCTS.add_product(PRODUCT_INV, PAIR_1000M, "inversion_strength", guidebook.FT_INV, guidebook.K_INV, units='C')
PRODUCTS.add_product(PRODUCT_IND, PAIR_1000M, "inversion_depth", guidebook.FT_INV, guidebook.K_IND, units='m')
PRODUCTS.add_product(PRODUCT_ICON, PAIR_1000M, "ice_concentration", guidebook.FT_ICECON, guidebook.K_ICECON, units='%')
PRODUCTS.add_product(PRODUCT_CTT, PAIR_MOD06, "cloud_top_temperature", guidebook.FT_MOD06CT, guidebook.K_CTT, units='K')
PRODUCTS.add_product(PRODUCT_TPW, PAIR_MOD07, "total_precipitable_water", guidebook.FT_MOD07, guidebook.K_TPW, units='cm')
### secondary products ###
PRODUCTS.add_product(PRODUCT_SLST, PAIR_1000M, "summer_land_surface_temperature", dependencies=(PRODUCT_LST,))
# radiance -> brightness temperature
PRODUCTS.add_product(PRODUCT_BT20, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR20,), units='K')
PRODUCTS.add_product(PRODUCT_BT21, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR21,), units='K')
PRODUCTS.add_product(PRODUCT_BT22, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR22,), units='K')
PRODUCTS.add_product(PRODUCT_BT23, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR23,), units='K')
PRODUCTS.add_product(PRODUCT_BT24, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR24,), units='K')
PRODUCTS.add_product(PRODUCT_BT25, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR25,), units='K')
PRODUCTS.add_product(PRODUCT_BT27, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR27,), units='K')
PRODUCTS.add_product(PRODUCT_BT28, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR28,), units='K')
PRODUCTS.add_product(PRODUCT_BT29, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR29,), units='K')
PRODUCTS.add_product(PRODUCT_BT30, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR30,), units='K')
PRODUCTS.add_product(PRODUCT_BT31, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR31,), units='K')
PRODUCTS.add_product(PRODUCT_BT32, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR32,), units='K')
PRODUCTS.add_product(PRODUCT_BT33, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR33,), units='K')
PRODUCTS.add_product(PRODUCT_BT34, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR34,), units='K')
PRODUCTS.add_product(PRODUCT_BT35, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR35,), units='K')
PRODUCTS.add_product(PRODUCT_BT36, PAIR_1000M, "brightness_temperature", dependencies=(PRODUCT_IR36,), units='K')
PRODUCTS.add_product(PRODUCT_FOG, PAIR_1000M, "temperature_difference", dependencies=(PRODUCT_BT31, PRODUCT_BT20, PRODUCT_SZA), units='K')
# cloud clear and land/sea mask cleared
PRODUCTS.add_product(PRODUCT_CLEAR_SST, PAIR_1000M, "sea_surface_temperature", dependencies=(PRODUCT_SST, PRODUCT_CMASK, PRODUCT_LSMASK, PRODUCT_SIMASK), units='C')
PRODUCTS.add_product(PRODUCT_CLEAR_LST, PAIR_1000M, "land_surface_temperature", dependencies=(PRODUCT_LST, PRODUCT_CMASK, PRODUCT_LSMASK), units='K')
PRODUCTS.add_product(PRODUCT_CLEAR_SLST, PAIR_1000M, "summer_land_surface_temperature", dependencies=(PRODUCT_CLEAR_LST,), units='K')
PRODUCTS.add_product(PRODUCT_CLEAR_NDVI, PAIR_1000M, "ndvi", dependencies=(PRODUCT_NDVI, PRODUCT_CMASK, PRODUCT_LSMASK))
# adaptive btemp
PRODUCTS.add_product(PRODUCT_ADAPTIVE_BT20, PAIR_1000M, "equalized_brightness_temperature", dependencies=(PRODUCT_BT20,))
PRODUCTS.add_product(PRODUCT_ADAPTIVE_BT27, PAIR_1000M, "equalized_brightness_temperature", dependencies=(PRODUCT_VIS02,))
PRODUCTS.add_product(PRODUCT_ADAPTIVE_BT31, PAIR_1000M, "equalized_brightness_temperature", dependencies=(PRODUCT_VIS07,))


VIS_PRODUCTS = [
    PRODUCT_VIS01,
    PRODUCT_VIS02,
    PRODUCT_VIS03,
    PRODUCT_VIS04,
    PRODUCT_VIS05,
    PRODUCT_VIS06,
    PRODUCT_VIS07,
    PRODUCT_VIS26,
]
RAD_PRODUCTS = [
    PRODUCT_IR20,
    PRODUCT_IR21,
    PRODUCT_IR22,
    PRODUCT_IR23,
    PRODUCT_IR24,
    PRODUCT_IR25,
    PRODUCT_IR27,
    PRODUCT_IR28,
    PRODUCT_IR29,
    PRODUCT_IR30,
    PRODUCT_IR31,
    PRODUCT_IR32,
    PRODUCT_IR33,
    PRODUCT_IR34,
    PRODUCT_IR35,
    PRODUCT_IR36,
]
BT_PRODUCTS = [
    PRODUCT_BT20,
    PRODUCT_BT21,
    PRODUCT_BT22,
    PRODUCT_BT23,
    PRODUCT_BT24,
    PRODUCT_BT25,
    PRODUCT_BT27,
    PRODUCT_BT28,
    PRODUCT_BT29,
    PRODUCT_BT30,
    PRODUCT_BT31,
    PRODUCT_BT32,
    PRODUCT_BT33,
    PRODUCT_BT34,
    PRODUCT_BT35,
    PRODUCT_BT36,
]
EDR_PRODUCTS = [
    PRODUCT_CLEAR_SST,
    PRODUCT_CLEAR_LST,
    PRODUCT_CLEAR_SLST,
    PRODUCT_CLEAR_NDVI,
    PRODUCT_IST,
    PRODUCT_INV,
    PRODUCT_IND,
    PRODUCT_ICON,
    PRODUCT_CTT,
    PRODUCT_TPW,
    PRODUCT_FOG,
]
MASK_PRODUCTS = [
    PRODUCT_CMASK,
    PRODUCT_LSMASK,
    PRODUCT_SIMASK,
]


class Frontend(roles.FrontendRole):
    FILE_EXTENSIONS = [".hdf"]

    def __init__(self, **kwargs):
        super(Frontend, self).__init__(**kwargs)
        self.load_files(self.find_files_with_extensions())

        self.secondary_product_functions = {
            PRODUCT_SLST: self.create_slst,
            PRODUCT_BT20: self.create_bt_from_ir,
            PRODUCT_BT21: self.create_bt_from_ir,
            PRODUCT_BT22: self.create_bt_from_ir,
            PRODUCT_BT23: self.create_bt_from_ir,
            PRODUCT_BT24: self.create_bt_from_ir,
            PRODUCT_BT25: self.create_bt_from_ir,
            PRODUCT_BT27: self.create_bt_from_ir,
            PRODUCT_BT28: self.create_bt_from_ir,
            PRODUCT_BT29: self.create_bt_from_ir,
            PRODUCT_BT30: self.create_bt_from_ir,
            PRODUCT_BT31: self.create_bt_from_ir,
            PRODUCT_BT32: self.create_bt_from_ir,
            PRODUCT_BT33: self.create_bt_from_ir,
            PRODUCT_BT34: self.create_bt_from_ir,
            PRODUCT_BT35: self.create_bt_from_ir,
            PRODUCT_BT36: self.create_bt_from_ir,
            PRODUCT_ADAPTIVE_BT20: self.create_adaptive_btemp,
            PRODUCT_ADAPTIVE_BT27: self.create_adaptive_btemp,
            PRODUCT_ADAPTIVE_BT31: self.create_adaptive_btemp,
            PRODUCT_FOG: self.create_fog,
            PRODUCT_CLEAR_SST: self.create_cloud_land_cleared,
            PRODUCT_CLEAR_LST: self.create_cloud_sea_cleared,
            PRODUCT_CLEAR_SLST: self.create_slst,
            PRODUCT_CLEAR_NDVI: self.create_cloud_sea_cleared,
            }

        for p, p_def in PRODUCTS.items():
            if p_def.data_kind == "reflectance" and p_def.dependencies:
                self.secondary_product_functions[p] = self.day_check_reflectance

    def load_files(self, file_paths):
        """Sort files by 'file type' and create objects to help load the data later.

        This method should not be called by the user.
        """
        self.file_readers = {}
        for file_type, file_type_info in guidebook.FILE_TYPES.items():
            self.file_readers[file_type] = guidebook.MultiFileReader(file_type_info)

        # Don't modify the passed list (we use in place operations)
        file_paths_left = []
        for fp in file_paths:
            try:
                h = guidebook.HDFEOSReader(fp)
                LOG.debug("Recognize file %s as file type %s", fp, h.file_type)
                if h.file_type in self.file_readers:
                    self.file_readers[h.file_type].add_file(h)
                else:
                    LOG.debug("Recognized the file type, but don't know anything more about the file")
            except StandardError:
                LOG.debug("Could not parse HDF file as HDF-EOS file: %s", fp)
                LOG.debug("File parsing error: ", exc_info=True)
                file_paths_left.append(fp)
                continue

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

        self.available_file_types = self.file_readers.keys()

    @property
    def begin_time(self):
        return self.file_readers[self.available_file_types[0]].begin_time

    @property
    def end_time(self):
        return self.file_readers[self.available_file_types[0]].end_time

    @property
    def all_product_names(self):
        return PRODUCTS.keys()

    @property
    def available_product_names(self):
        """Return all loadable products including all geolocation products.
        """
        raw_products = [p for p in PRODUCTS.all_raw_products if self.raw_product_available(p)]
        return sorted(PRODUCTS.get_product_dependents(raw_products))

    @property
    def default_products(self):
        """Logical default list of products if not specified by the user
        """
        if os.getenv("P2G_MODIS_DEFAULTS", None):
            return os.getenv("P2G_MODIS_DEFAULTS")
        defaults = []
        available = self.available_product_names

        # If we can't cloud/land/sea clear these products then we want the regular uncleared products
        # If we can clear them then we don't want the uncleared products
        for clearp, p in ((PRODUCT_CLEAR_SST, PRODUCT_SST), (PRODUCT_CLEAR_LST, PRODUCT_LST),
                          (PRODUCT_CLEAR_SLST, PRODUCT_SLST), (PRODUCT_CLEAR_NDVI, PRODUCT_NDVI)):
            if clearp in available:
                defaults.append(clearp)
                continue
            if p in available:
                defaults.append(p)

        other_defaults = [
            PRODUCT_VIS01,
            PRODUCT_VIS02,
            PRODUCT_VIS03,
            PRODUCT_VIS04,
            PRODUCT_VIS05,
            PRODUCT_VIS06,
            PRODUCT_VIS07,
            PRODUCT_VIS26,
            PRODUCT_BT20,
            PRODUCT_BT21,
            PRODUCT_BT22,
            PRODUCT_BT23,
            PRODUCT_BT24,
            PRODUCT_BT25,
            PRODUCT_BT27,
            PRODUCT_BT28,
            PRODUCT_BT29,
            PRODUCT_BT30,
            PRODUCT_BT31,
            PRODUCT_BT32,
            PRODUCT_BT33,
            PRODUCT_BT34,
            PRODUCT_BT35,
            PRODUCT_BT36,
            PRODUCT_IST, PRODUCT_INV, PRODUCT_IND, PRODUCT_ICON, PRODUCT_CTT, PRODUCT_TPW, PRODUCT_FOG,
        ]
        return defaults + other_defaults

    def raw_product_available(self, product_name):
        """Is it possible to load the provided product with the files provided to the `Frontend`.

        :returns: True if product can be loaded, False otherwise (including if product is not a raw product)
        """
        product_def = PRODUCTS[product_name]
        if product_def.is_raw:
            if isinstance(product_def.file_type, str):
                file_type = product_def.file_type
            else:
                return any(ft in self.file_readers for ft in product_def.file_type)

            return file_type in self.file_readers
        return False

    def create_swath_definition(self, lon_product, lat_product):
        product_def = PRODUCTS[lon_product["product_name"]]
        file_type = product_def.get_file_type(self.available_file_types)
        lon_file_reader = self.file_readers[file_type]
        product_def = PRODUCTS[lat_product["product_name"]]
        file_type = product_def.get_file_type(self.available_file_types)
        lat_file_reader = self.file_readers[file_type]

        # sanity check
        for k in ["data_type", "swath_rows", "swath_columns", "rows_per_scan", "fill_value"]:
            if lon_product[k] != lat_product[k]:
                if k == "fill_value" and numpy.isnan(lon_product[k]) and numpy.isnan(lat_product[k]):
                    # NaN special case: NaNs can't be compared normally
                    continue
                LOG.error("Longitude and latitude products do not have equal attributes: %s", k)
                raise RuntimeError("Longitude and latitude products do not have equal attributes: %s" % (k,))

        swath_name = GEO_PAIRS[product_def.get_geo_pair_name(self.available_file_types)].name
        swath_definition = containers.SwathDefinition(
            swath_name=swath_name, longitude=lon_product["swath_data"], latitude=lat_product["swath_data"],
            data_type=lon_product["data_type"], swath_rows=lon_product["swath_rows"],
            swath_columns=lon_product["swath_columns"], rows_per_scan=lon_product["rows_per_scan"],
            source_filenames=sorted(set(lon_file_reader.filepaths + lat_file_reader.filepaths)),
            # nadir_resolution=lon_file_reader.nadir_resolution, limb_resolution=lat_file_reader.limb_resolution,
            fill_value=lon_product["fill_value"],
            )

        # Tell the lat and lon products not to delete the data arrays, the swath definition will handle that
        lon_product.set_persist()
        lat_product.set_persist()

        # mmmmm, almost circular
        lon_product["swath_definition"] = swath_definition
        lat_product["swath_definition"] = swath_definition

        return swath_definition

    def create_raw_swath_object(self, product_name, swath_definition):
        product_def = PRODUCTS[product_name]
        try:
            file_type = product_def.get_file_type(self.available_file_types)
            file_key = product_def.get_file_key(self.available_file_types)
        except StandardError:
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
            data_type = file_reader.get_data_type(file_key)
            fill_value = file_reader.get_fill_value(file_key)
            shape = file_reader.write_var_to_flat_binary(file_key, filename, dtype=data_type)
            rows_per_scan = GEO_PAIRS[product_def.get_geo_pair_name(self.available_file_types)].rows_per_scan
        except StandardError:
            LOG.error("Could not extract data from file")
            LOG.debug("Extraction exception: ", exc_info=True)
            raise

        one_swath = containers.SwathProduct(
            product_name=product_name, description=product_def.description, units=product_def.units,
            satellite=file_reader.satellite, instrument=file_reader.instrument,
            begin_time=file_reader.begin_time, end_time=file_reader.end_time,
            swath_definition=swath_definition, fill_value=fill_value,
            swath_rows=shape[0], swath_columns=shape[1], data_type=data_type, swath_data=filename,
            source_filenames=file_reader.filepaths, data_kind=product_def.data_kind, rows_per_scan=rows_per_scan
        )
        return one_swath

    def create_secondary_swath_object(self, product_name, swath_definition, filename, data_type, products_created):
        product_def = PRODUCTS[product_name]
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
        return one_swath

    def create_scene(self, products=None, **kwargs):
        LOG.debug("Loading scene data...")
        # If the user didn't provide the products they want, figure out which ones we can create
        if products is None:
            LOG.debug("No products specified to frontend, will try to load logical defaults")
            products = self.default_products

        # Do we actually have all of the files needed to create the requested products?
        products = self.loadable_products(products)

        # Needs to be ordered (least-depended product -> most-depended product)
        products_needed = PRODUCTS.dependency_ordered_products(products)
        geo_pairs_needed = PRODUCTS.geo_pairs_for_products(products_needed, self.available_file_types)
        # both lists below include raw products that need extra processing/masking
        raw_products_needed = (p for p in products_needed if PRODUCTS.is_raw(p, geo_is_raw=False))
        secondary_products_needed = [p for p in products_needed if PRODUCTS.needs_processing(p)]
        for p in secondary_products_needed:
            if p not in self.secondary_product_functions:
                msg = "Product (secondary or extra processing) required, but not sure how to make it: '%s'" % (p,)
                LOG.error(msg)
                raise ValueError(msg)

        # final scene object we'll be providing to the caller
        scene = containers.SwathScene()
        # Dictionary of all products created so far (local variable so we don't hold on to any product objects)
        products_created = {}
        swath_definitions = {}

        # Load geolocation files
        for geo_pair_name in geo_pairs_needed:
            ### Lon Product ###
            lon_product_name = GEO_PAIRS[geo_pair_name].lon_product
            LOG.info("Creating navigation product '%s'", lon_product_name)
            lon_swath = products_created[lon_product_name] = self.create_raw_swath_object(lon_product_name, None)
            if lon_product_name in products:
                scene[lon_product_name] = lon_swath

            ### Lat Product ###
            lat_product_name = GEO_PAIRS[geo_pair_name].lat_product
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
                swath_def = swath_definitions[PRODUCTS[product_name].get_geo_pair_name(self.available_file_types)]
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
            swath_def = swath_definitions[PRODUCTS[product_name].get_geo_pair_name(self.available_file_types)]

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

    def create_slst(self, product_name, swath_definition, products_created):
        product_def = PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) != 1:
            LOG.error("Expected 1 dependencies to create SLST product, got %d" % (len(deps),))
            raise RuntimeError("Expected 1 dependencies to create SLST product, got %d" % (len(deps),))

        lst_product_name = deps[0]
        lst_product = products_created[lst_product_name]
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        try:
            shutil.copyfile(lst_product["swath_data"], filename)
            one_swath = self.create_secondary_swath_object(product_name, swath_definition, filename,
                                                           lst_product["data_type"], products_created)
        except StandardError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        return one_swath

    def create_bt_from_ir(self, product_name, swath_definition, products_created):
        product_def = PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) != 1:
            LOG.error("Expected 1 dependencies to create BT product from IR, got %d" % (len(deps),))
            raise RuntimeError("Expected 1 dependencies to create BT product from IR, got %d" % (len(deps),))

        ir_product_name = deps[0]
        ir_product = products_created[ir_product_name]
        ir_mask = ir_product.get_data_mask()
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        try:
            output_data = ir_product.copy_array(filename=filename, read_only=False)
            sat = ir_product["satellite"]
            band_number = {
                PRODUCT_BT20: 20,
                PRODUCT_BT21: 21,
                PRODUCT_BT22: 22,
                PRODUCT_BT23: 23,
                PRODUCT_BT24: 24,
                PRODUCT_BT25: 25,
                PRODUCT_BT27: 27,
                PRODUCT_BT28: 28,
                PRODUCT_BT29: 29,
                PRODUCT_BT30: 30,
                PRODUCT_BT31: 31,
                PRODUCT_BT32: 32,
                PRODUCT_BT33: 33,
                PRODUCT_BT34: 34,
                PRODUCT_BT35: 35,
                PRODUCT_BT36: 36,
            }[product_name]
            # since the input and output fill value and the invalid calculation value are all NaN we don't have to do
            # any extra calculations
            output_data[~ir_mask] = bright_shift(sat.title(), output_data[~ir_mask], band_number)

            one_swath = self.create_secondary_swath_object(product_name, swath_definition, filename,
                                                           ir_product["data_type"], products_created)
        except StandardError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        return one_swath

    def create_adaptive_btemp(self, product_name, swath_definition, products_created):
        product_def = PRODUCTS[product_name]
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

    def create_fog(self, product_name, swath_definition, products_created):
        product_def = PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) != 3:
            LOG.error("Expected 3 dependencies to create FOG/temperature difference product, got %d" % (len(deps),))
            raise RuntimeError("Expected 3 dependencies to create FOG/temperature difference product, got %d" % (len(deps),))

        PRODUCTS.add_product(PRODUCT_FOG, PAIR_1000M, "temperature_difference", dependencies=(PRODUCT_BT20, PRODUCT_BT31, PRODUCT_SZA))
        left_term_name = deps[0]
        right_term_name = deps[1]
        sza_product_name = deps[2]
        fill = products_created[left_term_name]["fill_value"]
        left_data = products_created[left_term_name].get_data_array()
        left_mask = products_created[left_term_name].get_data_mask()
        right_data = products_created[right_term_name].get_data_array()
        right_mask = products_created[right_term_name].get_data_mask()
        sza_data = products_created[sza_product_name].get_data_array()
        sza_mask = products_created[sza_product_name].get_data_mask()
        night_mask = sza_data >= 90  # where is it night
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
            fraction_night = numpy.count_nonzero(valid_night_mask) / (float(sza_data.size) - numpy.count_nonzero(invalid_mask))
            if fraction_night < 0.10:
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

    def create_cloud_land_cleared(self, product_name, swath_definition, products_created,
                                  cloud_values_to_clear=[1, 2], lsmask_values_to_clear=[3, 4], simask_values_to_clear=[1]):
        product_def = PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) == 4:
            base_product_name = deps[0]
            cmask_product_name = deps[1]
            lsmask_product_name = deps[2]
            simask_product_name = deps[3]
        elif len(deps) == 3:
            base_product_name = deps[0]
            cmask_product_name = deps[1]
            lsmask_product_name = deps[2]
            simask_product_name = None
        else:
            LOG.error("Expected 3 or 4 dependencies to create cleared product, got %d" % (len(deps),))
            raise RuntimeError("Expected 3 or 4 dependencies to create cleared product, got %d" % (len(deps),))

        base_product = products_created[base_product_name]
        fill = base_product["fill_value"]
        base_mask = base_product.get_data_mask()
        cmask = products_created[cmask_product_name].get_data_array()
        lsmask = products_created[lsmask_product_name].get_data_array()
        if simask_product_name is not None:
            simask = products_created[simask_product_name].get_data_array()
        else:
            simask = None
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        try:
            output_data = base_product.copy_array(filename=filename, read_only=False)
            # in1d operates on 1 dimensional arrays so we need to reshape it back to the swath shape
            shape = (base_product["swath_rows"], base_product["swath_columns"])
            clearable_mask = base_mask | numpy.in1d(cmask, cloud_values_to_clear).reshape(shape) | numpy.in1d(lsmask, lsmask_values_to_clear).reshape(shape)
            if simask is not None:
                LOG.debug("Clearing {!r} Snow/Ice values from {}".format(simask_values_to_clear, product_name))
                clearable_mask |= numpy.in1d(simask, simask_values_to_clear).reshape(shape)
            output_data[clearable_mask] = fill

            one_swath = self.create_secondary_swath_object(product_name, swath_definition, filename,
                                                           base_product["data_type"], products_created)
        except StandardError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        return one_swath

    def create_cloud_sea_cleared(self, product_name, swath_definition, products_created):
        return self.create_cloud_land_cleared(product_name, swath_definition, products_created,
                                              lsmask_values_to_clear=[1])

    def _get_day_percentage(self, sza_swath):
        if "day_percentage" not in sza_swath:
            sza_data = sza_swath.get_data_array()
            invalid_mask = sza_swath.get_data_mask()
            valid_day_mask = (sza_data < 90) & ~invalid_mask
            fraction_day = numpy.count_nonzero(valid_day_mask) / (float(sza_data.size) - numpy.count_nonzero(invalid_mask))
            sza_swath["day_percentage"] = fraction_day * 100.0
        else:
            LOG.debug("Day percentage found in SZA swath already")
        return sza_swath["day_percentage"]

    def day_check_reflectance(self, product_name, swath_definition, products_created, fill=numpy.nan):
        product_def = PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) != 1:
            LOG.error("Expected 1 dependencies to check night mask, got %d" % (len(deps),))
            raise RuntimeError("Expected 1 dependencies to check night mask, got %d" % (len(deps),))

        sza_swath = products_created[deps[0]]
        day_percentage = self._get_day_percentage(sza_swath)
        LOG.debug("Reflectance product's scene has %f%% day data", day_percentage)
        if day_percentage < 10.0:
            LOG.info("Will not create product '%s' because there is less than 10%% of day data", product_name)
            return None
        return products_created[product_name]


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    from polar2grid.core.script_utils import ExtendAction, ExtendConstAction
    # Set defaults for other components that may be used in polar2grid processing
    parser.set_defaults(fornav_D=10, fornav_d=1)

    # Use the append_const action to handle adding products to the list
    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                       help="List available frontend products and exit")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    group.add_argument("-p", "--products", dest="products", nargs="+", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    group.add_argument('--ir-products', dest='products', action=ExtendConstAction, const=RAD_PRODUCTS,
                       help="Add IR products to list of products")
    group.add_argument('--bt-products', dest='products', action=ExtendConstAction, const=BT_PRODUCTS,
                       help="Add BT products to list of products")
    group.add_argument('--vis-products', dest='products', action=ExtendConstAction, const=VIS_PRODUCTS,
                       help="Add Visible products to list of products")
    group.add_argument('--edr-products', dest='products', action=ExtendConstAction, const=EDR_PRODUCTS,
                       help="Add EDR products and temperature difference 'fog' to list of products")
    group.add_argument('--mask-products', dest='products', action=ExtendConstAction, const=MASK_PRODUCTS,
                       help="Add cloud and other mask products to list of products")
    group.add_argument('--adaptive-bt', dest='products', action=ExtendConstAction, const=ADAPTIVE_BT_PRODUCTS,
                       help="Create adaptively scaled brightness temperature bands")
    return ["Frontend Initialization", "Frontend Swath Extraction"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    parser = create_basic_parser(description="Extract MODIS swath data into binary files")
    subgroup_titles = add_frontend_argument_groups(parser)
    parser.add_argument('-f', dest='data_files', nargs="+", default=[],
                        help="List of data files or directories to extract data from")
    parser.add_argument('-o', dest="output_filename", default=None,
                        help="Output filename for JSON scene (default is to stdout)")
    global_keywords = ["exit_on_error", "keep_intermediate", "overwrite_existing"]
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
