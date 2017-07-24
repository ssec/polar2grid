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
"""The Corrected Reflectance Reader operates on corrected reflectance files created from
VIIRS Science Data Record (SDR) files or MODIS Level 1B (L1B) files, in either IMAPP or
NASA Archive naming conventions. Currently corrected reflectance files are created by 
third party software developed by NASA. The ``CREFL_SPA`` algorithm for MODIS and 
``CVIIRS_SPA`` algorithm for VIIRS can be found here: 
http://directreadout.sci.gsfc.nasa.gov/?id=software .

Polar2Grid uses its own patched version of the CREFL processing code for VIIRS data. This code is available in
the main code repository and fixes a few bugs that were not fixed in the original CREFL code at the time of writing.  

Output CREFL software HDF4 product naming conventions are:

  +-----------------------------------+--------------------------------------------+
  | **MODIS (250m, 500m and 1 km)**   |    **VIIRS  (I and M Bands)**              |
  +===================================+============================================+
  | a1 or                             |                                            | 
  | t1.YYDDD.HHMM.crefl.1000m.hdf     | CREFLI_npp_dYYYYMMDD_tHHMMSSS_eHHMMSSS.hdf |
  +-----------------------------------+--------------------------------------------+
  | a1 or                             |                                            | 
  | t1.YYDDD.HHMM.crefl.500m.hdf      | CREFLM_npp_dYYYYMMDD_tHHMMSSS_eHHMMSSS.hdf |
  +-----------------------------------+--------------------------------------------+
  | a1 or                             |                                            | 
  | t1.YYDDD.HHMM.crefl.250m.hdf      |                                            |
  +-----------------------------------+--------------------------------------------+

After processing the output can be provided to Polar2Grid to create true color images or other RGB images.

The CREFL reader can create True Color and False Color RGB composites when the
corresponding ``--true-color`` and ``--false-color`` flags are specified. The
default is to create a True Color image if no parameters are specified.
However when used with the AWIPS writer the default is to apply a ratio
sharpening between low and high resolution bands to produce better quality
single band images since AWIPS does not support 3-dimensional arrays. These
defaults can all be turned off with the ``--no-compositors`` flag.

The CREFL reader accepts output from MODIS and VIIRS corrected reflectance
processing. If provided with L1B or SDR files it will attempt to call the proper
programs to convert the files. The required commands that must be available
are:

 - h5SDS_transfer_rename
 - cviirs (for VIIRS corrected reflectance)
 - crefl (for MODIS corrected reflectance)

The CREFL software also requires ancillary data in the form of ``tbase.hdf``
and ``CMGDEM.hdf`` files for the MODIS and VIIRS processing respectively.
These files are provided in the CSPP software bundle and are automatically
detected by the software. Alternate locations can be specified with the
``P2G_CMODIS_ANCPATH`` and ``P2G_CVIIRS_ANCPATH`` environment variables.

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--fornav-D`` option is set to 40 and the
``--fornav-d`` option is set to 1. Note that for working with MODIS data
it may produce lower quality images with these settings so the
``--fornav-D`` option should be set to 10 on the command line::

    --fornav-D 10

The following products are provided by this reader:


    +--------------------+--------------------------------------------+
    | Product Name       | Description                                |
    +====================+============================================+
    | viirs_crefl01      | Corrected Reflectance from VIIRS M05 Band  |
    +--------------------+--------------------------------------------+
    | viirs_crefl02      | Corrected Reflectance from VIIRS M07 Band  |
    +--------------------+--------------------------------------------+
    | viirs_crefl03      | Corrected Reflectance from VIIRS M03 Band  |
    +--------------------+--------------------------------------------+
    | viirs_crefl04      | Corrected Reflectance from VIIRS M04 Band  |
    +--------------------+--------------------------------------------+
    | viirs_crefl05      | Corrected Reflectance from VIIRS M08 Band  |
    +--------------------+--------------------------------------------+
    | viirs_crefl06      | Corrected Reflectance from VIIRS M10 Band  |
    +--------------------+--------------------------------------------+
    | viirs_crefl07      | Corrected Reflectance from VIIRS M11 Band  |
    +--------------------+--------------------------------------------+
    | viirs_crefl08      | Corrected Reflectance from VIIRS I01 Band  |
    +--------------------+--------------------------------------------+
    | viirs_crefl09      | Corrected Reflectance from VIIRS I02 Band  |
    +--------------------+--------------------------------------------+
    | viirs_crefl10      | Corrected Reflectance from VIIRS I03 Band  |
    +--------------------+--------------------------------------------+
    | modis_crefl01_1000m| Corrected Reflectance from MODIS Band 1    |
    +--------------------+--------------------------------------------+
    | modis_crefl02_1000m| Corrected Reflectance from MODIS Band 2    |
    +--------------------+--------------------------------------------+
    | modis_crefl03_1000m| Corrected Reflectance from MODIS Band 3    |
    +--------------------+--------------------------------------------+
    | modis_crefl04_1000m| Corrected Reflectance from MODIS Band 4    |
    +--------------------+--------------------------------------------+
    | modis_crefl05_1000m| Corrected Reflectance from MODIS Band 5    |
    +--------------------+--------------------------------------------+
    | modis_crefl06_1000m| Corrected Reflectance from MODIS Band 6    |
    +--------------------+--------------------------------------------+
    | modis_crefl07_1000m| Corrected Reflectance from MODIS Band 7    |
    +--------------------+--------------------------------------------+
    | modis_crefl01_500m | Corrected Reflectance from MODIS Band 1    |
    +--------------------+--------------------------------------------+
    | modis_crefl02_500m | Corrected Reflectance from MODIS Band 2    |
    +--------------------+--------------------------------------------+
    | modis_crefl03_500m | Corrected Reflectance from MODIS Band 3    |
    +--------------------+--------------------------------------------+
    | modis_crefl04_500m | Corrected Reflectance from MODIS Band 4    |
    +--------------------+--------------------------------------------+
    | modis_crefl05_500m | Corrected Reflectance from MODIS Band 5    |
    +--------------------+--------------------------------------------+
    | modis_crefl06_500m | Corrected Reflectance from MODIS Band 6    |
    +--------------------+--------------------------------------------+
    | modis_crefl07_500m | Corrected Reflectance from MODIS Band 7    |
    +--------------------+--------------------------------------------+
    | modis_crefl01_250m | Corrected Reflectance from MODIS Band 1    |
    +--------------------+--------------------------------------------+
    | modis_crefl02_250m | Corrected Reflectance from MODIS Band 2    |
    +--------------------+--------------------------------------------+
    | modis_crefl03_250m | Corrected Reflectance from MODIS Band 3    |
    +--------------------+--------------------------------------------+
    | modis_crefl04_250m | Corrected Reflectance from MODIS Band 4    |
    +--------------------+--------------------------------------------+

"""
__docformat__ = "restructuredtext en"

