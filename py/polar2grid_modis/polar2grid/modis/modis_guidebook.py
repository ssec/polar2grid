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
# Written by David Hoese    November 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Provide information about MODIS product files for a variety of uses.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

from polar2grid.core.frontend_utils import BaseFileReader, BaseMultiFileReader
from polar2grid.modis.modis_geo_interp_250 import interpolate_geolocation_cartesian

import os
import logging

from datetime import datetime
from pyhdf import SD
import numpy

LOG = logging.getLogger(__name__)

# file keys
K_LONGITUDE = "longitude_var"
K_LATITUDE = "latitude_var"
K_LONGITUDE_500 = "longitude500_var"
K_LATITUDE_500 = "latitude500_var"
K_LONGITUDE_250 = "longitude250_var"
K_LATITUDE_250 = "latitude250_var"
K_VIS01 = "vis01_var"
K_VIS02 = "vis02_var"
K_VIS03 = "vis03_var"
K_VIS04 = "vis04_var"
K_VIS05 = "vis05_var"
K_VIS06 = "vis06_var"
K_VIS07 = "vis07_var"
K_VIS26 = "vis26_var"
K_IR20 = "ir20_var"
K_IR21 = "ir21_var"
K_IR22 = "ir22_var"
K_IR23 = "ir23_var"
K_IR24 = "ir24_var"
K_IR25 = "ir25_var"
K_IR27 = "ir27_var"
K_IR28 = "ir28_var"
K_IR29 = "ir29_var"
K_IR30 = "ir30_var"
K_IR31 = "ir31_var"
K_IR32 = "ir32_var"
K_IR33 = "ir33_var"
K_IR34 = "ir34_var"
K_IR35 = "ir35_var"
K_IR36 = "ir36_var"
K_CMASK = "cloud_mask_var"
K_LSMASK = "land_sea_mask_var"
K_SIMASK = "snow_ice_mask_var"
K_SST = "sst_var"
K_LST = "lst_var"
K_SLST = "slst_var"
K_NDVI = "ndvi_var"
K_SZA = "sza_var"
K_SenZA = "senza_var"
K_IST = "ist_var"
K_INV = "inv_var"
K_IND = "ind_var"
K_ICECON = "icecon_var"
K_CTT = "ctt_var"
K_TPW = "tpw_var"


def mask_helper(data, fill_value):
    if numpy.isnan(fill_value):
        return numpy.isnan(data)
    return data == fill_value


