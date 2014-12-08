#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
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
"""Read one or more contiguous in-order HDF4 VIIRS or MODIS corrected reflectance product
granules and aggregate them into one swath per band.
Write out Swath binary files used by other polar2grid components.

The crefl frontend accepts output from MODIS and VIIRS corrected reflectance processing. If provided with SDR files
it will attempt to call the proper programs to convert the files. The required commands that must be available are:

 - h5SDS_transfer_rename
 - cviirs (for VIIRS corrected reflectance)
 - crefl.1.7.1 (for MODIS corrected reflectance)

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2014
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

from polar2grid.core import roles
from polar2grid.core.constants import *
from polar2grid.core.fbf import file_appender,check_stem
# from polar2grid.viirs import viirs_guidebook
from polar2grid.modis.modis_geo_interp_250 import interpolate_geolocation
from pyhdf import SD
import h5py
from . import guidebook
import numpy

from polar2grid.core.frontend_utils import ProductDict, GeoPairDict
from polar2grid.core import meta
from polar2grid.modis.modis_to_swath import PRODUCT_1000M_LON, PRODUCT_1000M_LAT,\
    PRODUCT_500M_LON, PRODUCT_500M_LAT,\
    PRODUCT_250M_LON, PRODUCT_250M_LAT
import polar2grid.modis.modis_to_swath as modis_module
import polar2grid.modis.modis_guidebook as modis_guidebook
import polar2grid.viirs.swath as viirs_module
import polar2grid.viirs.io as viirs_io
import polar2grid.viirs.guidebook as viirs_guidebook

import os
import sys
import logging
from datetime import datetime, timedelta
from pprint import pprint

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

class FileInfo(object):
    def __init__(self, var_name, scale_attr_name="scale_factor", offset_attr_name="add_offset",
                 fill_attr_name="_FillValue", data_type=numpy.float32):
        self.var_name = var_name
        self.data_type = data_type
        self.scale_attr_name = scale_attr_name
        self.offset_attr_name = offset_attr_name
        self.fill_attr_name = fill_attr_name

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
    def get_swath_data(self, item, fill=None):
        if fill is None:
            fill = self.get_fill_value(item)

        var_info = self.file_type_info[item]
        var_name = var_info.var_name
        scale_factor_attr_name = var_info.scale_attr_name
        scale_offset_attr_name = var_info.offset_attr_name
        fill_attr_name = var_info.fill_attr_name

        # Get the band data from the file
        variable = self[var_name]
        data = variable.get()

        if fill_attr_name:
            input_fill_value = self[var_name + "." + fill_attr_name]
            LOG.debug("Using fill value attribute '%s' (%s) to filter bad data", fill_attr_name, str(input_fill_value))
            input_fill_value = 16000
            LOG.debug("Ignoring fill value and using '%s' instead", str(input_fill_value))
            fill_mask = data > input_fill_value
        else:
            fill_mask = numpy.zeros_like(data).astype(numpy.bool)

        if isinstance(scale_factor_attr_name, float):
            scale_factor = scale_factor_attr_name
        elif scale_factor_attr_name is not None:
            scale_factor = self[var_name + "." + scale_factor_attr_name]

        if isinstance(scale_offset_attr_name, float):
            scale_offset = scale_offset_attr_name
        elif scale_offset_attr_name is not None:
            scale_offset = self[var_name + "." + scale_offset_attr_name]

        # Scale the data
        if scale_factor_attr_name is not None and scale_offset_attr_name is not None:
            data = data * scale_factor + scale_offset
        data[fill_mask] = fill

        return data


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
PRODUCT_MCR01_250M = "modis_crefl01_500m"
PRODUCT_MCR02_250M = "modis_crefl02_500m"
PRODUCT_MCR03_250M = "modis_crefl03_500m"
PRODUCT_MCR04_250M = "modis_crefl04_500m"

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
PRODUCTS[viirs_module.PRODUCT_I_LON] = viirs_module.PRODUCTS[viirs_module.PRODUCT_I_LON]
PRODUCTS[viirs_module.PRODUCT_I_LAT] = viirs_module.PRODUCTS[viirs_module.PRODUCT_I_LAT]
PRODUCTS[viirs_module.PRODUCT_M_LON] = viirs_module.PRODUCTS[viirs_module.PRODUCT_M_LON]
PRODUCTS[viirs_module.PRODUCT_M_LAT] = viirs_module.PRODUCTS[viirs_module.PRODUCT_M_LAT]
PRODUCTS.add_product(PRODUCT_VCR01, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL01)
PRODUCTS.add_product(PRODUCT_VCR02, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL02)
PRODUCTS.add_product(PRODUCT_VCR03, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL03)
PRODUCTS.add_product(PRODUCT_VCR04, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL04)
PRODUCTS.add_product(PRODUCT_VCR05, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL05)
PRODUCTS.add_product(PRODUCT_VCR06, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL06)
PRODUCTS.add_product(PRODUCT_VCR07, PAIR_MNAV, "corrected_reflectance", FT_CREFL_M, K_CREFL07)
PRODUCTS.add_product(PRODUCT_VCR08, PAIR_INAV, "corrected_reflectance", FT_CREFL_I, K_CREFL08)
PRODUCTS.add_product(PRODUCT_VCR09, PAIR_INAV, "corrected_reflectance", FT_CREFL_I, K_CREFL09)
PRODUCTS.add_product(PRODUCT_VCR10, PAIR_INAV, "corrected_reflectance", FT_CREFL_I, K_CREFL10)

PRODUCTS[modis_module.PRODUCT_1000M_LON] = modis_module.PRODUCTS[modis_module.PRODUCT_1000M_LON]
PRODUCTS[modis_module.PRODUCT_1000M_LAT] = modis_module.PRODUCTS[modis_module.PRODUCT_1000M_LAT]
PRODUCTS[modis_module.PRODUCT_500M_LON] = modis_module.PRODUCTS[modis_module.PRODUCT_500M_LON]
PRODUCTS[modis_module.PRODUCT_500M_LAT] = modis_module.PRODUCTS[modis_module.PRODUCT_500M_LAT]
PRODUCTS[modis_module.PRODUCT_250M_LON] = modis_module.PRODUCTS[modis_module.PRODUCT_250M_LON]
PRODUCTS[modis_module.PRODUCT_250M_LAT] = modis_module.PRODUCTS[modis_module.PRODUCT_250M_LAT]
PRODUCTS.add_product(PRODUCT_MCR01_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL01)
PRODUCTS.add_product(PRODUCT_MCR02_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL02)
PRODUCTS.add_product(PRODUCT_MCR03_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL03)
PRODUCTS.add_product(PRODUCT_MCR04_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL04)
PRODUCTS.add_product(PRODUCT_MCR05_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL05)
PRODUCTS.add_product(PRODUCT_MCR06_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL06)
PRODUCTS.add_product(PRODUCT_MCR07_1000M, PAIR_1000M, "corrected_reflectance", FT_CREFL_1000M, K_CREFL07)
PRODUCTS.add_product(PRODUCT_MCR01_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL01)
PRODUCTS.add_product(PRODUCT_MCR02_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL02)
PRODUCTS.add_product(PRODUCT_MCR03_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL03)
PRODUCTS.add_product(PRODUCT_MCR04_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL04)
PRODUCTS.add_product(PRODUCT_MCR05_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL05)
PRODUCTS.add_product(PRODUCT_MCR06_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL06)
PRODUCTS.add_product(PRODUCT_MCR07_500M, PAIR_500M, "corrected_reflectance", FT_CREFL_500M, K_CREFL07)
PRODUCTS.add_product(PRODUCT_MCR01_250M, PAIR_250M, "corrected_reflectance", FT_CREFL_250M, K_CREFL01)
PRODUCTS.add_product(PRODUCT_MCR02_250M, PAIR_250M, "corrected_reflectance", FT_CREFL_250M, K_CREFL02)
PRODUCTS.add_product(PRODUCT_MCR03_250M, PAIR_250M, "corrected_reflectance", FT_CREFL_250M, K_CREFL03)
PRODUCTS.add_product(PRODUCT_MCR04_250M, PAIR_250M, "corrected_reflectance", FT_CREFL_250M, K_CREFL04)

# R, G, B, HighRes Red
VIIRS_TRUE_COLOR_PRODUCTS = [PRODUCT_VCR01, PRODUCT_VCR04, PRODUCT_VCR03, PRODUCT_VCR08]
MODIS_TRUE_COLOR_PRODUCTS = [PRODUCT_MCR01_1000M, PRODUCT_MCR04_1000M, PRODUCT_MCR03_1000M, PRODUCT_MCR01_250M]
TRUE_COLOR_PRODUCTS = VIIRS_TRUE_COLOR_PRODUCTS + MODIS_TRUE_COLOR_PRODUCTS


class Frontend(roles.FrontendRole):
    def __init__(self, use_terrain_corrected=True, ignore_crefl=False, **kwargs):
        super(Frontend, self).__init__(**kwargs)
        self.use_terrain_corrected = use_terrain_corrected
        # Ignore existing CREFL files and just create from SDRs
        self.ignore_crefl = ignore_crefl
        self.secondary_product_functions = {}

        # MODIS SDRs and CREFL files:
        hdf4_files = self.find_files_with_extensions([".hdf"])
        # VIIRS SDR files:
        hdf5_files = self.find_files_with_extensions([".h5"])

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
        self.file_readers[FT_CREFL_M] = MultiFileReader(FILE_TYPES[FT_CREFL_M], single_class=VIIRSFileReader)
        self.file_readers[FT_CREFL_I] = MultiFileReader(FILE_TYPES[FT_CREFL_I], single_class=VIIRSFileReader)
        self.file_readers[FT_CREFL_1000M] = MultiFileReader(FILE_TYPES[FT_CREFL_1000M], single_class=MODISFileReader)
        self.file_readers[FT_CREFL_500M] = MultiFileReader(FILE_TYPES[FT_CREFL_500M], single_class=MODISFileReader)
        self.file_readers[FT_CREFL_250M] = MultiFileReader(FILE_TYPES[FT_CREFL_250M], single_class=MODISFileReader)
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
        if not have_crefl:
            if have_modis:
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

            hdf4_files = self.find_files_with_extensions([".hdf"])  # FIXME: needs to use new directory
            have_crefl, have_modis = self.analyze_hdf4_files(hdf4_files)
            if not have_crefl:
                LOG.error("Could not create crefl files from SDRs")
                raise RuntimeError("Could not create crefl files from SDRs")
        elif FT_CREFL_M in self.file_readers or FT_CREFL_I in self.file_readers:
            # we have crefl files, but we will need the VIIRS SDR Navigation files
            have_viirs = self.analyze_hdf5_files(hdf5_files, geo_only=True)
            if not have_viirs:
                LOG.error("Found VIIRS CREFL files, but not the associated geolocation files")
                raise RuntimeError("Found VIIRS CREFL files, but not the associated geolocation files")

        # We have CREFL files now so let's get rid of the SDRs
        for ft in self.modis_refl_fts + self.viirs_refl_fts:
            del self.file_readers[ft]
        # Get rid of empty crefl file readers
        for ft in self.crefl_fts:
            if len(self.file_readers[ft]) == 0:
                del self.file_readers[ft]

        self.available_file_types = self.file_readers.keys()

    def analyze_hdf4_files(self, hdf4_files):
        have_crefl = False
        have_modis = False
        for fp in hdf4_files:
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
            elif fn.startswith("a1") or fn.startswith("t1"):
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
            h = viirs_io.HDF5Reader(fp)
            for ft in file_types:
                data_path = viirs_guidebook.FILE_TYPES[ft][viirs_guidebook.K_DATA_PATH]
                if data_path in h:
                    self.file_readers[ft].add_file(h)
                    have_viirs = True
                    break
            else:
                LOG.debug("Unnecessary hdf5 file: %s", fp)
        return have_viirs

    def create_modis_crefl_files(self):
        # TODO: Delete the intermediate CREFL files if we created them after we've loaded the data
        pass

    def create_viirs_crefl_files(self):
        # TODO: Delete the intermediate CREFL files if we created them after we've loaded the data
        pass

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
        swath_definition = meta.SwathDefinition(
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

        LOG.info("Writing product '%s' data to binary file", product_name)
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

        one_swath = meta.SwathProduct(
            product_name=product_name, description=product_def.description, units=product_def.units,
            satellite=file_reader.satellite, instrument=file_reader.instrument,
            begin_time=file_reader.begin_time, end_time=file_reader.end_time,
            swath_definition=swath_definition, fill_value=fill_value,
            swath_rows=shape[0], swath_columns=shape[1], data_type=data_type, swath_data=filename,
            source_filenames=file_reader.filepaths, data_kind=product_def.data_kind, rows_per_scan=rows_per_scan
        )
        return one_swath

    def create_secondary_swath_object(self, product_name, swath_definition, filename, data_type, products_created):
        pass

    def create_scene(self, products=None, **kwargs):
        LOG.info("Loading scene data...")
        # If the user didn't provide the products they want, figure out which ones we can create
        if products is None:
            LOG.info("No products specified to frontend, will try to load logical defaults products")
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
        scene = meta.SwathScene()
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
    from polar2grid.core.script_utils import ExtendAction
    # Set defaults for other components that may be used in polar2grid processing
    # FIXME: These should probably be changed depending on what instrument is being dealt with...currently not possible in polar2grid
    parser.set_defaults(fornav_D=40, fornav_d=2)

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