import sys
from datetime import datetime, timedelta
from pyhdf import SD

import logging
import numpy
import os

import polar2grid.modis.modis_guidebook as modis_guidebook
import polar2grid.modis.modis_to_swath as modis_module
import polar2grid.viirs.guidebook as viirs_guidebook
import polar2grid.viirs.io as viirs_io
import polar2grid.viirs.swath as viirs_module
from polar2grid.core import containers, roles
from polar2grid.core.frontend_utils import ProductDict, GeoPairDict

LOG = logging.getLogger(__name__)

# HDF4 crefl files
FT_CREFL_1000M = modis_guidebook.FT_CREFL_1000M
FT_CREFL_500M = modis_guidebook.FT_CREFL_500M
FT_CREFL_250M = modis_guidebook.FT_CREFL_250M
FT_CREFL_M = "ft_crefl_m"
FT_CREFL_I = "ft_crefl_i"

FT_GEO = modis_guidebook.FT_GEO
FT_GITCO = viirs_guidebook.FILE_TYPE_GITCO
FT_GIMGO = viirs_guidebook.FILE_TYPE_GIMGO
FT_GMTCO = viirs_guidebook.FILE_TYPE_GMTCO
FT_GMODO = viirs_guidebook.FILE_TYPE_GMODO

K_CREFL01 = "crefl01_fk"
K_CREFL02 = "crefl02_fk"
K_CREFL03 = "crefl03_fk"
K_CREFL04 = "crefl04_fk"
K_CREFL05 = "crefl05_fk"
K_CREFL06 = "crefl06_fk"
K_CREFL07 = "crefl07_fk"
K_CREFL08 = "crefl08_fk"
K_CREFL09 = "crefl09_fk"
K_CREFL10 = "crefl10_fk"

# File Info for CREFL files

class FileInfo(modis_guidebook.FileInfo):
    def __init__(self, *args, **kwargs):
        # I think (from reading source code) that 32767 is fill, 32766 is missing, 32765 is saturated
        # The saturated pixels then should therefore already be at the top of the range
        kwargs.setdefault("range_attr_name", (0, 32765))
        kwargs.setdefault("fill_attr_name", 32766)
        # kwargs.setdefault("clip_saturated", True)  # not needed since the sat value is the top value
        super(FileInfo, self).__init__(*args, **kwargs)