class HDFEOSMetadata(dict):
    """Basic Metadata parser for MODIS HDF-EOS files.

    This parser could probably be done better, but no one seems to know specifics about the Metadata format.
    """
    def __init__(self, metadata_str):
        metadata_lines = [x.strip() for x in metadata_str.split("\n") if x]

        # Check that we have a fully constructed metadata dictionary
        assert(metadata_lines[0].split("=")[0].strip() == "GROUP")
        group_type_key, group_type = metadata_lines[1].split("=")
        assert(group_type_key.strip() == "GROUPTYPE" and group_type.strip() == "MASTERGROUP")
        assert(metadata_lines[-1] == "END")

        # We only want the stuff inside
        # Add special value to END keyword because why would consistency matter
        metadata_key_values = [(line.split("=")[0].strip(), line.split("=")[1].strip()) for line in metadata_lines[:-1]] + [("END", "END")]
        self._recurse_metadata_lines(metadata_key_values)

    def _recurse_metadata_lines(self, key_values, current_idx=0, current_prefix=""):
        current_key, current_val = key_values[current_idx]
        # print "Info: ", current_prefix, current_idx, current_key, current_val
        if current_idx >= len(key_values):
            return current_idx + 1

        if current_key == "OBJECT":
            this_prefix = "/%s" % (current_val,)
            current_prefix += this_prefix
            current_object_val = None
            current_object_num_vals = None
            current_idx += 1
            current_key, current_val = key_values[current_idx]
            # we are starting an object
            while current_key != "END_OBJECT":
                if current_key == "NUM_VAL":
                    current_object_num_vals = int(current_val)
                elif current_key == "VALUE":
                    current_object_val = current_val
                elif current_key == "CLASS":
                    # not sure what this is used for or what it means
                    pass
                elif current_key == "OBJECT" or current_key == "GROUP":
                    # go process this object or group which could be recursive
                    # since we are a container object we don't have any specific value to add so return to parent
                    while current_key != "END_OBJECT":
                        current_idx = self._recurse_metadata_lines(key_values, current_idx=current_idx, current_prefix=current_prefix)
                        current_key, current_val = key_values[current_idx]
                    LOG.debug("End of container object: %s", current_prefix)
                    return current_idx + 1
                else:
                    LOG.warning("Unknown key/value: %s = %s", current_key, current_val)

                current_idx += 1
                current_key, current_val = key_values[current_idx]

            if current_object_num_vals != 1:
                current_object_val = tuple(current_object_val[1:-1].split(","))
            else:
                # remove quotation marks
                current_object_val = current_object_val.replace("\"", "")
            LOG.debug("Adding metadata: %s = %r", current_prefix, current_object_val)
            self[current_prefix] = current_object_val
            return current_idx+1
        elif current_key == "GROUP":
            this_prefix = "/%s" % (current_val,)
            current_prefix += this_prefix
            current_idx += 1
            current_key, current_val = key_values[current_idx]
            # process everything in this group
            while current_key != "END_GROUP":
                current_idx = self._recurse_metadata_lines(key_values, current_idx=current_idx, current_prefix=current_prefix)
                current_key, current_val = key_values[current_idx]
            # we are done with the group and the parent should keep moving on
            LOG.debug("End of group: %s", current_prefix)
            return current_idx + 1
        elif current_key == "GROUPTYPE":
            # passive group thing, just keep moving on
            return current_idx + 1
        elif current_key == "CLASS":
            # we don't know what to do with this
            return current_idx + 1
        else:
            raise RuntimeError("Could not properly parse HDF-EOS Metadata")

        # Return the next index to look at
        return current_idx + 1


class HDFReader(object):
    """Abstract HDF4 file object reader.

    Attributes can be retrieved via "var_name.attr_name" or ".attr_name" for global attributes.
    """
    def __init__(self, filename):
        self.filename = os.path.basename(filename)
        self.filepath = os.path.realpath(filename)
        self._hdf_handle = SD.SD(self.filepath, SD.SDC.READ)
        # HDF4 files are fairly simple so no need to get all of the variables before

    def __contains__(self, item):
        """Does this file contain the specified variable or attribute.
        """
        try:
            _ = self[item]
            return True
        except KeyError:
            return False

    def __getitem__(self, item):
        # work around for attributes with periods in the name (WTF)
        item = item.replace("\.", "\\")
        var_name, attr_name = item.split(".") if "." in item else (item, None)
        if var_name:
            try:
                var_name = var_name.replace("\\", ".")
                var_obj = self._hdf_handle.select(var_name)
            except SD.HDF4Error:
                raise KeyError("'%s' not found in HDF4 file '%s'" % (item, self.filepath))
        else:
            # global attribute access
            var_obj = self._hdf_handle

        if attr_name:
            try:
                attr_name = attr_name.replace("\\", ".")
                attr_obj = var_obj.attributes()[attr_name]
                return attr_obj
            except KeyError:
                raise KeyError("'%s' not found in HDF4 file '%s'" % (item, self.filepath))

        return var_obj

