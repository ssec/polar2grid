#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2012-2015 Space Science and Engineering Center (SSEC),
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
# Written by David Hoese    September 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""The MIRS frontend extracts data from files created by the Community
Satellite Processing Package (CSPP) direct broadcast version of the
NOAA/STAR Microwave Integrated Retrieval System (MIRS). The software
supports the creation of atmospheric profile and surface parameters from 
ATMS, AMSU-A, and MHS microwave sensor data. For more information
on this product, please see the 
`CSPP LEO distribution website <https://cimss.ssec.wisc.edu/cspp/>`_.

When executed on Suomi-NPP Advanced Technology Microwave Sounder (ATMS) 
MIRS product files, a limb correction algorithm is applied for  
brightness temperatures reprojections for each of the 22 spectral bands.  
The correction software was provided by Kexin Zhang of NOAA STAR, and
is applied as part of the MIRS ATMS Polar2Grid execution. 

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--fornav-D`` option is set to 100 and the
``--fornav-d`` option is set to 1.

The frontend offers the following products:

    +--------------------+----------------------------------------------------+
    | Product Name       | Description                                        |
    +====================+====================================================+
    | rain_rate          | Rain Rate                                          |
    +--------------------+----------------------------------------------------+
    | sea_ice            | Sea Ice in percent                                 |
    +--------------------+----------------------------------------------------+
    | snow_cover         | Snow Cover                                         |
    +--------------------+----------------------------------------------------+
    | tpw                | Total Precipitable Water                           |
    +--------------------+----------------------------------------------------+
    | swe                | Snow Water Equivalence                             |
    +--------------------+----------------------------------------------------+
    | btemp_X            | Brightness Temperature for channel X (see below)   |
    +--------------------+----------------------------------------------------+

For specific brightness temperature band products, use the ``btemp_X`` option,
where ``X`` is a combination of the microwave frequency (integer) and
polarization of the channel. If there is more than one channel at that
frequency and polarization a "count" number is added to the end. To create
output files of all available bands, use the ``--bt-channels`` option.

As an example, the ATMS band options are:

.. list-table:: ATMS Brightness Temperature Channels
    :header-rows: 1
    
    * - **Band Number**
      - **Frequency (GHz)**
      - **Polarization**
      - **Polar2Grid Dataset Name**
    * - 1
      - 23.79
      - V
      - btemp_23v
    * - 2
      - 31.40
      - V
      - btemp_31v
    * - 3
      - 50.30
      - H
      - btemp_50h
    * - 4
      - 51.76
      - H
      - btemp_51h
    * - 5
      - 52.80
      - H
      - btemp_52h
    * - 6
      - 53.59±0.115
      - H
      - btemp_53h
    * - 7
      - 54.40
      - H
      - btemp_54h1
    * - 8
      - 54.94
      - H
      - btemp_54h2
    * - 9
      - 55.50
      - H
      - btemp_55h
    * - 10
      - 57.29
      - H
      - btemp_57h1
    * - 11
      - 57.29±2.17
      - H
      - btemp_57h2
    * - 12
      - 57.29±0.3222±0.048
      - H
      - btemp_57h3
    * - 13
      - 57.29±0.3222±0.022
      - H
      - btemp_57h4
    * - 14
      - 57.29±0.3222±0.010
      - H
      - btemp_57h5
    * - 15
      - 57.29±0.3222±0.0045
      - H
      - btemp_57h6
    * - 16
      - 88.20
      - V
      - btemp_88v
    * - 17
      - 165.50
      - H
      - btemp_165h
    * - 18
      - 183.31±7.0
      - H
      - btemp_183h1
    * - 19
      - 183.31±4.5
      - H
      - btemp_183h2
    * - 20
      - 183.31±3.0
      - H
      - btemp_183h3
    * - 21
      - 183.31±1.8
      - H
      - btemp_183h4
    * - 22
      - 183.31±1.0
      - H
      - btemp_183h5