FILE_TYPES = {}
FILE_TYPES[FT_CREFL_1000M] = {
    K_CREFL01: FileInfo("CorrRefl_01"),
    K_CREFL02: FileInfo("CorrRefl_02"),
    K_CREFL03: FileInfo("CorrRefl_03"),
    K_CREFL04: FileInfo("CorrRefl_04"),
    K_CREFL05: FileInfo("CorrRefl_05"),
    K_CREFL06: FileInfo("CorrRefl_06"),
    K_CREFL07: FileInfo("CorrRefl_07"),
}
FILE_TYPES[FT_CREFL_500M] = {
    K_CREFL01: FileInfo("CorrRefl_01"),
    K_CREFL02: FileInfo("CorrRefl_02"),
    K_CREFL03: FileInfo("CorrRefl_03"),
    K_CREFL04: FileInfo("CorrRefl_04"),
    K_CREFL05: FileInfo("CorrRefl_05"),
    K_CREFL06: FileInfo("CorrRefl_06"),
    K_CREFL07: FileInfo("CorrRefl_07"),
}
FILE_TYPES[FT_CREFL_250M] = {
    K_CREFL01: FileInfo("CorrRefl_01"),
    K_CREFL02: FileInfo("CorrRefl_02"),
    K_CREFL03: FileInfo("CorrRefl_03"),
    K_CREFL04: FileInfo("CorrRefl_04"),
}
FILE_TYPES[FT_CREFL_M] = {
    K_CREFL01: FileInfo("CorrRefl_01"),
    K_CREFL02: FileInfo("CorrRefl_02"),
    K_CREFL03: FileInfo("CorrRefl_03"),
    K_CREFL04: FileInfo("CorrRefl_04"),
    K_CREFL05: FileInfo("CorrRefl_05"),
    K_CREFL06: FileInfo("CorrRefl_06"),
    K_CREFL07: FileInfo("CorrRefl_07"),
}
FILE_TYPES[FT_CREFL_I] = {
    K_CREFL08: FileInfo("CorrRefl_08"),
    K_CREFL09: FileInfo("CorrRefl_09"),
    K_CREFL10: FileInfo("CorrRefl_10"),
}

# CREFL File Readers


class MODISFileReader(modis_guidebook.FileReader):
    pass


class VIIRSCreflReader(modis_guidebook.HDFReader):
    def __init__(self, filename):
        self.filename = os.path.basename(filename)
        self.filepath = os.path.realpath(filename)
        self._hdf_handle = SD.SD(self.filepath, SD.SDC.READ)
        # CREFLM_npp_d20141103_t1758468_e1800112.hdf
        fn = os.path.splitext(self.filename)[0]
        parts = fn.split("_")
        self.satellite = parts[1].lower()
        self.instrument = "viirs"

        # Parse out the datetime, making sure to add the microseconds and set the timezone to UTC
        begin_us = int(parts[3][-1]) * 100000
        self.begin_time = datetime.strptime(parts[2][1:] + parts[3][1:-1], "%Y%m%d%H%M%S").replace(microsecond=begin_us)
        end_us = int(parts[4][-1]) * 100000
        self.end_time = datetime.strptime(parts[2][1:] + parts[4][1:-1], "%Y%m%d%H%M%S").replace(microsecond=end_us)
        if self.end_time < self.begin_time:
            self.end_time += timedelta(days=1)


class VIIRSFileReader(MODISFileReader):
    def __init__(self, filename_or_hdf_obj, file_type_info):
        if isinstance(filename_or_hdf_obj, (str, unicode)):
            filename_or_hdf_obj = VIIRSCreflReader(filename_or_hdf_obj)
        super(VIIRSFileReader, self).__init__(filename_or_hdf_obj, file_type_info)

        self.instrument = self.file_handle.instrument.lower()
        self.satellite = self.file_handle.satellite.lower()
        self.begin_time = self.file_handle.begin_time
        self.end_time = self.file_handle.end_time


class MultiFileReader(modis_guidebook.MultiFileReader):
    def __init__(self, file_type_info, single_class=MODISFileReader):
        super(MultiFileReader, self).__init__(file_type_info, single_class)

# VIIRS crefl products
# Low resolution (M band resolution)
PRODUCT_VCR01 = "viirs_crefl01"
PRODUCT_VCR02 = "viirs_crefl02"
PRODUCT_VCR03 = "viirs_crefl03"
PRODUCT_VCR04 = "viirs_crefl04"
PRODUCT_VCR05 = "viirs_crefl05"
PRODUCT_VCR06 = "viirs_crefl06"
PRODUCT_VCR07 = "viirs_crefl07"
# High resolution (I band resolution)
PRODUCT_VCR08 = "viirs_crefl08"
PRODUCT_VCR09 = "viirs_crefl09"
PRODUCT_VCR10 = "viirs_crefl10"

# MODIS crefl products
# Low resolution (1000m band resolution)
PRODUCT_MCR01_1000M = "modis_crefl01_1000m"
PRODUCT_MCR02_1000M = "modis_crefl02_1000m"
PRODUCT_MCR03_1000M = "modis_crefl03_1000m"
PRODUCT_MCR04_1000M = "modis_crefl04_1000m"
PRODUCT_MCR05_1000M = "modis_crefl05_1000m"
PRODUCT_MCR06_1000M = "modis_crefl06_1000m"
PRODUCT_MCR07_1000M = "modis_crefl07_1000m"

# Medium resolution (500m)
PRODUCT_MCR01_500M = "modis_crefl01_500m"
PRODUCT_MCR02_500M = "modis_crefl02_500m"
PRODUCT_MCR03_500M = "modis_crefl03_500m"
PRODUCT_MCR04_500M = "modis_crefl04_500m"
PRODUCT_MCR05_500M = "modis_crefl05_500m"
PRODUCT_MCR06_500M = "modis_crefl06_500m"
PRODUCT_MCR07_500M = "modis_crefl07_500m"