FT_MOD03 = FT_GEO = "file_type_geo"
FT_MOD021KM = FT_1000M = "file_type_1000m"
FT_MOD02HKM = FT_500M = "file_type_500m"
FT_MOD02QKM = FT_250M = "file_type_250m"
FT_MOD06 = "file_type_mod06"
FT_MOD06CT = "file_type_mod06ct"  # Special IMAPP subset of the MOD06 file
FT_MOD07 = "file_type_mod07"
FT_MOD28 = "file_type_mod28"
FT_MOD35 = "file_type_mod35"
# FT_MOD11 = "file_type_mod11"  # LST, but different than direct broadcast
# FT_MOD13A2 = "file_type_ndvi_1000m"
# FT_MOD13A1 = "file_type_ndvi_500m"
# FT_MOD13Q1 = "file_type_ndvi_250m"
# IMAPP Direct Broadcast Files
FT_MODLST = "file_type_modlst"
FT_MASK_BYTE1 = "file_type_mask_byte1"  # Special IMAPP DB product = Byte 1 of MOD35 and separated out
FT_IST = "file_type_ist"
FT_INV = "file_type_inversion"
FT_ICECON = "file_type_icecon"
FT_SNOW_MASK = "file_type_snow_mask"  # FIXME: What MOD product does this come from? And others of course
FT_NDVI_1000M = "file_type_ndvi_1000m"
FT_NDVI_500M = "file_type_ndvi_500m"
FT_NDVI_250M = "file_type_ndvi_250m"
FT_CREFL_1000M = "file_type_crefl_1000M"
FT_CREFL_500M = "file_type_crefl_500M"
FT_CREFL_250M = "file_type_crefl_250M"

class HDFEOSReader(HDFReader):
    """HDF-EOS file reader with special handling of 'MetaData' attributes.

    If the 'CoreMetadata.0' global attribute doesn't exist it will try to use the filename to get the
    needed information.
    """
    METADATA_ATTR_NAME = "CoreMetadata\.0"
    METADATA_SDATE = "/INVENTORYMETADATA/RANGEDATETIME/RANGEBEGINNINGDATE"
    METADATA_STIME = "/INVENTORYMETADATA/RANGEDATETIME/RANGEBEGINNINGTIME"
    METADATA_EDATE = "/INVENTORYMETADATA/RANGEDATETIME/RANGEENDINGDATE"
    METADATA_ETIME = "/INVENTORYMETADATA/RANGEDATETIME/RANGEENDINGTIME"
    METADATA_INSTRUMENT = "/INVENTORYMETADATA/ASSOCIATEDPLATFORMINSTRUMENTSENSOR/ASSOCIATEDPLATFORMINSTRUMENTSENSORCONTAINER/ASSOCIATEDINSTRUMENTSHORTNAME"
    METADATA_FILE_TYPE = "/INVENTORYMETADATA/COLLECTIONDESCRIPTIONCLASS/SHORTNAME"

    MODIS2FILETYPE = {
        # archive locations
        "021KM": FT_1000M,
        "02QKM": FT_250M,
        "02HKM": FT_500M,
        "03": FT_MOD03,
        "06_L2": FT_MOD06,
        "07_L2": FT_MOD07,
        "28_L2": FT_MOD28,
        "35_L2": FT_MOD35,
        # "11A1": FT_MOD11,
        # "13A2": FT_MOD13A2,
        # "13A1": FT_MOD13A1,
        # "13Q1": FT_MOD13Q1,
        # DB naming:
        "geo": FT_GEO,
        "1000m": FT_1000M,
        "500m": FT_500M,
        "250m": FT_250M,
        "icecon": FT_ICECON,
        "inversion": FT_INV,
        "ist": FT_IST,
        "mask_byte1": FT_MASK_BYTE1,
        "mod06ct": FT_MOD06CT,
        "mod07": FT_MOD07,
        "mod28": FT_MOD28,
        "mod35": FT_MOD35,
        "modlst": FT_MODLST,
        "ndvi.1000m": FT_NDVI_1000M,
        "ndvi.500m": FT_NDVI_500M,
        "ndvi.250m": FT_NDVI_250M,
        "snowmask": FT_SNOW_MASK,
        "crefl.1000m": FT_CREFL_1000M,
        "crefl.500m": FT_CREFL_500M,
        "crefl.250m": FT_CREFL_250M,
    }

    def __init__(self, filename):
        super(HDFEOSReader, self).__init__(filename)

        # handle meta data
        try:
            # Kept the begin and end time for the file
            fn = os.path.basename(filename)
            if fn[0] == "M":
                # archive filenaming:
                self.satellite = "aqua" if fn[:3] == "MYD" else "terra"
                self.instrument = "modis"
                parts = fn.split(".")
                self.begin_time = datetime.strptime(parts[1][1:] + parts[2], "%Y%j%H%M")
                # we don't know the end time from the filename
                self.end_time = self.begin_time
                self.file_type = self.MODIS2FILETYPE[parts[0][3:]]
            else:
                self.satellite = "aqua" if fn[0] == "a" else "terra"
                self.instrument = "modis"
                parts = fn.split(".")
                self.begin_time = datetime.strptime(parts[1] + parts[2], "%y%j%H%M")
                # we don't know the end time from the filename
                self.end_time = self.begin_time
                file_type_str = ".".join(parts[3:-1])
                self.file_type = self.MODIS2FILETYPE[file_type_str]

            # Get file type and satellite from the information in the file
            # try:
            #     metadata_str = self["." + self.METADATA_ATTR_NAME]
            #     self.meta = HDFEOSMetadata(metadata_str)
            #
            #     # begin_time_str = self.meta[self.METADATA_SDATE] + self.meta[self.METADATA_STIME]
            #     # end_time_str = self.meta[self.METADATA_EDATE] + self.meta[self.METADATA_ETIME]
            #     # self.begin_time = datetime.strptime(begin_time_str.split(".")[0], "%Y-%m-%d%H:%M:%S")
            #     # self.begin_time.replace(microsecond=int(begin_time_str.split(".")[1]))
            #     # self.end_time = datetime.strptime(end_time_str.split(".")[0], "%Y-%m-%d%H:%M:%S")
            #     # self.end_time.replace(microsecond=int(end_time_str.split(".")[1]))
            #     self.instrument = self.meta[self.METADATA_INSTRUMENT]
            #     file_type_str = self.meta[self.METADATA_FILE_TYPE]
            #     self.file_type = self.MODIS2FILETYPE[file_type_str[3:]]
            #     self.satellite = "aqua" if file_type_str.startswith("MYD") else "terra"
            # except KeyError:
            #     pass
        except StandardError:
            LOG.debug("Could not parse HDF-EOS file", exc_info=True)
            raise RuntimeError("Could not parse HDF-EOS file (see debug log for details)")