"""
__docformat__ = "restructuredtext en"

import sys
from datetime import datetime
from netCDF4 import Dataset

import logging
import numpy as np
import os

from polar2grid.core import containers, roles
from polar2grid.core.frontend_utils import BaseMultiFileReader, BaseFileReader, ProductDict, GeoPairDict

try:
    # try getting setuptools/distribute's version of resource retrieval first
    from pkg_resources import resource_string as get_resource_string
except ImportError:
    from pkgutil import get_data as get_resource_string

LOG = logging.getLogger(__name__)
# 'Polo' variable in MIRS files use these values for H/V polarization
POLO_H = 3
POLO_V = 2

# File types (only one for now)
FT_IMG = "MIRS_IMG"
# File variables
RR_VAR = "rr_var"
BT_ALL_VARS = "bt_var"
FREQ_VAR = "freq_var"
LAT_VAR = "latitude_var"
LON_VAR = "longitude_var"
SURF_TYPE_VAR = "surface_type_var"
SICE_VAR = "sea_ice_var"
SNOWCOVER_VAR = "snow_cover_var"
TPW_VAR = "tpw_var"
SWE_VAR = "swe_var"
CLW_VAR = "clw_var"
TSKIN_VAR = "tskin_var"
SFR_VAR = "sfr_var"

PRODUCT_RAIN_RATE = "rain_rate"
PRODUCT_BT_CHANS = "btemp_channels"
PRODUCT_LATITUDE = "latitude"
PRODUCT_LONGITUDE = "longitude"
PRODUCT_SURF_TYPE = "surface_type"
PRODUCT_SICE = "sea_ice"
PRODUCT_SNOW_COVER = "snow_cover"
PRODUCT_TPW = "tpw"
PRODUCT_SWE = "swe"
PRODUCT_CLW = "clw"
PRODUCT_TSKIN = "tskin"
PRODUCT_SFR = "sfr"

PAIR_MIRS_NAV = "mirs_nav"

PRODUCTS = ProductDict()
PRODUCTS.add_product(PRODUCT_LATITUDE, PAIR_MIRS_NAV, "latitude", FT_IMG, LAT_VAR, description="Latitude", units="degrees")
PRODUCTS.add_product(PRODUCT_LONGITUDE, PAIR_MIRS_NAV, "longitude", FT_IMG, LON_VAR, description="Longitude", units="degrees")
PRODUCTS.add_product(PRODUCT_RAIN_RATE, PAIR_MIRS_NAV, "rain_rate", FT_IMG, RR_VAR, description="Rain Rate", units="mm/hr")
PRODUCTS.add_product(PRODUCT_SURF_TYPE, PAIR_MIRS_NAV, "mask", FT_IMG, SURF_TYPE_VAR, description="Surface Type: type of surface:0-ocean,1-sea ice,2-land,3-snow")
PRODUCTS.add_product(PRODUCT_BT_CHANS, PAIR_MIRS_NAV, "brightness_temperature", FT_IMG, BT_ALL_VARS, description="Channel Brightness Temperature for every channel", units="K")
PRODUCTS.add_product(PRODUCT_SICE, PAIR_MIRS_NAV, "sea_ice", FT_IMG, SICE_VAR, description="Sea Ice", units="%")
PRODUCTS.add_product(PRODUCT_SNOW_COVER, PAIR_MIRS_NAV, "snow_cover", FT_IMG, SNOWCOVER_VAR, description="Snow Cover", units="1")
PRODUCTS.add_product(PRODUCT_TPW, PAIR_MIRS_NAV, "total_precipitable_water", FT_IMG, TPW_VAR, description="Total Precipitable Water", units="mm")
PRODUCTS.add_product(PRODUCT_SWE, PAIR_MIRS_NAV, "snow_water_equivalence", FT_IMG, SWE_VAR, description="Snow Water Equivalence", units="cm")
PRODUCTS.add_product(PRODUCT_CLW, PAIR_MIRS_NAV, "cloud_liquid_water", FT_IMG, CLW_VAR, description="Cloud Liquid Water", units="mm")
PRODUCTS.add_product(PRODUCT_TSKIN, PAIR_MIRS_NAV, "skin_temperature", FT_IMG, TSKIN_VAR, description="skin temperature", units="K")
PRODUCTS.add_product(PRODUCT_SFR, PAIR_MIRS_NAV, "snow_fall_rate", FT_IMG, SFR_VAR, description="snow fall rate", units="mm/hr")


GEO_PAIRS = GeoPairDict()
GEO_PAIRS.add_pair(PAIR_MIRS_NAV, PRODUCT_LONGITUDE, PRODUCT_LATITUDE, 0)

### I/O Operations ###

FILE_STRUCTURE = {
    RR_VAR: ("RR", ("scale", "scale_factor"), None, None),
    BT_ALL_VARS: ("BT", ("scale", "scale_factor"), None, None),
    FREQ_VAR: ("Freq", None, None, None),
    LAT_VAR: ("Latitude", None, None, None),
    LON_VAR: ("Longitude", None, None, None),
    SURF_TYPE_VAR: ("Sfc_type", None, None, None),
    SICE_VAR: ("SIce", ("scale", "scale_factor"), None, None),
    SNOWCOVER_VAR: ("Snow", ("scale", "scale_factor"), None, None),
    TPW_VAR: ("TPW", ("scale", "scale_factor"), None, None),
    SWE_VAR: ("SWE", ("scale", "scale_factor"), None, None),
    CLW_VAR: ("CLW", ("scale", "scale_factor"), None, None),
    TSKIN_VAR: ("TSkin", ("scale", "scale_factor"), None, None),
    SFR_VAR: ("SFR", ("scale", "scale_factor"), None, None),
    }

LIMB_SEA_FILE = os.environ.get("ATMS_LIMB_SEA", "polar2grid.mirs:limball_atmssea.txt")
LIMB_LAND_FILE = os.environ.get("ATMS_LIMB_LAND", "polar2grid.mirs:limball_atmsland.txt")


def read_atms_limb_correction_coefficients(fn):
    if os.path.isfile(fn):
        coeff_str = open(fn, "r").readlines()
    else:
        parts = fn.split(":")
        mod_part, file_part = parts if len(parts) == 2 else ("", parts[0])
        mod_part = mod_part or __package__  # self.__module__
        coeff_str = get_resource_string(mod_part, file_part).decode().split("\n")
    # make it a generator
    coeff_str = (line.strip() for line in coeff_str)

    all_coeffs = np.zeros((22, 96, 22), dtype=np.float32)
    all_amean = np.zeros((22, 96, 22), dtype=np.float32)
    all_dmean = np.zeros(22, dtype=np.float32)
    all_nchx = np.zeros(22, dtype=np.int32)
    all_nchanx = np.zeros((22, 22), dtype=np.int32)
    all_nchanx[:] = 9999
    # There should be 22 sections
    for chan_idx in range(22):
        # blank line at the start of each section
        _ = next(coeff_str)

        # section header
        nx, nchx, dmean = [x.strip() for x in next(coeff_str).split(" ") if x]
        nx = int(nx)
        all_nchx[chan_idx] = nchx = int(nchx)
        all_dmean[chan_idx] = float(dmean)

        # coeff locations (indexes to put the future coefficients in)
        locations = [int(x.strip()) for x in next(coeff_str).split(" ") if x]
        assert(len(locations) == nchx)
        for x in range(nchx):
            all_nchanx[chan_idx, x] = locations[x] - 1

        # Read 'nchx' coefficients for each of 96 FOV
        for fov_idx in range(96):
            # chan_num, fov_num, *coefficients, error
            coeff_line_parts = [x.strip() for x in next(coeff_str).split(" ") if x][2:]
            coeffs = [float(x) for x in coeff_line_parts[:nchx]]
            ameans = [float(x) for x in coeff_line_parts[nchx:-1]]
            error_val = float(coeff_line_parts[-1])
            for x in range(nchx):
                all_coeffs[chan_idx, fov_idx, all_nchanx[chan_idx, x]] = coeffs[x]
                all_amean[all_nchanx[chan_idx, x], fov_idx, chan_idx] = ameans[x]

    return all_dmean, all_coeffs, all_amean, all_nchx, all_nchanx


def apply_atms_limb_correction(datasets, dmean, coeffs, amean, nchx, nchanx):
    all_new_ds = []
    coeff_sum = np.zeros(datasets.shape[1], dtype=datasets[0].dtype)
    for channel_idx in range(datasets.shape[0]):
        ds = datasets[channel_idx]
        new_ds = ds.copy()
        all_new_ds.append(new_ds)
        for fov_idx in range(96):
            coeff_sum[:] = 0
            for k in range(nchx[channel_idx]):
                coef = coeffs[channel_idx, fov_idx, nchanx[channel_idx, k]] * (
                    datasets[nchanx[channel_idx, k], :, fov_idx] -
                    amean[nchanx[channel_idx, k], fov_idx, channel_idx])
                coeff_sum += coef
            new_ds[:, fov_idx] = coeff_sum + dmean[channel_idx]

    return all_new_ds


class NetCDFFileReader(object):
    def __init__(self, filepath):
        self.filename = os.path.basename(filepath)
        self.filepath = os.path.realpath(filepath)
        self.nc_obj = Dataset(self.filepath, "r")

    def __getattr__(self, item):
        return getattr(self.nc_obj, item)

    def __getitem__(self, item):
        return self.nc_obj.variables[item]


class MIRSFileReader(BaseFileReader):
    """Basic MIRS file reader.

    If there are alternate formats/structures for MIRS files then new classes should be made.
    """
    FILE_TYPE = FT_IMG

    GLOBAL_FILL_ATTR_NAME = "missing_value"
    # Constant -> (var_name, scale_attr_name, fill_attr_name, frequency)

    # best case nadir resolutions in meters (could be made per band):
    INST_NADIR_RESOLUTION = {
        "atms": 15800,
        "amsua-mhs": 20300,
    }

    # worst case nadir resolutions in meters (could be made per band):
    INST_LIMB_RESOLUTION = {
        "atms": 323100,
        "amsua-mhs": 323100,
    }

    FILENAME_TO_SAT = {
        "M1": "metopb",
        "M2": "metopa",
        "NN": "noaa18",
        "NP": "noaa19",
        "n18": "noaa18",
        "n19": "noaa19",
        "ma1": "metopb",
        "ma2": "metopa",
        # should have file attributes, but just in case:
        "npp": "npp",
        "n20": "n20",
    }

    def __init__(self, filepath, file_type_info):
        super(MIRSFileReader, self).__init__(NetCDFFileReader(filepath), file_type_info)
        # Not supported in older version of NetCDF4 library
        #self.file_handle.set_auto_maskandscale(False)
        if not self.handles_file(self.file_handle):
            LOG.error("Unknown file format for file %s" % (self.filename,))
            raise ValueError("Unknown file format for file %s" % (self.filename,))

        try:
            self.satellite = self.file_handle.satellite_name.lower()
            self.instrument = self.file_handle.instrument_name.lower()
            self.begin_time = datetime.strptime(self.file_handle.time_coverage_start, "%Y-%m-%dT%H:%M:%SZ")
            self.end_time = datetime.strptime(self.file_handle.time_coverage_end, "%Y-%m-%dT%H:%M:%SZ")
        except AttributeError:
            if self.file_handle.filename.startswith('IMG'):
                self._parse_old_filename()
            else:
                self._parse_new_filename()

        if self.instrument in self.INST_NADIR_RESOLUTION:
            self.nadir_resolution = self.INST_NADIR_RESOLUTION[self.instrument]
        else:
            self.nadir_resolution = None

        if self.instrument in self.INST_LIMB_RESOLUTION:
            self.limb_resolution = self.INST_LIMB_RESOLUTION[self.instrument]
        else:
            self.limb_resolution = None

    def _parse_old_filename(self):
        # IMG_SX.M1.D15238.S1614.E1627.B0000001.WE.HR.ORB.nc
        fn_parts = self.file_handle.filename.split(".")
        self.satellite = self.FILENAME_TO_SAT[fn_parts[1]]
        self.instrument = "amsua-mhs"  # actually combination of mhs and amsu
        self.begin_time = datetime.strptime(fn_parts[2][1:] + fn_parts[3][1:], "%y%j%H%M")
        self.end_time = datetime.strptime(fn_parts[2][1:] + fn_parts[4][1:], "%y%j%H%M")

    def _parse_new_filename(self):
        # NPR-MIRS-IMG_v11r3_n19_s201809112039000_e201809112050000_c201809112117030.nc
        fn_parts = self.file_handle.filename.split('_')
        self.satellite = self.FILENAME_TO_SAT[fn_parts[2]]
        self.instrument = "amsua-mhs"  # actually combination of mhs and amsu
        self.begin_time = datetime.strptime(fn_parts[3][1:-1], "%Y%m%d%H%M%S")
        self.end_time = datetime.strptime(fn_parts[4][1:-1], "%Y%m%d%H%M%S")

    @classmethod
    def handles_file(cls, fn_or_nc_obj):
        """Validate that the file this object represents is something that we actually know how to read.
        """
        try:
            if isinstance(fn_or_nc_obj, str):
                nc_obj = NetCDFFileReader(fn_or_nc_obj)
            else:
                nc_obj = fn_or_nc_obj

            return True
        except AssertionError:
            LOG.debug("File Validation Exception Information: ", exc_info=True)
            return False

    def __getitem__(self, item):
        known_item = self.file_type_info.get(item, item)
        if known_item is None:
            raise KeyError("Key 'None' was not found")

        LOG.debug("Loading %s from %s", known_item[0], self.filename)
        nc_var = self.file_handle[known_item[0]]
        nc_var.set_auto_maskandscale(False)
        return nc_var

    def get_fill_value(self, item, default_type=np.float32):
        fill_value = None
        if item in FILE_STRUCTURE:
            var_name = FILE_STRUCTURE[item][0]
            fill_attr_name = FILE_STRUCTURE[item][2]
            if fill_attr_name:
                fill_value = getattr(self.file_handle[var_name], fill_attr_name)
        if fill_value is None:
            fill_value = getattr(self.file_handle, self.GLOBAL_FILL_ATTR_NAME, None)

        LOG.debug("File fill value for '%s' is '%f'", item, float(fill_value))
        return fill_value

    def get_valid_range(self, item):
        valid_range = 0
        if item in FILE_STRUCTURE:
            var_name = FILE_STRUCTURE[item][0]
            valid_range = getattr(self.file_handle[var_name], 'valid_range', None)
        return valid_range

    def get_scale_value(self, item):
        scale_value = None
        if item in FILE_STRUCTURE:
            var_name = FILE_STRUCTURE[item][0]
            scale_attr_name = FILE_STRUCTURE[item][1]
            if scale_attr_name:
                if isinstance(scale_attr_name, str):
                    scale_attr_name = [scale_attr_name]
                for x in scale_attr_name:
                    try:
                        scale_value = float(self.file_handle[var_name].getncattr(x))
                        LOG.debug("File scale value for '%s' is '%f'", item, float(scale_value))
                        break
                    except AttributeError:
                        pass
        return scale_value

    def get_channel_index(self, freq):
        freq_var = self[FREQ_VAR]
        freq_idx = np.nonzero(freq_var[:] == freq)[0]
        # try getting something close
        if freq_idx.shape[0] == 0:
            freq_idx = np.nonzero(np.isclose(freq_var[:], freq, atol=1))[0]
        if freq_idx.shape[0] != 0:
            freq_idx = freq_idx[0]
        else:
            LOG.error("Frequency %f does not exist" % (freq,))
            raise ValueError("Frequency %f does not exist" % (freq,))
        return freq_idx

    def filter_by_frequency(self, item, arr, freq):
        freq_idx = self.get_channel_index(freq)
        freq_var = self[FREQ_VAR]
        freq_dim_idx = self[item].dimensions.index(freq_var.dimensions[0])
        idx_obj = [slice(x) for x in arr.shape]
        idx_obj[freq_dim_idx] = freq_idx
        return arr[idx_obj]

    def filter_by_channel(self, item, arr, idx):
        freq_var = self[FREQ_VAR]
        freq_dim_idx = self[item].dimensions.index(freq_var.dimensions[0])
        idx_obj = [slice(x) for x in arr.shape]
        idx_obj[freq_dim_idx] = idx
        return arr[idx_obj]

    def get_swath_data(self, item, dtype=np.float32, fill=np.nan):
        """Get swath data from the file. Usually requires special processing.
        """
        var_data = self[item][:].astype(dtype)
        freq = FILE_STRUCTURE[item][3]
        if isinstance(freq, int):
            # filter by channel index
            var_data = self.filter_by_channel(item, var_data, freq)
        elif freq:
            # filter by float channel frequency
            var_data = self.filter_by_frequency(item, var_data, freq)
        elif item == BT_ALL_VARS:
            # import ipdb; ipdb.set_trace()
            # special case, make sure dimension order is channel, scan, fov
            channel_dim_name = "Channel"
            scan_dim_name = "Scanline"
            fov_dim_name = "Field_of_view"
            dims = list(self[item].dimensions)
            if dims[0] != channel_dim_name:
                idx = dims.index(channel_dim_name)
                var_data = np.swapaxes(var_data, 0, idx)
                # reorder the dimension names
                swap_name = dims[0]
                dims[0] = channel_dim_name
                dims[idx] = swap_name
            if dims[1] != scan_dim_name:
                idx = dims.index(scan_dim_name)
                var_data = np.swapaxes(var_data, 1, idx)
                swap_name = dims[1]
                dims[1] = scan_dim_name
                dims[idx] = swap_name

        file_fill = self.get_fill_value(item)
        file_scale = self.get_scale_value(item)
        valid_range = self.get_valid_range(item)

        bad_mask = None
        if file_fill is not None:
            if item == LON_VAR:
                # Because appaarently -999.79999877929688 is a fill value now
                bad_mask = (var_data == file_fill) | (var_data < -180) | (var_data > 180)
            elif item == LAT_VAR:
                # Because appaarently -999.79999877929688 is a fill value now
                bad_mask = (var_data == file_fill) | (var_data < -90) | (var_data > 90)
            else:
                bad_mask = var_data == file_fill
            var_data[bad_mask] = fill
        if valid_range is not None:
            invalid_mask = (var_data < valid_range[0]) | (var_data > valid_range[1])
            var_data[invalid_mask] = fill
            if bad_mask is not None:
                bad_mask |= invalid_mask
        if file_scale is not None:
            var_data = var_data.astype(dtype)
            if bad_mask is not None:
                var_data[~bad_mask] = var_data[~bad_mask] * file_scale
            else:
                var_data = var_data * file_scale

        return var_data


class MIRSMultiReader(BaseMultiFileReader):
    def __init__(self, filenames=None):
        super(MIRSMultiReader, self).__init__(FILE_STRUCTURE, MIRSFileReader)

    @classmethod
    def handles_file(cls, fn_or_nc_obj):
        return MIRSFileReader.handles_file(fn_or_nc_obj)

    def get_channel_index(self, freq):
        return self.file_readers[0].get_channel_index(freq)

    @property
    def satellite(self):
        return self.file_readers[0].satellite

    @property
    def instrument(self):
        return self.file_readers[0].instrument

    @property
    def begin_time(self):
        return self.file_readers[0].begin_time

    @property
    def end_time(self):
        return self.file_readers[-1].end_time

    @property
    def nadir_resolution(self):
        return self.file_readers[0].nadir_resolution

    @property
    def limb_resolution(self):
        return self.file_readers[0].limb_resolution

    @property
    def filepaths(self):
        return [fr.filepath for fr in self.file_readers]


FILE_CLASSES = {
    FT_IMG: MIRSMultiReader,
}


def get_file_type(filepath):
    LOG.debug("Checking file type for %s", filepath)
    if not filepath.endswith(".nc"):
        return None

    nc_obj = Dataset(filepath, "r")
    for file_kind, file_class in FILE_CLASSES.items():
        if file_class.handles_file(nc_obj):
            return file_kind

    LOG.debug("File doesn't match any known file types: %s", filepath)
    return None


class Frontend(roles.FrontendRole):
    """Polar2Grid Frontend object for handling MIRS files.
    """
    FILE_EXTENSIONS = [".nc"]
    PRODUCTS = PRODUCTS
    GEO_PAIRS = GEO_PAIRS

    def __init__(self, **kwargs):
        super(Frontend, self).__init__(**kwargs)
        self._load_files(self.find_files_with_extensions())
        self.all_bt_channels = []
        self.update_dynamic_products()

        self.secondary_product_functions = {}
        for pname in self.all_bt_channels:
            self.secondary_product_functions[pname] = self.limb_correct_atms_bt

    def update_dynamic_products(self):
        fh = self.file_readers['MIRS_IMG'].file_readers[0]
        freq = fh[('Freq',)]
        polo = fh[('Polo',)]
        from collections import Counter
        c = Counter()
        normals = []
        for idx, (f, p) in enumerate(zip(freq, polo)):
            normal_f = str(int(f))
            normal_p = 'v' if p == POLO_V else 'h'
            c[normal_f + normal_p] += 1
            normals.append((idx, f, p, normal_f, normal_p))

        c2 = Counter()
        new_names = []
        for idx, f, p, normal_f, normal_p in normals:
            c2[normal_f + normal_p] += 1
            new_name = "btemp_{}{}{}".format(normal_f, normal_p, str(c2[normal_f + normal_p] if c[normal_f + normal_p] > 1 else ''))
            new_names.append(new_name)
            var_name = 'bt_var_{}'.format(new_name)
            FILE_STRUCTURE[var_name] = ("BT", ("scale", "scale_factor"), None, idx)
            self.PRODUCTS.add_product(new_name, PAIR_MIRS_NAV, "toa_brightness_temperature", FT_IMG, var_name, description="Channel Brightness Temperature at {}GHz".format(f), units="K", frequency=f, dependencies=(PRODUCT_BT_CHANS, PRODUCT_SURF_TYPE), channel_index=idx)
            self.all_bt_channels.append(new_name)

    def _load_files(self, filepaths):
        self.file_readers = {}
        for filepath in filepaths:
            file_type = get_file_type(filepath)
            if file_type is None:
                LOG.debug("Unrecognized file: %s", filepath)
                continue

            if file_type in self.file_readers:
                file_reader = self.file_readers[file_type]
            else:
                self.file_readers[file_type] = file_reader = FILE_CLASSES[file_type]()
            file_reader.add_file(filepath)

        # Get rid of the readers we aren't using
        for file_type, file_reader in self.file_readers.items():
            if not len(file_reader):
                del self.file_readers[file_type]
            else:
                self.file_readers[file_type].finalize_files()

        if not self.file_readers:
            LOG.error("No useable files loaded")
            raise ValueError("No useable files loaded")

        first_length = len(self.file_readers[next(iter(self.file_readers.keys()))])
        if not all(len(x) == first_length for x in self.file_readers.values()):
            LOG.error("Corrupt directory: Varying number of files for each type")
            ft_str = "\n\t".join("%s: %d" % (ft, len(fr)) for ft, fr in self.file_readers.items())
            LOG.debug("File types and number of files:\n\t%s", ft_str)
            raise RuntimeError("Corrupt directory: Varying number of files for each type")

        self.available_file_types = self.file_readers.keys()

    @property
    def available_product_names(self):
        raw_products = [p for p in self.PRODUCTS.all_raw_products if self.raw_product_available(p)]
        return sorted(self.PRODUCTS.get_product_dependents(raw_products))

    def raw_product_available(self, product_name):
        """Is it possible to load the provided product with the files provided to the `Frontend`.

        :returns: True if product can be loaded, False otherwise (including if product is not a raw product)
        """
        product_def = self.PRODUCTS[product_name]
        if product_def.is_raw:
            if isinstance(product_def.file_type, str):
                file_type = product_def.file_type
            else:
                return any(ft in self.file_readers for ft in product_def.file_type)

            return file_type in self.file_readers
        return False

    @property
    def all_product_names(self):
        return self.PRODUCTS.keys()

    @property
    def default_products(self):
        if os.getenv("P2G_MIRS_DEFAULTS", None):
            return os.getenv("P2G_MIRS_DEFAULTS")

        return list({PRODUCT_RAIN_RATE, 'btemp_88v', 'btemp_89v1'} &
                    set(self.PRODUCTS.keys()))

    @property
    def begin_time(self):
        return self.file_readers[next(iter(self.file_readers.keys()))].begin_time

    @property
    def end_time(self):
        return self.file_readers[next(iter(self.file_readers.keys()))].end_time

    def create_swath_definition(self, lon_product, lat_product):
        product_def = self.PRODUCTS[lon_product["product_name"]]
        lon_file_reader = self.file_readers[product_def.file_type]
        product_def = self.PRODUCTS[lat_product["product_name"]]
        lat_file_reader = self.file_readers[product_def.file_type]

        # sanity check
        for k in ["data_type", "swath_rows", "swath_columns", "rows_per_scan", "fill_value"]:
            if lon_product[k] != lat_product[k]:
                if k == "fill_value" and np.isnan(lon_product[k]) and np.isnan(lat_product[k]):
                    # NaN special case: NaNs can't be compared normally
                    continue
                LOG.error("Longitude and latitude products do not have equal attributes: %s", k)
                raise RuntimeError("Longitude and latitude products do not have equal attributes: %s" % (k,))

        swath_name = lon_product["product_name"] + "_" + lat_product["product_name"]
        swath_definition = containers.SwathDefinition(
            swath_name=swath_name, longitude=lon_product["swath_data"], latitude=lat_product["swath_data"],
            data_type=lon_product["data_type"], swath_rows=lon_product["swath_rows"],
            swath_columns=lon_product["swath_columns"], rows_per_scan=lon_product["swath_rows"],
            source_filenames=sorted(set(lon_file_reader.filepaths + lat_file_reader.filepaths)),
            nadir_resolution=lon_file_reader.nadir_resolution, limb_resolution=lat_file_reader.limb_resolution,
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
        product_def = self.PRODUCTS[product_name]
        file_reader = self.file_readers[product_def.file_type]
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        # TODO: Get the data type from the data or allow the user to specify
        try:
            shape = file_reader.write_var_to_flat_binary(product_def.file_key, filename)
        except (OSError, ValueError):
            LOG.error("Could not extract data from file")
            LOG.debug("Extraction exception: ", exc_info=True)
            raise

        kwargs = {}
        if hasattr(product_def, "channel_index"):
            kwargs["channel_index"] = product_def.channel_index
            # frequencies should be the same for each file (if multiple loaded) so just take the first (0) one
            kwargs["frequency"] = file_reader[FREQ_VAR][0][product_def.channel_index]
        elif hasattr(product_def, "frequency"):
            channel_index = file_reader.get_channel_index(product_def.frequency)
            kwargs["channel_index"] = channel_index
            kwargs["frequency"] = product_def.frequency
        one_swath = containers.SwathProduct(
            product_name=product_name, description=product_def.description, units=product_def.units,
            reader='mirs',
            satellite=file_reader.satellite, instrument=file_reader.instrument,
            begin_time=file_reader.begin_time, end_time=file_reader.end_time,
            swath_definition=swath_definition, fill_value=np.nan,
            swath_rows=shape[0], swath_columns=shape[1], data_type=np.float32, swath_data=filename,
            source_filenames=file_reader.filepaths, data_kind=product_def.data_kind, rows_per_scan=shape[0],
            **kwargs
        )
        return one_swath

    def create_scene(self, products=None, nprocs=1, all_bt_channels=False, **kwargs):
        if nprocs != 1:
            raise NotImplementedError("The MIRS frontend does not support multiple processes yet")
        if products is None:
            if not all_bt_channels:
                LOG.debug("No products specified to frontend, will try to load logical defaults")
                products = self.default_products
            else:
                products = []
        if all_bt_channels:
            products.extend([x for x in self.PRODUCTS.keys() if x.startswith('btemp_') and x != PRODUCT_BT_CHANS])
            products = list(set(products))

        # Do we actually have all of the files needed to create the requested products?
        products = self.loadable_products(products)

        # Needs to be ordered (least-depended product -> most-depended product)
        products_needed = self.PRODUCTS.dependency_ordered_products(products)
        geo_pairs_needed = self.PRODUCTS.geo_pairs_for_products(products_needed, self.available_file_types)
        # both lists below include raw products that need extra processing/masking
        raw_products_needed = (p for p in products_needed if self.PRODUCTS.is_raw(p, geo_is_raw=True))
        secondary_products_needed = [p for p in products_needed if self.PRODUCTS.needs_processing(p)]
        for p in secondary_products_needed:
            if p not in self.secondary_product_functions:
                msg = "Product (secondary or extra processing) required, but not sure how to make it: '%s'" % (p,)
                LOG.error(msg)
                raise ValueError(msg)

        LOG.debug("Extracting data to create the following products:\n\t%s", "\n\t".join(products))
        # final scene object we'll be providing to the caller
        scene = containers.SwathScene()
        # Dictionary of all products created so far (local variable so we don't hold on to any product objects)
        products_created = {}
        swath_definitions = {}

        # Load geographic products - every product needs a geo-product
        for geo_pair_name in geo_pairs_needed:
            lon_product_name = self.GEO_PAIRS[geo_pair_name].lon_product
            lat_product_name = self.GEO_PAIRS[geo_pair_name].lat_product
            # longitude
            if lon_product_name not in products_created:
                one_lon_swath = self.create_raw_swath_object(lon_product_name, None)
                products_created[lon_product_name] = one_lon_swath
                if lon_product_name in products:
                    # only process the geolocation product if the user requested it that way
                    scene[lon_product_name] = one_lon_swath
            else:
                one_lon_swath = products_created[lon_product_name]

            # latitude
            if lat_product_name not in products_created:
                one_lat_swath = self.create_raw_swath_object(lat_product_name, None)
                products_created[lat_product_name] = one_lat_swath
                if lat_product_name in products:
                    # only process the geolocation product if the user requested it that way
                    scene[lat_product_name] = one_lat_swath
            else:
                one_lat_swath = products_created[lat_product_name]

            swath_definitions[geo_pair_name] = self.create_swath_definition(one_lon_swath, one_lat_swath)

        # Create each raw products (products that are loaded directly from the file)
        for product_name in raw_products_needed:
            if product_name in products_created:
                # already created
                continue

            try:
                LOG.info("Creating data product '%s'", product_name)
                swath_def = swath_definitions[self.PRODUCTS[product_name].get_geo_pair_name(self.available_file_types)]
                one_swath = products_created[product_name] = self.create_raw_swath_object(product_name, swath_def)
            except (ValueError, OSError):
                LOG.error("Could not create raw product '%s'", product_name)
                LOG.debug("Debug: ", exc_info=True)
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
            except (ValueError, OSError, KeyError):
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

    def limb_correct_atms_bt(self, product_name, swath_definition, products_created, fill=np.nan):
        bt_product = products_created[product_name]
        if bt_product["instrument"].lower() != "atms":
            LOG.info("Limb Correction will not be applied to non-ATMS BTs")
            return products_created[product_name]

        LOG.info("Starting ATMS Limb Correction...")

        product_def = self.PRODUCTS[product_name]
        deps = product_def.dependencies
        if len(deps) != 2:
            LOG.error("Expected 1 dependencies to create corrected BT product, got %d" % (len(deps),))
            raise ValueError("Expected 1 dependencies to create corrected BT product, got %d" % (len(deps),))

        full_bt_product_name = deps[0]
        full_bt_product = products_created[full_bt_product_name]
        full_bt_data = full_bt_product.get_data_array("swath_data")
        surf_type_name = deps[1]
        surf_type_product = products_created[surf_type_name]
        surf_type_mask = surf_type_product.get_data_array("swath_data")

        bt_data = bt_product.get_data_array("swath_data", mode="r+")
        sea_coeff_results = read_atms_limb_correction_coefficients(LIMB_SEA_FILE)
        new_sea_bt_data = apply_atms_limb_correction(full_bt_data, *sea_coeff_results)
        land_coeff_results = read_atms_limb_correction_coefficients(LIMB_LAND_FILE)
        new_land_bt_data = apply_atms_limb_correction(full_bt_data, *land_coeff_results)
        is_sea = (surf_type_mask == 0)
        bt_data[is_sea] = new_sea_bt_data[bt_product["channel_index"]][is_sea]
        bt_data[~is_sea] = new_land_bt_data[bt_product["channel_index"]][~is_sea]

        # return the same original swath object since we modified the data in place
        return products_created[product_name]


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    # parser.set_defaults(remap_method="ewa", fornav_D=100, fornav_d=1, maximum_weight_mode=True)
    parser.set_defaults(remap_method="ewa", fornav_D=100, fornav_d=1)

    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                        help="List available frontend products")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    group.add_argument("--bt-channels", dest="all_bt_channels", action='store_true',
                       help="Add all BT channels to the list of requested products")
    group.add_argument("-p", "--products", dest="products", nargs="*", default=None,
                       help="Specify frontend products to process")
    return ["Frontend Initialization", "Frontend Swath Extraction"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, setup_logging, create_exc_handler
    parser = create_basic_parser(description="Extract image data from MIRS files and print JSON scene dictionary")
    subgroup_titles = add_frontend_argument_groups(parser)
    parser.add_argument('-f', dest='data_files', nargs="+", default=[],
                        help="List of data files and directories to get extract data from")
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