# High resolution (250m band resolution)
PRODUCT_MCR01_250M = "modis_crefl01_250m"
PRODUCT_MCR02_250M = "modis_crefl02_250m"
PRODUCT_MCR03_250M = "modis_crefl03_250m"
PRODUCT_MCR04_250M = "modis_crefl04_250m"

PRODUCTS = ProductDict()
GEO_PAIRS = GeoPairDict()

PAIR_INAV = viirs_module.PAIR_INAV
PAIR_MNAV = viirs_module.PAIR_MNAV
PAIR_1000M = modis_module.PAIR_1000M
PAIR_500M = modis_module.PAIR_500M
PAIR_250M = modis_module.PAIR_250M

GEO_PAIRS[PAIR_INAV] = viirs_module.GEO_PAIRS[PAIR_INAV]
GEO_PAIRS[PAIR_MNAV] = viirs_module.GEO_PAIRS[PAIR_MNAV]
GEO_PAIRS[PAIR_1000M] = modis_module.GEO_PAIRS[PAIR_1000M]
GEO_PAIRS[PAIR_500M] = modis_module.GEO_PAIRS[PAIR_500M]
GEO_PAIRS[PAIR_250M] = modis_module.GEO_PAIRS[PAIR_250M]

# VIIRS CREFL
vmin = -0.011764705898
vmax = 1.192352914276
PRODUCTS[viirs_module.PRODUCT_I_LON] = viirs_module.PRODUCTS[viirs_module.PRODUCT_I_LON]
PRODUCTS[viirs_module.PRODUCT_I_LAT] = viirs_module.PRODUCTS[viirs_module.PRODUCT_I_LAT]
PRODUCTS[viirs_module.PRODUCT_M_LON] = viirs_module.PRODUCTS[viirs_module.PRODUCT_M_LON]
PRODUCTS[viirs_module.PRODUCT_M_LAT] = viirs_module.PRODUCTS[viirs_module.PRODUCT_M_LAT]
PRODUCTS.add_product(PRODUCT_VCR01, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL01, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_VCR02, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL02, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_VCR03, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL03, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_VCR04, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL04, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_VCR05, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL05, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_VCR06, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL06, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_VCR07, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL07, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_VCR08, PAIR_INAV, "corrected_reflectance", FT_CREFL_I, K_CREFL08, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_VCR09, PAIR_INAV, "corrected_reflectance", FT_CREFL_I, K_CREFL09, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_VCR10, PAIR_INAV, "corrected_reflectance", FT_CREFL_I, K_CREFL10, units='1', valid_min=vmin, valid_max=vmax)

PRODUCTS[modis_module.PRODUCT_1000M_LON] = modis_module.PRODUCTS[modis_module.PRODUCT_1000M_LON]
PRODUCTS[modis_module.PRODUCT_1000M_LAT] = modis_module.PRODUCTS[modis_module.PRODUCT_1000M_LAT]
PRODUCTS[modis_module.PRODUCT_500M_LON] = modis_module.PRODUCTS[modis_module.PRODUCT_500M_LON]
PRODUCTS[modis_module.PRODUCT_500M_LAT] = modis_module.PRODUCTS[modis_module.PRODUCT_500M_LAT]
PRODUCTS[modis_module.PRODUCT_250M_LON] = modis_module.PRODUCTS[modis_module.PRODUCT_250M_LON]
PRODUCTS[modis_module.PRODUCT_250M_LAT] = modis_module.PRODUCTS[modis_module.PRODUCT_250M_LAT]
PRODUCTS.add_product(PRODUCT_MCR01_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL01, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR02_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL02, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR03_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL03, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR04_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL04, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR05_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL05, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR06_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL06, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR07_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL07, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR01_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL01, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR02_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL02, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR03_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL03, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR04_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL04, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR05_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL05, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR06_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL06, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR07_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL07, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR01_250M, PAIR_250M, "corrected_reflectance", FT_CREFL_250M, K_CREFL01, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR02_250M, PAIR_250M, "corrected_reflectance", FT_CREFL_250M, K_CREFL02, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR03_250M, PAIR_500M, "corrected_reflectance", FT_CREFL_250M, K_CREFL03, units='1', valid_min=vmin, valid_max=vmax)
PRODUCTS.add_product(PRODUCT_MCR04_250M, PAIR_500M, "corrected_reflectance", FT_CREFL_250M, K_CREFL04, units='1', valid_min=vmin, valid_max=vmax)