class FileReader(BaseFileReader):
    """Basic file wrapper that uses a `file_type_info` dictionary to map common key names to complex
    variable or attribute names and how to get them.
    """
    # Special values (not verified, but this is what I was told) because who would store special values in a file
    # these are used in reflectance band 1 and 2
    SATURATION_VALUE = 65533
    # if a value couldn't be aggregated from 250m/500m to 1km then we should clip those too
    CANT_AGGR_VALUE = 65528

    def __init__(self, filename_or_hdf_obj, file_type_info):
        if isinstance(filename_or_hdf_obj, (str, unicode)):
            filename_or_hdf_obj = HDFEOSReader(filename_or_hdf_obj)
        super(FileReader, self).__init__(filename_or_hdf_obj, file_type_info)

        self.instrument = self.file_handle.instrument.lower()
        self.satellite = self.file_handle.satellite.lower()
        self.begin_time = self.file_handle.begin_time
        self.end_time = self.file_handle.end_time
        # special hack for storing the 250m resolution navigation
        self.nav_interpolation = {"250": [None, None]}

    def __getitem__(self, item):
        known_item = self.file_type_info.get(item, item)
        if known_item is None:
            raise KeyError("Key 'None' was not found")

        if not isinstance(known_item, (str, unicode)):
            # Using FileVar class
            known_item = known_item.var_path
        LOG.debug("Loading %s from %s", known_item, self.filename)
        return self.file_handle[known_item]

    def get_swath_data(self, item, fill=None):
        """Retrieve the item asked for then set it to the specified data type, scale it, and mask it.
        """
        if fill is None:
            fill = self.get_fill_value(item)
        var_info = self.file_type_info.get(item)
        variable = self[var_info.var_name]
        data = variable.get()
        if var_info.index is not None:
            data = data[var_info.index]
        # before or after scaling/offset?
        if var_info.bit_mask is not None:
            bit_mask = var_info.bit_mask
            shift_amount = var_info.right_shift
            offset = var_info.additional_offset
            numpy.bitwise_and(data, bit_mask, data)
            numpy.right_shift(data, shift_amount, data)
            numpy.add(data, offset, data)

        # Convert to the correct data type
        data = data.astype(var_info.data_type)

        # Get the fill value
        if var_info.fill_attr_name and isinstance(var_info.fill_attr_name, (str, unicode)):
            fill_value = self[var_info.var_name + "." + var_info.fill_attr_name]
            mask = data == fill_value
        elif var_info.fill_attr_name:
            fill_value = var_info.fill_attr_name
            mask = data >= fill_value
        else:
            fill_value = -999.0
            mask = data == fill_value

        # Get the valid_min and valid_max
        valid_min, valid_max = None, None
        if var_info.range_attr_name:
            if isinstance(var_info.range_attr_name, (str, unicode)):
                valid_min, valid_max = self[var_info.var_name + "." + var_info.range_attr_name]
            else:
                valid_min, valid_max = var_info.range_attr_name

        # Certain data need to have special values clipped
        if var_info.clip_saturated and valid_max is not None:
            LOG.debug("Setting any saturation or \"can't aggregate\" values to valid maximum")
            data[(data == self.CANT_AGGR_VALUE) | (data == self.SATURATION_VALUE)] = valid_max

        # Get the scaling factors
        scale_value = None
        if var_info.scale_attr_name:
            try:
                scale_value = self[var_info.var_name + "." + var_info.scale_attr_name]
                if var_info.index is not None:
                    scale_value = scale_value[var_info.index]
                scale_value = float(scale_value)
            except KeyError:
                LOG.debug("No scaling factors for %s", item)
        offset_value = None
        if var_info.offset_attr_name is not None:
            try:
                offset_value = self[var_info.var_name + "." + var_info.offset_attr_name]
                if var_info.index is not None:
                    offset_value = offset_value[var_info.index]
                offset_value = float(offset_value)
            except KeyError:
                LOG.debug("No offset for %s", item)

        LOG.debug("Variable " + str(var_info.var_name) + " is using scale value " + str(scale_value) + " and offset value " + str(offset_value))

        if offset_value is not None:
            data -= offset_value
        if scale_value is not None:
            data *= scale_value

        # Special case: 250m Resolution
        if var_info.interpolate:
            if mask is not None:
                data[mask] = numpy.nan

            if self.nav_interpolation["250"][0] is not None and self.nav_interpolation["250"][1] is not None:
                LOG.debug("Returning previously interpolated 250m resolution geolocation data")
                data = self.nav_interpolation["250"][not (item == K_LONGITUDE_250)]
                self.nav_interpolation["250"] = [None, None]
                return data

            if item == K_LONGITUDE_250:
                self.nav_interpolation["250"][0] = data
            else:
                self.nav_interpolation["250"][1] = data

            if self.nav_interpolation["250"][0] is None or self.nav_interpolation["250"][1] is None:
                # We don't have the other coordinate data yet
                self.get_swath_data(K_LONGITUDE_250 if item == K_LATITUDE_250 else K_LATITUDE_250, fill=fill)
            else:
                # We already have the other coordinate variable, the user isn't asking for this item so just return
                LOG.debug("Returning 'None' because this instance of the function shouldn't have been called by the user")
                return None

            LOG.info("Interpolating to higher resolution: %s" % (var_info.var_name,))
            lon_data, lat_data = self.nav_interpolation["250"]

            new_lon_data, new_lat_data = interpolate_geolocation_cartesian(lon_data, lat_data)

            new_lon_data[numpy.isnan(new_lon_data)] = fill
            new_lat_data[numpy.isnan(new_lat_data)] = fill
            # Cache the results when the user requests the other coordinate
            self.nav_interpolation["250"] = [new_lon_data, new_lat_data]

            data = new_lon_data if item == K_LONGITUDE_250 else new_lat_data
        elif mask is not None:
            data[mask] = fill

        return data