# R, G, B, HighRes Red
VIIRS_TRUE_COLOR_PRODUCTS = [PRODUCT_VCR01, PRODUCT_VCR04, PRODUCT_VCR03, PRODUCT_VCR08]
# MODIS_TRUE_COLOR_PRODUCTS = [PRODUCT_MCR01_1000M, PRODUCT_MCR04_1000M, PRODUCT_MCR03_1000M, PRODUCT_MCR01_250M]
MODIS_TRUE_COLOR_PRODUCTS = [PRODUCT_MCR01_500M, PRODUCT_MCR04_500M, PRODUCT_MCR03_500M, PRODUCT_MCR01_250M]
TRUE_COLOR_PRODUCTS = VIIRS_TRUE_COLOR_PRODUCTS + MODIS_TRUE_COLOR_PRODUCTS
# R, G, B, HighRes Blue
VIIRS_FALSE_COLOR_PRODUCTS = [PRODUCT_VCR07, PRODUCT_VCR02, PRODUCT_VCR01, PRODUCT_VCR08]
# MODIS_FALSE_COLOR_PRODUCTS = [PRODUCT_MCR07_1000M, PRODUCT_MCR02_1000M, PRODUCT_MCR01_1000M, PRODUCT_MCR01_250M]
MODIS_FALSE_COLOR_PRODUCTS = [PRODUCT_MCR07_500M, PRODUCT_MCR02_500M, PRODUCT_MCR01_500M, PRODUCT_MCR01_250M]
FALSE_COLOR_PRODUCTS = VIIRS_FALSE_COLOR_PRODUCTS + MODIS_FALSE_COLOR_PRODUCTS

# VIIRS Band to CREFL bands
# M05 = CR01
# M07 = CR02
# M03 = CR03
# M04 = CR04
# M08 = CR05
# M10 = CR06
# M11 = CR07
# I01 = CR08
# I02 = CR09
# I03 = CR10