class MultiFileReader(BaseMultiFileReader):
    def __init__(self, file_type_info, single_class=FileReader):
        super(MultiFileReader, self).__init__(file_type_info, single_class)


class FileInfo(object):
    def __init__(self, var_name, index=None,
                 scale_attr_name="scale_factor", offset_attr_name="add_offset", range_attr_name="valid_range",
                 bit_mask=None, right_shift=None, additional_offset=None, fill_attr_name="_FillValue",
                 data_type=numpy.float32, interpolate=False, clip_saturated=False):
        self.var_name = var_name
        self.index = index
        self.data_type = data_type
        self.scale_attr_name = scale_attr_name
        self.offset_attr_name = offset_attr_name
        self.range_attr_name = range_attr_name
        self.bit_mask = bit_mask
        self.right_shift = right_shift
        self.additional_offset = additional_offset
        self.fill_attr_name = fill_attr_name
        self.interpolate = interpolate
        self.clip_saturated = clip_saturated


FILE_TYPES = {}
FILE_TYPES[FT_MOD03] = {
    K_LONGITUDE: FileInfo("Longitude", scale_attr_name=None, offset_attr_name=None),
    K_LATITUDE: FileInfo("Latitude", scale_attr_name=None, offset_attr_name=None),
    K_LONGITUDE_250: FileInfo("Longitude", interpolate=True),
    K_LATITUDE_250: FileInfo("Latitude", interpolate=True),
    K_SZA: FileInfo("SolarZenith", offset_attr_name=None),
    K_SenZA: FileInfo("SensorZenith", offset_attr_name=None),
}
FILE_TYPES[FT_MOD021KM] = {
    K_VIS01: FileInfo("EV_250_Aggr1km_RefSB", 0, "reflectance_scales", "reflectance_offsets"),
    K_VIS02: FileInfo("EV_250_Aggr1km_RefSB", 1, "reflectance_scales", "reflectance_offsets", clip_saturated=True),
    K_VIS03: FileInfo("EV_500_Aggr1km_RefSB", 0, "reflectance_scales", "reflectance_offsets"),
    K_VIS04: FileInfo("EV_500_Aggr1km_RefSB", 1, "reflectance_scales", "reflectance_offsets"),
    K_VIS05: FileInfo("EV_500_Aggr1km_RefSB", 2, "reflectance_scales", "reflectance_offsets"),
    K_VIS06: FileInfo("EV_500_Aggr1km_RefSB", 3, "reflectance_scales", "reflectance_offsets"),
    K_VIS07: FileInfo("EV_500_Aggr1km_RefSB", 4, "reflectance_scales", "reflectance_offsets"),
    K_VIS26: FileInfo("EV_Band26", None, "reflectance_scales", "reflectance_offsets"),
    K_IR20: FileInfo("EV_1KM_Emissive", 0, "radiance_scales", "radiance_offsets"),
    K_IR21: FileInfo("EV_1KM_Emissive", 1, "radiance_scales", "radiance_offsets"),
    K_IR22: FileInfo("EV_1KM_Emissive", 2, "radiance_scales", "radiance_offsets"),
    K_IR23: FileInfo("EV_1KM_Emissive", 3, "radiance_scales", "radiance_offsets"),
    K_IR24: FileInfo("EV_1KM_Emissive", 4, "radiance_scales", "radiance_offsets"),
    K_IR25: FileInfo("EV_1KM_Emissive", 5, "radiance_scales", "radiance_offsets"),
    K_IR27: FileInfo("EV_1KM_Emissive", 6, "radiance_scales", "radiance_offsets"),
    K_IR28: FileInfo("EV_1KM_Emissive", 7, "radiance_scales", "radiance_offsets"),
    K_IR29: FileInfo("EV_1KM_Emissive", 8, "radiance_scales", "radiance_offsets"),
    K_IR30: FileInfo("EV_1KM_Emissive", 9, "radiance_scales", "radiance_offsets"),
    K_IR31: FileInfo("EV_1KM_Emissive", 10, "radiance_scales", "radiance_offsets"),
    K_IR32: FileInfo("EV_1KM_Emissive", 11, "radiance_scales", "radiance_offsets"),
    K_IR33: FileInfo("EV_1KM_Emissive", 12, "radiance_scales", "radiance_offsets"),
    K_IR34: FileInfo("EV_1KM_Emissive", 13, "radiance_scales", "radiance_offsets"),
    K_IR35: FileInfo("EV_1KM_Emissive", 14, "radiance_scales", "radiance_offsets"),
    K_IR36: FileInfo("EV_1KM_Emissive", 15, "radiance_scales", "radiance_offsets"),
}
FILE_TYPES[FT_MOD02HKM] = {}
FILE_TYPES[FT_MOD02QKM] = {
    K_VIS01: FileInfo("EV_250_RefSB", 0, "reflectance_scales", "reflectance_offsets"),
    K_VIS02: FileInfo("EV_250_RefSB", 1, "reflectance_scales", "reflectance_offsets", clip_saturated=True),
}
FILE_TYPES[FT_MOD06CT] = {
    K_LONGITUDE: FileInfo("Longitude",
                          scale_attr_name=None, offset_attr_name=None, range_attr_name=None, fill_attr_name=None),
    K_LATITUDE: FileInfo("Latitude",
                         scale_attr_name=None, offset_attr_name=None, range_attr_name=None, fill_attr_name=None),
    K_CTT: FileInfo("Cloud_Top_Temperature"),
}
FILE_TYPES[FT_MOD07] = {
    K_LONGITUDE: FileInfo("Longitude",
                          scale_attr_name=None, offset_attr_name=None, range_attr_name=None, fill_attr_name=None),
    K_LATITUDE: FileInfo("Latitude",
                         scale_attr_name=None, offset_attr_name=None, range_attr_name=None, fill_attr_name=None),
    K_TPW: FileInfo("Water_Vapor"),
}
FILE_TYPES[FT_MOD28] = {
    K_SST: FileInfo("Sea_Surface_Temperature", range_attr_name=None),
}
FILE_TYPES[FT_MOD35] = {
    K_CMASK: FileInfo("Cloud_Mask",
                      index=0, bit_mask=0b110, right_shift=1, additional_offset=1, data_type=numpy.int32),
    K_LSMASK: FileInfo("Cloud_Mask",
                       index=0, bit_mask=0b11000000, right_shift=1, additional_offset=1, data_type=numpy.int32),
}
FILE_TYPES[FT_MASK_BYTE1] = {
    K_CMASK: FileInfo("MODIS_Cloud_Mask", data_type=numpy.int32),
    K_LSMASK: FileInfo("MODIS_Simple_LandSea_Mask", data_type=numpy.int32),
    K_SIMASK: FileInfo("MODIS_Snow_Ice_Flag", data_type=numpy.int32),
}
FILE_TYPES[FT_MODLST] = {
    K_LST: FileInfo("LST", range_attr_name=None, offset_attr_name=None, fill_attr_name="missing_value"),
    K_SLST: FileInfo("LST", range_attr_name=None, offset_attr_name=None, fill_attr_name="missing_value"),
}
FILE_TYPES[FT_IST] = {
    K_IST: FileInfo("Ice_Surface_Temperature"),
}
FILE_TYPES[FT_INV] = {
    K_INV: FileInfo("Inversion_Strength"),
    K_IND: FileInfo("Inversion_Depth"),
}
FILE_TYPES[FT_ICECON] = {
    K_ICECON: FileInfo("Ice_Concentration"),
}
FILE_TYPES[FT_NDVI_1000M] = {
    K_NDVI: FileInfo("NDVI", range_attr_name=None, fill_attr_name=None),
}