class Frontend(roles.FrontendRole):
    def __init__(self, use_terrain_corrected=True, ignore_crefl=False, **kwargs):
        super(Frontend, self).__init__(**kwargs)
        self.use_terrain_corrected = use_terrain_corrected
        # Ignore existing CREFL files and just create from SDRs
        self.ignore_crefl = ignore_crefl
        # FUTURE: Remove these files or give the option to remove them when an error is encountered
        self.crefl_files_created = []
        self.secondary_product_functions = {}

        # MODIS SDRs and CREFL files:
        hdf4_files = self.find_files_with_extensions([".hdf"], warn_invalid=False)
        # VIIRS SDR files:
        hdf5_files = self.find_files_with_extensions([".h5"], warn_invalid=False)

        self.modis_refl_fts = (modis_guidebook.FT_1000M, modis_guidebook.FT_500M, modis_guidebook.FT_250M)
        self.viirs_refl_fts = (
            viirs_guidebook.FILE_TYPE_I01, viirs_guidebook.FILE_TYPE_I02, viirs_guidebook.FILE_TYPE_I03,
            viirs_guidebook.FILE_TYPE_M05, viirs_guidebook.FILE_TYPE_M07, viirs_guidebook.FILE_TYPE_M03,
            viirs_guidebook.FILE_TYPE_M04, viirs_guidebook.FILE_TYPE_M08, viirs_guidebook.FILE_TYPE_M10,
            viirs_guidebook.FILE_TYPE_M11
        )
        self.crefl_fts = (FT_CREFL_M, FT_CREFL_I, FT_CREFL_1000M, FT_CREFL_500M, FT_CREFL_250M)

        # Get any CREFL files we know about
        self.file_readers = {}
        # HDF4
        self._init_crefl_file_readers()
        self.file_readers[FT_GEO] = modis_guidebook.MultiFileReader(modis_guidebook.FILE_TYPES[FT_GEO])
        # If we don't have any of the files for CREFL then we will need to create them from the following file types
        for ft in self.modis_refl_fts:
            self.file_readers[ft] = modis_guidebook.MultiFileReader(modis_guidebook.FILE_TYPES[ft])

        # HDF5 files
        self.file_readers[FT_GITCO] = viirs_io.VIIRSSDRMultiReader(viirs_guidebook.FILE_TYPES[FT_GITCO])
        self.file_readers[FT_GIMGO] = viirs_io.VIIRSSDRMultiReader(viirs_guidebook.FILE_TYPES[FT_GIMGO])
        self.file_readers[FT_GMTCO] = viirs_io.VIIRSSDRMultiReader(viirs_guidebook.FILE_TYPES[FT_GMTCO])
        self.file_readers[FT_GMODO] = viirs_io.VIIRSSDRMultiReader(viirs_guidebook.FILE_TYPES[FT_GMODO])
        # If we don't have any of the files for CREFL then we will need to create them from the following file types
        for ft in self.viirs_refl_fts:
            self.file_readers[ft] = viirs_io.VIIRSSDRMultiReader(viirs_guidebook.FILE_TYPES[ft])

        have_crefl, have_modis = self.analyze_hdf4_files(hdf4_files)
        if have_crefl:
            # Check for VIIRS
            have_m_crefl = FT_CREFL_M in self.file_readers
            have_i_crefl = FT_CREFL_I in self.file_readers
            if have_m_crefl or have_i_crefl:
                self.analyze_hdf5_files(hdf5_files, geo_only=True)
                if self.use_terrain_corrected:
                    have_m_nav = FT_GMTCO in self.file_readers
                    have_i_nav = FT_GITCO in self.file_readers
                else:
                    have_m_nav = FT_GMODO in self.file_readers
                    have_i_nav = FT_GIMGO in self.file_readers
                if (have_m_crefl and not have_m_nav) or (have_i_crefl and not have_i_nav):
                    LOG.error("Found VIIRS CREFL files, but not the associated geolocation files")
                    raise RuntimeError("Found VIIRS CREFL files, but not the associated geolocation files")
            elif FT_GEO not in self.file_readers:
                # Check for MODIS
                LOG.error("Found MODIS CREFL files, but not the associated geolocation files")
                raise RuntimeError("Found MODIS CREFL files, but not the associated geolocation files")
        elif have_modis:
            LOG.info("Could not find any existing crefl output will use MODIS SDRs to create some")
            self.create_modis_crefl_files()
        else:
            have_viirs = self.analyze_hdf5_files(hdf5_files)
            if have_viirs:
                    LOG.info("Could not find any existing crefl output will use VIIRS SDRs to create some")
                    self.create_viirs_crefl_files()
            else:
                LOG.error("Could not find any existing CREFL files, MODIS SDRs, or VIIRS SDRs")
                raise RuntimeError("Could not find any existing CREFL files, MODIS SDRs, or VIIRS SDRs")

        # We have CREFL files now so let's get rid of the SDRs
        for ft in self.modis_refl_fts + self.viirs_refl_fts:
            del self.file_readers[ft]
        # Get rid of empty crefl file readers
        for ft in list(self.crefl_fts) + [FT_GEO, FT_GIMGO, FT_GITCO, FT_GMTCO, FT_GMODO]:
            if len(self.file_readers[ft]) == 0:
                del self.file_readers[ft]

        self.available_file_types = self.file_readers.keys()

    def _init_crefl_file_readers(self):
        self.file_readers[FT_CREFL_M] = MultiFileReader(FILE_TYPES[FT_CREFL_M], single_class=VIIRSFileReader)
        self.file_readers[FT_CREFL_I] = MultiFileReader(FILE_TYPES[FT_CREFL_I], single_class=VIIRSFileReader)
        self.file_readers[FT_CREFL_1000M] = MultiFileReader(FILE_TYPES[FT_CREFL_1000M], single_class=MODISFileReader)
        self.file_readers[FT_CREFL_500M] = MultiFileReader(FILE_TYPES[FT_CREFL_500M], single_class=MODISFileReader)
        self.file_readers[FT_CREFL_250M] = MultiFileReader(FILE_TYPES[FT_CREFL_250M], single_class=MODISFileReader)

    def _clear_crefl_file_readers(self):
        for ft in self.crefl_fts:
            del self.file_readers[ft]

    def analyze_hdf4_files(self, hdf4_files):
        have_crefl = False
        have_modis = False
        for fp in hdf4_files:
            LOG.debug("Analyzing %s", fp)
            fn = os.path.basename(fp)
            if fn.startswith("CREFL") and not self.ignore_crefl:
                # VIIRS CREFL
                if fn[5] == "I":
                    self.file_readers[FT_CREFL_I].add_file(fp)
                    have_crefl = True
                elif fn[5] == "M":
                    self.file_readers[FT_CREFL_M].add_file(fp)
                    have_crefl = True
                else:
                    LOG.warning("Unknown CREFL file: %s", fp)
                    continue
            elif fn[:3] in ["a1.", "t1.", "MYD", "MOD"]:
                try:
                    hdf4_obj = modis_guidebook.HDFEOSReader(fp)
                    if hdf4_obj.file_type == FT_CREFL_1000M:
                        self.file_readers[FT_CREFL_1000M].add_file(hdf4_obj)
                        have_crefl = True
                    elif hdf4_obj.file_type == FT_CREFL_500M:
                        self.file_readers[FT_CREFL_500M].add_file(hdf4_obj)
                        have_crefl = True
                    elif hdf4_obj.file_type == FT_CREFL_250M:
                        self.file_readers[FT_CREFL_250M].add_file(hdf4_obj)
                        have_crefl = True
                    elif hdf4_obj.file_type == FT_GEO:
                        self.file_readers[FT_GEO].add_file(hdf4_obj)
                    elif hdf4_obj.file_type in self.file_readers:
                        self.file_readers[hdf4_obj.file_type].add_file(hdf4_obj)
                        have_modis = True
                    else:
                        LOG.warning("Unnecessary MODIS file found: %s", fp)
                except StandardError:
                    LOG.warning("Could not parse modis HDF4 file: %s", fp)
                    continue
            else:
                LOG.warning("Unknown HDF4 file: %s", fp)
        self.file_readers[FT_CREFL_1000M].finalize_files()
        self.file_readers[FT_CREFL_500M].finalize_files()
        self.file_readers[FT_CREFL_250M].finalize_files()
        self.file_readers[FT_GEO].finalize_files()
        self.file_readers[FT_CREFL_M].finalize_files()
        self.file_readers[FT_CREFL_I].finalize_files()

        return have_crefl, have_modis

    def analyze_hdf5_files(self, hdf5_files, geo_only=False):
        have_viirs = False
        nav_file_types = [FT_GITCO, FT_GMTCO] if self.use_terrain_corrected else [FT_GIMGO, FT_GMODO]
        file_types = nav_file_types
        if not geo_only:
            file_types += self.viirs_refl_fts
        for fp in hdf5_files:
            LOG.debug("Analyzing %s", fp)
            h = viirs_io.HDF5Reader(fp)
            for ft in file_types:
                data_path = viirs_guidebook.FILE_TYPES[ft][viirs_guidebook.K_DATA_PATH]
                if data_path in h:
                    self.file_readers[ft].add_file(h)
                    have_viirs = True
                    break
            else:
                LOG.debug("Unnecessary hdf5 file: %s", fp)
        for ft in file_types:
            self.file_readers[ft].finalize_files()
        return have_viirs

    def create_modis_crefl_files(self):
        from polar2grid.crefl.crefl_wrapper import run_modis_crefl
        try:
            kwargs = {"keep_intermediate": self.keep_intermediate}
            if modis_guidebook.FT_1000M in self.file_readers and len(self.file_readers[modis_guidebook.FT_1000M]):
                km_files = self.file_readers[modis_guidebook.FT_1000M].filepaths
            else:
                LOG.error("Can not create MODIS crefl files with out 1000m files")
                raise RuntimeError("Can not create MODIS crefl files with out 1000m files")

            # Use the MODIS Frontend to determine if we have enough day time data
            LOG.debug("Loading the MODIS frontend to check for daytime data")
            f = modis_module.Frontend(search_paths=self.file_readers[FT_GEO].filepaths)
            scene = f.create_scene(products=[modis_module.PRODUCT_SZA])
            day_percentage = f._get_day_percentage(scene[modis_module.PRODUCT_SZA])
            if day_percentage < 10:
                LOG.error("Will not create modis crefl products because there is less than 10%% of day data")
                raise RuntimeError("Will not create modis crefl products because there is less than 10%% of day data")

            if modis_guidebook.FT_500M in self.file_readers and len(self.file_readers[modis_guidebook.FT_500M]):
                kwargs["hkm_files"] = self.file_readers[modis_guidebook.FT_500M].filepaths
                LOG.debug("Adding HKM files to crefl call: %s", ",".join(kwargs["hkm_files"]))
            if modis_guidebook.FT_250M in self.file_readers and len(self.file_readers[modis_guidebook.FT_250M]):
                kwargs["qkm_files"] = self.file_readers[modis_guidebook.FT_250M].filepaths
                LOG.debug("Adding QKM files to crefl call: %s", ",".join(kwargs["qkm_files"]))

            files_created = run_modis_crefl(km_files, **kwargs)
            self.crefl_files_created.extend(files_created)

            # we already tried to load some hdf4 files, so we need to clear the crefl ones
            self._clear_crefl_file_readers()
            self._init_crefl_file_readers()
            have_crefl, _ = self.analyze_hdf4_files(files_created)
            if not have_crefl:
                raise RuntimeError("crefl completed successfully, but didn't give us any recognizable crefl files")
        except StandardError:
            LOG.error("Could not create modis crefl files from SDRs")
            raise

    def create_viirs_crefl_files(self):
        from polar2grid.crefl.crefl_wrapper import run_cviirs
        kw_names = ["i01_files", "i02_files", "i03_files", "m05_files",
                    "m07_files", "m03_files", "m04_files", "m08_files",
                    "m10_files", "m11_files"]
        try:
            ft = FT_GMTCO if self.use_terrain_corrected else FT_GMODO
            if ft not in self.file_readers:
                LOG.error("M-band geolocation is required for crefl processing")
                raise RuntimeError("M-band geolocation is required for crefl processing")
            geo_files = self.file_readers[ft].filepaths

            # Use the VIIRS Frontend to determine if we have enough day time data
            LOG.debug("Loading the VIIRS frontend to check for daytime data")
            f = viirs_module.Frontend(search_paths=geo_files, use_terrain_corrected=self.use_terrain_corrected)
            scene = f.create_scene(products=[viirs_module.PRODUCT_M_SZA])
            day_percentage = f._get_day_percentage(scene[viirs_module.PRODUCT_M_SZA])
            if day_percentage < 10:
                LOG.error("Will not create viirs crefl products because there is less than 10%% of day data")
                raise RuntimeError("Will not create viirs crefl products because there is less than 10%% of day data")
            LOG.debug("Will attempt crefl creation, found %f%% day data", day_percentage)

            kwargs = {"keep_intermediate": self.keep_intermediate}
            for ft, kw_name in zip(self.viirs_refl_fts, kw_names):
                if ft in self.file_readers:
                    kwargs[kw_name] = self.file_readers[ft].filepaths
            files_created = run_cviirs(geo_files, **kwargs)
            self.crefl_files_created.extend(files_created)

            # we already tried to load some hdf4 files, so we need to clear the crefl ones
            self._clear_crefl_file_readers()
            self._init_crefl_file_readers()
            have_crefl, _ = self.analyze_hdf4_files(files_created)
            if not have_crefl:
                raise RuntimeError("cviirs completed successfully, but didn't give us any recognizable crefl files")
        except StandardError:
            LOG.error("Could not create crefl files from SDRs")
            raise

    @property
    def begin_time(self):
        for ft in self.crefl_fts:
            if ft in self.file_readers:
                return self.file_readers[ft].begin_time

    @property
    def end_time(self):
        for ft in self.crefl_fts:
            if ft in self.file_readers:
                return self.file_readers[ft].end_time

    @property
    def all_product_names(self):
        return PRODUCTS.keys()

    @property
    def available_product_names(self):
        return [product_name for product_name, product_def in PRODUCTS.items()
                if product_def.file_type in self.file_readers]

    @property
    def default_products(self):
        available = self.available_product_names
        return [x for x in TRUE_COLOR_PRODUCTS if x in available]

    def create_swath_definition(self, lon_product, lat_product):
        index = None
        if lon_product in [viirs_module.PRODUCT_I_LON, viirs_module.PRODUCT_M_LON]:
            index = 0 if self.use_terrain_corrected else 1
        product_def = PRODUCTS[lon_product["product_name"]]
        file_type = product_def.get_file_type(self.available_file_types, index=index)
        lon_file_reader = self.file_readers[file_type]
        product_def = PRODUCTS[lat_product["product_name"]]
        file_type = product_def.get_file_type(self.available_file_types, index=index)
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

    def _get_file_type(self, product_name):
        ft = PRODUCTS[product_name].file_type
        if not isinstance(ft, str):
            return ft[0 if self.use_terrain_corrected else 1]
        return ft

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
            shape = file_reader.write_var_to_flat_binary(file_key, filename)
            data_type = file_reader.get_data_type(file_key)
            fill_value = file_reader.get_fill_value(file_key)
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
            source_filenames=file_reader.filepaths, data_kind=product_def.data_kind, rows_per_scan=rows_per_scan,
            **product_def.info
        )
        return one_swath

    def create_secondary_swath_object(self, product_name, swath_definition, filename, data_type, products_created):
        pass

    def create_scene(self, products=None, **kwargs):
        LOG.debug("Loading scene data...")
        # If the user didn't provide the products they want, figure out which ones we can create
        if products is None:
            LOG.debug("No products specified to frontend, will try to load logical defaults products")
            products = self.default_products

        # Do we actually have all of the files needed to create the requested products?
        products = self.loadable_products(products)

        # Needs to be ordered (least-depended product -> most-depended product)
        products_needed = PRODUCTS.dependency_ordered_products(products)
        geo_pairs_needed = PRODUCTS.geo_pairs_for_products(products_needed)
        # both lists below include raw products that need extra processing/masking
        raw_products_needed = (p for p in products_needed if PRODUCTS.is_raw(p, geo_is_raw=False))
        secondary_products_needed = [p for p in products_needed if PRODUCTS.needs_processing(p)]
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
                swath_def = swath_definitions[PRODUCTS[product_name].geo_pair_name]
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
            swath_def = swath_definitions[PRODUCTS[product_name].geo_pair_name]

            try:
                LOG.info("Creating secondary product '%s'", product_name)
                one_swath = product_func(self, product_name, swath_def, products_created)
            except StandardError:
                LOG.error("Could not create product (unexpected error): '%s'", product_name)
                LOG.debug("Could not create product (unexpected error): '%s'", product_name, exc_info=True)
                if self.exit_on_error:
                    raise
                continue

            products_created[product_name] = one_swath
            if product_name in products:
                # the user wants this product
                scene[product_name] = one_swath

        return scene


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    from polar2grid.core.script_utils import ExtendAction, ExtendConstAction
    # Set defaults for other components that may be used in polar2grid processing
    # FIXME: These should probably be changed depending on what instrument is being dealt with...currently not possible in polar2grid
    parser.set_defaults(fornav_D=40, fornav_d=1)

    # Use the append_const action to handle adding products to the list
    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                       help="List available frontend products and exit")
    group.add_argument("--no-tc", dest="use_terrain_corrected", action="store_false",
                       help="Don't use terrain-corrected navigation (VIIRS products only)")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    group.add_argument("-p", "--products", dest="products", nargs="+", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    group.add_argument("--true-color", dest="products", const=TRUE_COLOR_PRODUCTS, action=ExtendConstAction,
                       help="Attempt to extract the products that could be used to create true color images")
    group.add_argument("--false-color", dest="products", const=FALSE_COLOR_PRODUCTS, action=ExtendConstAction,
                       help="Attempt to extract the products that could be used to create false color images")
    group.add_argument("--no-compositors", dest="no_compositors", action="store_true",
                       help="Force no compositors to be used during glue script execution")
    return ["Frontend Initialization", "Frontend Swath Extraction"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    parser = create_basic_parser(description="Extract VIIRS and MODIS CREFL swath data into binary files")
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

if __name__ == "__main__":
    sys.exit(main())

