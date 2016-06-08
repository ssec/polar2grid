#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2012-2016 Space Science and Engineering Center (SSEC),
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
# Written by David Hoese    June 2016
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""The SCMI AWIPS backend is used to create AWIPS compatible tiled NetCDF
files. The Advanced Weather Interactive Processing System (AWIPS) is a
program used by the United States National Weather Service (NWS) and others
to view
different forms of weather imagery. Sectorized Cloud and Moisture Imagery
(SCMI) is a netcdf format accepted by AWIPS to store one image broken up
in to one or more "tiles". Once AWIPS is configured for specific products
the SCMI NetCDF backend can be used to provide compatible products to the
system. The files created by this backend are compatible with AWIPS II (AWIPS I is no
longer supported).

The AWIPS NetCDF backend takes remapped binary image data and creates an
AWIPS-compatible NetCDF 4 file.
Both the AWIPS backend and the AWIPS client must be configured to handle certain
products over certain grids

 .. warning::

     The SCMI backend does not default to using any grid. Therefore, it is recommended to specify
     one or more grids for remapping by using the `-g` flag.

:author:       David Hoese (davidh)
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012-2016 University of Wisconsin SSEC. All rights reserved.
:date:         June 2016
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

from polar2grid.core import roles
from polar2grid.core.rescale import Rescaler, DEFAULT_RCONFIG
from polar2grid.core.dtype import clip_to_data_type, DTYPE_UINT8
from .awips_config import AWIPS2ConfigReader, CONFIG_FILE as DEFAULT_AWIPS_CONFIG, NoSectionError
from netCDF4 import Dataset
import numpy as np

import os
import re
import sys
import logging
import calendar
import math
from datetime import datetime, timedelta
from collections import namedtuple

LOG = logging.getLogger(__name__)

fgf_yxmb = namedtuple('fgf', ['y', 'x', 'my', 'mx', 'by', 'bx'])

def native_FACOFF(nav):
    return dict(CFAC=nav.CFAC, LFAC=nav.LFAC, COFF=nav.COFF, LOFF=nav.LOFF)
#
# def lookup_FACOFF(band, factor, existing):
#     if factor==1:
#         LOG.info("using pre-existing FAC/OFF from scene")
#         return native_FACOFF(existing)
#     # check that we actually have what are probably the correct values!
#     native = FACOFF.get(NATIVE_REZ[band], None)
#     if not FACOFF_matches(native, existing):
#         LOG.error("could not match FAC/OFF parameters to support data reduction. cannot assign without a donor file (use -n option)!")
#         return None
#     # okay we have confidence in the LUT! figure out what effective nav values unnamed-people expect
#     LOG.info("using table lookup FAC/OFF values")
#     key = NATIVE_REZ[band] * factor
#     return FACOFF.get(key, None)

SCMI_GLOBAL_ATT=dict(
    product_tile_height=None,  # 1100,
    projection=None,
    periodicity=10,
    tile_center_longitude=None,  # 88.0022078322,
    satellite_altitude=None,  # 35785.863,
    satellite_id=None,  # GOES-H8
    tile_column_offset=None,  # 2750,
    pixel_y_size=None,  # km
    product_center_latitude=None,
    start_date_time=None,  # 2015181030000,  # %Y%j%H%M%S
    product_columns=None,  # 11000,
    title="Sectorized Cloud and Moisture Full Disk Imagery",
    abi_mode=1,
    pixel_x_size=None,  # km
    product_name=None,  # "HFD-010-B11-M1C01",
    satellite_longitude=None,  # 140.7,
    source_spatial_resolution=None,  # km
    central_wavelength=None,  # 0.47063,
    number_product_tiles=None,  # 76,
    bit_depth=None,
    product_rows=None,  # 11000,
    satellite_latitude=0.0,
    ICD_version="SE-08_7034704_GS_AWIPS_Ext_ICD_RevB.3",
    source_scene=None,  # FIXME: handle regionals
    production_location=None,  # "MSC",
    tile_center_latitude=None,  # 62.41709885,
    Conventions="CF-1.6",
    channel_id=None,  # 1,
    product_center_longitude=None,  # 140.7,
    product_tile_width=None,  # 1375,
    request_spatial_resolution=None,
    tile_row_offset=None,  # 0,
)

SCMI_Y_ATT=dict(
    units="microradian",
    standard_name="projection_y_coordinate",
    scale_factor=None,
    add_offset=None
)

SCMI_X_ATT=dict(
    units="microradian",
    standard_name="projection_x_coordinate",
    scale_factor=None,
    add_offset=None
)

SCMI_DATA_ATT=dict(
    grid_mapping="fixedgrid_projection",
    scale_factor=None,  # 0.000588235294901,
    standard_name=None,  # toa_bidirectional_reflectance,
    add_offset=None,  #-0.011764705898,
    valid_min=None,
    units=1,
    valid_max=None,  # 2047 for scaled ints
)

SCMI_FGF_ATT=dict(
    latitude_of_projection_origin=0.0,
    perspective_point_height=None,  # 35785863.0,
    semi_minor=None,  # 6356752.3,
    # semi_minor_axis=6356752.3,  # CF
    longitude_of_projection_origin=None, # 140.7,
    grid_mapping_name='geostationary',
    semi_major=None,  # 6378137.0,
    # semi_major_axis=6378137.0,  # CF
    sweep_angle_axis="x",
)

def _ahi_bit_depth(channel):
    return AHI_BIT_DEPTH[channel - 1]

# extracted with
# for c in `seq 1 16`; do
#   ccc=$(printf '%02d' c);
#   fn=$(find . -name "*C${ccc}*.nc" -type f |head -1);
#   cat <(ncdump -h $fn |grep Sectorized_CMI: |sed -E 's/^.*?://g' |grep -v FillValue) \
#       <(echo "print '(', $c, ',', add_offset+scale_factor*valid_min, ',', add_offset + scale_factor*valid_max, ')'") |python;
# done
AHI_SCMI_CHANNEL_RANGES = [
    ( 1 , -0.011764705898 , 1.19235294276 ),
    ( 2 , -0.011764705603 , 1.19235291287 ),
    ( 3 , -0.0117647057594 , 1.19235292871 ),
    ( 4 , -0.0117647058027 , 1.1923529331 ),
    ( 5 , -0.0117647058528 , 1.19235293818 ),
    ( 6 , -0.0117647058774 , 1.19235294068 ),
    ( 7 , 99.0 , 400.981567383 ),
    ( 8 , 69.0 , 321.876464844 ),
    ( 9 , 69.0 , 321.876464844 ),
    ( 10 , 69.0 , 320.938476562 ),
    ( 11 , 69.0 , 330.936035156 ),
    ( 12 , 69.0 , 330.936035156 ),
    ( 13 , 69.0 , 331.935791016 ),
    ( 14 , 69.0 , 331.935791016 ),
    ( 15 , 70.0 , 331.936035156 ),
    ( 16 , 70.0 , 332.871582031 )
]

AHI_BIT_DEPTH = [11, 11, 11, 11,
                 11, 11, 14, 11,
                 11, 12, 12, 12,
                 12, 12, 12, 11]

AHI_CENTRAL_WAVELENGTH = [
    0.47, 0.51, 0.64, 0.86,
    1.61, 2.26, 3.89, 6.24,
    6.94, 7.35, 8.59, 9.64,
    10.41, 11.24, 12.38, 13.28]

# zy_xxxx-rrr-Bnn-MnCnn-Tnnn_Gnn_sYYYYDDDhhmmss _cYYYYDDDhhmmss.nc
# OR_HFD-020-B14-M1C07-T055_GH8_s2015181030000_c2015181031543
# ref Table 3.3.4.1.2-1 Sectorized CMI File Naming Convention Fields on NOAA VLAB wiki
FMT_SCMI_NAME="{environment:1s}{data_type:1s}_{region:s}-{resolution:3s}-B{bits:02d}-M{mode:1d}C{channel:02d}-T{tile:03d}_G{satellite:2s}_s{scene_time:13s}_c{creation_time:13s}.nc"


def scmi_product(
        region='HFD',     # HFD / EFD / WFD / ECONUS / WCONUS / HIREGI / PRREG / AKREGI
        resolution='040', # technically may not be valid to have 4km?
        bits=0,           # 8..14
        mode=1,           # ABI mode
        channel=0,
        **kwargs):       # channel number, 1..16
    bits = _ahi_bit_depth(channel) if bits==0 else bits
    return "{region:s}-{resolution:3s}-B{bits:02d}-M{mode:1d}C{channel:02d}".format(**locals())


def scmi_filename(
        environment='D',  # Integrated Test, Development, Operational
        data_type='T',    # Real-time Playback Simulated Test
        region='HFD',     # HFD / EFD / WFD / ECONUS / WCONUS / HIREGI / PRREG / AKREGI
        resolution='040', # technically may not be valid to have 4km?
        bits=0,           # 8..14
        mode=1,           # ABI mode
        channel=0,        # channel number, 1..16
        tile=None,           # 001..### upper left to lower right
        satellite='H8',   # 16, 17, ... H8
        scene_time=None,  # datetime object
        creation_time=None): # now, datetime object
    scene_time = scene_time.strftime('%Y%j%H%M%S')
    if creation_time is None:
        creation_time = datetime.utcnow()
    creation_time = creation_time.strftime('%Y%j%H%M%S')
    assert(1<=channel<=16)
    bits = _ahi_bit_depth(channel) if bits==0 else bits
    return FMT_SCMI_NAME.format(**locals())


RESOLUTION_FROM_WIDTH = {
    2750: 40,
    5500: 20,
    11000: 10,
    22000: 5
}


# scale factors and add offsets for variables at different resolutions, from inspection
XY_SF_AO = {
    (40, 'y'): (-112.0, 153944.0),  # 4km extrapolated from 20,10,5 as m,b=-0.5,15400
    (40, 'x'): (112.0, -153944.0),
    (20, 'y'): (-56.0, 153972.0),
    (20, 'x'): (56.0, -153972.0),
    (10, 'y'): (-28.0, 153986.0),
    (10, 'x'): (28.0, -153986.0),
    (5, 'y'): (-14.0, 153993.0),
    (5, 'x'): (14.0, -153993.0)
}

# map 0..32767 to viable content
# IMG_SF_AO = {
#     'brightness_temp': (200.0/32767.0, 150.0), # 150K .. 350K
#     'albedo': (2.0/32767.0, -0.5)  # -0.5 .. 1.5
# }
IMG_SF_AO = dict(
    (channel, ((valid_max-valid_min)/float(2**bit_depth - 1), valid_min)) for ((channel, valid_min, valid_max), bit_depth) in zip(AHI_SCMI_CHANNEL_RANGES, AHI_BIT_DEPTH)
)

HCAST_DEFAULT_NAV = dict(
    r_eq = 6378.1690,   # km
    r_pol = 6356.5838,
    sat_height = 35785.831,
)

STANDARD_NAMES = {
    'albedo': 'toa_bidirectional_reflectance',
    'brightness_temp': 'brightness_temperature'
}

# FIXME: invalid data is not getting proper sentinel values from libHimawari.HCastFile.
# For now just focus on decent valid ranges (courtesy Jordan Gerth)
# Changed to integer unscaled values (see IMG_SF_AO)
# VALID_RANGE = {
#     'albedo': (0, 32767),  # (-0.012, 1.192),
#     'brightness_temp': (0, 32767)  # (164.15, 328.15)
# }

class AttributeHelper(object):
    """
    helper object which wraps around a HimawariScene to provide SCMI attributes
    """
    tile_count = (0,0)  # ny, nx
    hsd = None
    offset = (0,0)  # ty, tx tile number
    tile_shape = (0,0)  # wy, wx height and width of tile in pixels
    scene_shape = (0,0)  # sy, sx height and width of scene in pixels

    def __init__(self, hsd, offset, tile_count, scene_shape):
        self.hsd = hsd
        self.offset = offset
        self.tile_count = tile_count
        self.scene_shape = scene_shape
        self.tile_shape = (int(scene_shape[0] / tile_count[0]), int(scene_shape[1] / tile_count[1]))

    def apply_attributes(self, nc, table, prefix=''):
        """
        apply fixed attributes, or look up attributes needed and apply them
        """
        for name, value in table.items():
            if name in nc.ncattrs():
                LOG.debug('already have a value for %s' % name)
                continue
            if value is not None:
                setattr(nc, name, value)
            else:
                funcname = prefix+name  # _global_ + product_tile_height
                func = getattr(self, funcname, None)
                if func is not None:
                    value = func()
                    if value is not None:
                        setattr(nc, name, value)
                else:
                    LOG.info('no routine matching %s' % funcname)

    def _scene_time(self):
        # # FIXME this is what we want:
        # # timeline_hhmm = time(int(self.hsd.metadata.observation_timeline/100), int(self.hsd.metadata.observation_timeline%100))
        # # mot = self.hsd.metadata.start_time
        # # timeline_yyyymmdd = datetime(mot.year, mot.month, mot.day, mot.hour, mot.minute, mot.second)
        # # timeline_time = timeline_yyyymmdd  # but we use this instead
        # # return timeline_time
        # # but observation_time not provided by HCAST data so we just use start_time; so instead
        # # FIXME FUGLYSAURUS REX only to be used on HCAST not HSD, let's get some metadata from the filename... T^T
        # fn = os.path.split(self.hsd.path)[-1]
        # # e.g. IMG_DK01B07_201507241500
        # ymdhm, = re.findall(r'_(2\d{11})', fn) # strip out 201507241500
        # return datetime.strptime(ymdhm, '%Y%m%d%H%M')
        return self.hsd.metadata.start_time

    def _tile_number(self):
        # e.g.
        # 001 002 003 004
        # 005 006 ...
        return self.offset[0] * self.tile_count[1] + self.offset[1] + 1

    def _filename(self):
        satellite = self.hsd.gridded_product["satellite"].upper()
        return scmi_filename(satellite=satellite,
                             channel=self.hsd.metadata.band, scene_time=self._scene_time(), tile=self._tile_number())

    def _product_name(self):
        grid_def = self.hsd.gridded_product["grid_definition"]
        if "himawari" in grid_def["grid_name"]:
            region = "HFD"
        elif grid_def.proj4_dict["proj"] == "lcc":
            # FIXME: We need to actually know what region it is
            region = "ECONUS"
        else:
            region = "HFD"

        # (region='HFD',     # HFD / EFD / WFD / ECONUS / WCONUS / HIREGI / PRREG / AKREGI
        # resolution='040', # technically may not be valid to have 4km?
        # bits=0,           # 8..14
        # mode=1,           # ABI mode
        # channel=0,
        # **kwargs):       # channel number, 1..16
        return scmi_product(channel=self.hsd.metadata.band, scene_time=self._scene_time(),
                            region=region)

    def _global_product_tile_height(self):  # = None, # 1100,
        return self.tile_shape[0]

    def _global_product_tile_width(self):  # = None, # 1100,
        return self.tile_shape[1]

    def _global_number_product_tiles(self):
        return self.tile_count[0] * self.tile_count[1]

    def _global_satellite_id(self):
        return self.hsd.metadata.satellite_id

    @property
    def _file_nav_is_incomplete(self):
        n = self.hsd.gridded_product["grid_definition"]
        b = n.proj4_dict["b"]
        inc = np.isnan(b) or b <= 0
        if inc:
            LOG.warning('WARNING: incomplete nav, assuming HCAST H8 AHI ')
        return inc

    def _tile_center(self): # = None, # 88.0022078322,
        # calculate center longitude of tile
        # FIXME: resolve whether we need half-pixel offset
        row = self._global_tile_row_offset() + self.tile_shape[0]/2
        col = self._global_tile_column_offset() + self.tile_shape[1]/2
        return self.hsd.gridded_product["grid_definition"].get_lonlat(row, col)

    def _global_tile_center_longitude(self): # = None, # 88.0022078322,
        return np.float32(self._tile_center()[0])

    def _global_product_rows(self):
        return self.scene_shape[0]

    def _global_product_columns(self):
        return self.scene_shape[1]

    def _global_tile_row_offset(self):
        return self.offset[0] * self.tile_shape[0]

    def _global_tile_column_offset(self):
        return self.offset[1] * self.tile_shape[1]

    def _global_tile_center_latitude(self): # = None, # 88.0022078322,
        return np.float32(self._tile_center()[1])

    def _global_bit_depth(self):
        band = self.hsd.metadata.band
        return _ahi_bit_depth(band)

    def _global_satellite_altitude(self):
        """ABI grid based satellite altitude used by L1b processing.

        Returns
        -------
        float or None
            Height of satellite in meters or None
        """
        return self.hsd.gridded_product["grid_definition"].proj4_dict.get("h")

    def _global_satellite_longitude(self): # = None, # 35785.863,
        proj4_dict = self.hsd.gridded_product["grid_definition"].proj4_dict
        if "h" in proj4_dict:
            return np.float32(proj4_dict["lon_0"])  # float32 needed?
        else:
            return None

    def _data_standard_name(self):
        return STANDARD_NAMES[self.hsd.kind]

    def _global_product_name(self):
        return self._product_name()

    def _global_channel_id(self):
        return self.hsd.metadata.band

    def _global_pixel_x_size(self):
        # rez = RESOLUTION_FROM_WIDTH[self.hsd.extents[1]]
        # return float(rez)/10.0
        return self.hsd.metadata.columns_res_meters / 1000.

    _global_request_spatial_resolution = _global_source_spatial_resolution = _global_pixel_y_size = _global_pixel_x_size

    def _global_start_date_time(self):
        # FIXME this is what we want for HSD:
        # meta = self.hsd.metadata
        # when = meta.start_time
        # when = datetime(when.year, when.month, when.day, when.hour, when.minute, when.second, when.microsecond)
        # return when.strftime('%Y%m%d') + '%04d' % meta.observation_timeline + '00'
        when = self._scene_time()
        return when.strftime('%Y%j%H%M%S')

    def _global_product_center_longitude(self):
        grid_def = self.hsd.gridded_product["grid_definition"]
        return grid_def.lonlat_center[0]

    def _global_product_center_latitude(self):
        grid_def = self.hsd.gridded_product["grid_definition"]
        return grid_def.lonlat_center[1]

    def _data_valid_min(self):
        return 0

    def _data_valid_max(self):
        bit_depth = _ahi_bit_depth(self.hsd.metadata.band)
        return 2**bit_depth - 1


    def _global_production_location(self):
        org = os.environ.get('ORGANIZATION', None)
        if org is not None:
            return org
        else:
            LOG.warning('environment ORGANIZATION not set for .production_location attribute, using hostname')
            import socket
            return socket.gethostname()  # FUTURE: something more correct but this will do for now


class SCMI_writer(object):
    """
    Write a basic NetCDF4 file with header data mapped to global attributes, and BT/ALB/RAD variables
    FUTURE: optionally add time dimension (CF)
    FUTURE: optionally add zenith and azimuth angles

    """
    _nc = None
    _shape = None
    _offset = None  # offset within source file
    _kind = None  # 'albedo', 'brightness_temp'
    _band = None
    _include_geo = False
    _include_fgf = True
    _include_rad = False
    _fill_value = 0.0
    row_dim_name, col_dim_name = 'y', 'x'
    y_var_name, x_var_name = 'y', 'x'
    bt_var_name = 'Sectorized_CMI'
    rad_var_name = None
    alb_var_name = 'Sectorized_CMI'
    lat_var_name = 'latitude'
    lon_var_name = 'longitude'
    line_time_var_name = 'line_time_offset'
    bt = None
    rad = None
    alb = None
    lat = None
    lon = None
    fgf_y = None
    fgf_x = None
    line_time = None
    projection = None
    fmissing = np.float32(-999.0)
    missing = np.int16(-1.0)
    imissing = np.uint16(32767)


    def create_dimensions(self):
        # Create Dimensions
        lines, columns = self._shape
        _nc = self._nc
        _nc.createDimension(self.row_dim_name, lines)
        _nc.createDimension(self.col_dim_name, columns)

    def create_variables(self, scale_factor=None, add_offset=None):
        geo_coords = "%s %s" % (self.lat_var_name, self.lon_var_name)
        fgf_coords = "%s %s" % (self.y_var_name, self.x_var_name)

        if self._include_rad:
            self.rad = self._nc.createVariable(self.rad_var_name, 'u2', dimensions=(self.row_dim_name, self.col_dim_name), fill_value=self.imissing)
            self.rad.coordinates = geo_coords if self._include_geo else fgf_coords
            self.rad.units = 'W m-2 sr-1 um-1'
        else:
            if self._kind == 'brightness_temp':
                self.bt = self._nc.createVariable(self.bt_var_name, 'i2', dimensions=(self.row_dim_name, self.col_dim_name), fill_value=self.missing)
                self.bt.coordinates = geo_coords if self._include_geo else fgf_coords
                self.bt.units = 'kelvin'
                dv = self.bt
            elif self._kind == 'albedo':
                self.alb = self._nc.createVariable(self.alb_var_name, 'i2', dimensions=(self.row_dim_name, self.col_dim_name), fill_value=self.missing)
                self.alb.coordinates = geo_coords if self._include_geo else fgf_coords
                self.alb.units = '1'
                dv = self.alb

            dv.scale_factor = scale_factor
            dv.add_offset = add_offset
            self.helper.apply_attributes(dv, SCMI_DATA_ATT, '_data_')

        if self._include_fgf:
            self.fgf_y = self._nc.createVariable(self.y_var_name, 'i2', dimensions=(self.row_dim_name,))

            self.fgf_x = self._nc.createVariable(self.x_var_name, 'i2', dimensions=(self.col_dim_name,))

            # FUTURE: include compatibility 'y' and 'x', though there's a nonlinear transformation from CGMS to GOES y/x angles.
            # This requires that the scale_factor and add_offset are 1.0 and 0.0 respectively,
            # which violates some uses that use the line/column unscaled form expected by some applications.

        if self._include_geo:
            self.lat = self._nc.createVariable(self.lat_var_name, 'f4', dimensions=(self.row_dim_name, self.col_dim_name), fill_value=self.fmissing)
            self.lat.units = 'degrees_north'
            self.lon = self._nc.createVariable(self.lon_var_name, 'f4', dimensions=(self.row_dim_name, self.col_dim_name), fill_value=self.fmissing)
            self.lon.units = 'degrees_east'
        self.line_time = None # self._nc.createVariable(self.line_time_var_name, 'f8', dimensions=(self.row_dim_name,))
        # self.line_time.units = 'seconds POSIX'
        # self.line_time.long_name = "POSIX epoch seconds elapsed since base_time for image line"

    def __init__(self, filename, resolution, offset, shape, kind, band, include_geo=False, include_fgf=True, include_rad=True, helper=None):
        self._nc = Dataset(filename, 'w')
        self._resolution = resolution
        self._shape = shape
        self._offset = offset
        self._kind = kind
        self._include_geo = include_geo
        self._include_rad = include_rad
        self._include_fgf = include_fgf
        self._band = band
        self.rad_var_name = "RAD" # "ABI_Scaled_b%02d" % band if (band not in BAND_NAME_OVERRIDES) else BAND_NAME_OVERRIDES[band]
        self.helper = helper

    def set_geo(self, lat, lon):
        if self.lat is not None:
            self.lat[:,:] = np.ma.fix_invalid(lat, fill_value=self.missing)
        if self.lon is not None:
            self.lon[:,:] = np.ma.fix_invalid(lon, fill_value=self.missing)

    def set_fgf(self, x, mx, bx, y, my, by, units='meters', downsample_factor=1):
        # assign values before scale factors to avoid implicit scale reversal
        LOG.debug('y variable shape is {}'.format(self.fgf_y.shape))
        self.fgf_y.scale_factor = np.float32(my * float(downsample_factor))
        self.fgf_y.add_offset = np.float32(by)
        self.fgf_y.units = units
        self.fgf_y.standard_name = "projection_y_coordinate"
        self.fgf_y.long_name = "CGMS N/S fixed grid viewing angle (not interchangeable with GOES y)"
        self.fgf_y[:] = y

        self.fgf_x.scale_factor = np.float32(mx * float(downsample_factor))
        self.fgf_x.add_offset = np.float32(bx)
        self.fgf_x.units = units
        self.fgf_x.standard_name = "projection_x_coordinate"
        self.fgf_x.long_name = "CGMS E/W fixed grid viewing angle (not interchangeable with GOES x)"
        self.fgf_x[:] = x

    def set_rad_attrs(self, cal):
        self.rad.scale_factor = cal.rad_m
        self.rad.add_offset = cal.rad_b
        self.rad.c = cal.c
        self.rad.h = cal.h
        self.rad.k = cal.k
        if self._kind == 'albedo':
            self.rad.cprime = cal.bt_c0_or_albedo_cprime
        else:
            self.rad.bt_c0 = cal.bt_c0_or_albedo_cprime
            self.rad.bt_c1 = cal.bt_c1
            self.rad.bt_c2 = cal.bt_c2

    def set_image_data(self, counts=None, bt=None, alb=None):
        if counts is not None:
            LOG.info('writing radiance counts')
            # self.rad[:,:] = np.ma.fix_invalid(np.require(rad, dtype=np.float32), fill_value=self.missing)
            # missing values are being presented as nans
            # having masked the missing data, now let's replace them with imissing values
            assert(not np.any(counts<0.0))
            assert(not np.any(counts>=self.imissing))
            # we apply rounding in case the counts have been averaged down to lower resolution
            # using HimawariResample.
            rad = np.round(counts)
            # note that HimawariScene is returning masked arrays, typically NaNs as fill!
            rad = np.ma.fix_invalid(rad, fill_value=self.imissing)
            # and then convert to uint16 for writing as scaled integer
            rad = np.require(rad, dtype=np.int16)
            self.rad[:,:] = rad
            del rad
        if bt is not None and self.bt is not None:
            LOG.info('writing BT')
            # note: autoscaling will be applied to make int16
            # self.bt[:,:] = np.ma.fix_invalid(np.require(bt, dtype=np.float32), fill_value=self.missing)
            assert(hasattr(bt, 'mask'))
            self.bt[:,:] = np.require(bt.filled(self._fill_value), dtype=np.float32)
        if alb is not None and self.alb is not None:
            LOG.info('writing albedo')
            # note: autoscaling will be applied to make int16
            # self.alb[:,:] = np.ma.fix_invalid(np.require(alb, dtype=np.float32), fill_value=self.fmissing) # FUTURE: scaled ints
            assert(hasattr(alb, 'mask'))
            self.alb[:, :] = np.require(alb.filled(self._fill_value), dtype=np.float32)


    def set_projection_attrs(self, grid_def):
        """
        assign projection attributes per GRB standard
        """
        proj4_info = grid_def.proj4_dict
        if proj4_info["proj"] == "geos":
            p = self.projection = self._nc.createVariable("fixedgrid_projection", 'i4')
            if self.alb:
                self.alb.grid_mapping = "fixedgrid_projection"
            if self.bt:
                self.bt.grid_mapping = "fixedgrid_projection"
            p.short_name = grid_def["grid_name"]
            p.grid_mapping_name = "geostationary"
            # p.long_name = "Himawari Imagery Projection"
            p.sweep_angle_axis = proj4_info["sweep"]
            # Projection.units = "radians"
            # calculate invflat 'f' such that rpol = req - req/invflat
            a = proj4_info["a"]
            b = proj4_info["b"]
            h = proj4_info["h"]
            lon_0 = proj4_info["lon_0"]
            if "f" not in proj4_info:
                try:
                    f = 1.0 / (1.0 - b/a)
                except ZeroDivisionError as hcast_probably_did_this:
                    f = 0.0
            else:
                f = proj4_info["f"]

            if np.isnan(f) or f == 0.0:
                LOG.warning('invalid projection parameters, hello HimawariCast - using hardcoded values from Harris sample')
                p.semi_major = p.semi_major_axis = a = HCAST_DEFAULT_NAV['r_eq'] * 1e3  # m
                p.semi_minor = p.semi_minor_axis = b = HCAST_DEFAULT_NAV['r_pol'] * 1e3
                f = 1.0 / (1.0 - b/a)
                # Projection.inverse_flattening = np.float32(f) # 298.2572f ;
                p.perspective_point_height = HCAST_DEFAULT_NAV['sat_height'] * 1e3
                p.description = "HimawariCast nominal projection values"
            else:
                p.semi_major = a * 1e3 # 6378.137f ;
                p.semi_minor = b * 1e3  # convert to meters
                # Projection.inverse_flattening = np.float32(f) # 298.2572f ;
                p.perspective_point_height = h

            # Projection.latitude_of_projection_origin = np.float32(0.0) ;
            p.longitude_of_projection_origin = np.float32(lon_0)  # is the float32 needed?
            self.helper.apply_attributes(p, SCMI_FGF_ATT, '_proj_')  # TODO: Generalize

            # Set globals based on projection
            self._nc.projection = "Fixed_Grid"
            # FIXME: Handle other regions
            self._nc.source_scene = "Full Disk"
        elif proj4_info["proj"] == "lcc":
            p = self.projection = self._nc.createVariable("lambert_projection", 'i4')
            if self.alb:
                self.alb.grid_mapping = "lambert_projection"
            if self.bt:
                self.bt.grid_mapping = "lambert_projection"
            p.short_name = grid_def["grid_name"]
            p.grid_mapping_name = "lambert_conformal_conic"
            if proj4_info["lat_0"] != proj4_info["lat_1"]:
                raise NotImplementedError("Unsure how to handle two standard parallels for LCC projection")
            p.standard_parallel = proj4_info["lat_0"]  # How do we specify two standard parallels?
            p.longitude_of_central_meridian = proj4_info["lon_0"]
            p.latitude_of_projection_origion = proj4_info["lat_0"]  # XXX: lat_1?
            p.false_easting = proj4_info.get("x", 0.0)
            p.false_northing = proj4_info.get("y", 0.0)
            p.semi_major = proj4_info["a"]
            p.semi_minor = proj4_info["b"]

            # Set globals based on projection
            self._nc.projection = "Lambert Conformal"
            # FIXME: This is an assumption
            self._nc.source_scene = "CONUS"

    def set_global_attrs(self, meta, nav):
        # self._nc.WMO_SAT_ID = meta.wmo_sat_id
        # self._nc.start_time_unix = meta.start_time.unix_time
        # self._nc.end_time_unix = meta.end_time.unix_time
        # self._nc.observation_timeline = meta.observation_timeline
        self._nc.central_wavelength = AHI_CENTRAL_WAVELENGTH[meta.band - 1]  # meta.central_wavelength * 1e6  # meters to microns
        # self._nc.distance_from_earth_center_to_satellite = nav.distance_from_earth_center_to_satellite
        self._nc.creator = "UW SSEC libHimawari scmi.py"
        self._nc.creation_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        self.helper.apply_attributes(self._nc, SCMI_GLOBAL_ATT, '_global_')

    # def set_time_offsets(self, start_time, time_offsets):
    #     self.line_time.base_time = start_time
    #     self.line_time[:] = time_offsets

    def close(self):
        self._nc.sync()
        self._nc.close()
        self._nc = None


class _AttrDict(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class FakeHimawariScene(object):
    def __init__(self, gridded_product):
        self.gridded_product = gridded_product

    @property
    def kind(self):
        return {
            'reflectance': 'albedo',
            'brightness_temperature': 'brightness_temp',
        }.get(self.gridded_product["data_kind"])

    @property
    def metadata(self):
        return _AttrDict(
            lines=self.gridded_product["grid_definition"]["height"],
            columns=self.gridded_product["grid_definition"]["width"],
            lines_res_meters=self.gridded_product["grid_definition"]["cell_height"],
            columns_res_meters=self.gridded_product["grid_definition"]["cell_width"],
            start_time=self.gridded_product["begin_time"] + timedelta(minutes=int(os.environ.get("DEBUG_TIME_SHIFT", 0))),  # FIXME
            # FIXME:
            band=2,
            band_type=self.kind,
            satellite_id="{}-{}".format(self.gridded_product["satellite"].upper(), self.gridded_product["instrument"].upper())
        )

    # def geo(self, line_offset, column_offset, lines, columns, **args):
    #     lons, lats = self.gridded_product["grid_definition"].get_geolocation_arrays()
    #     return _AttrDict(
    #         longitude=lons[line_offset:line_offset+lines, column_offset:column_offset+columns],
    #         latitude=lats[line_offset:line_offset+lines, column_offset:column_offset+columns]
    #     )

    # @property
    # def fgf(self):
    #     x, y = self.gridded_product["grid_definition"].get_xy_arrays()
    #     x = x[0].squeeze()  # all rows should have the same coordinates
    #     y = y[:, 0].squeeze()  # all columns should have the same coordinates
    #     # scale the X and Y arrays to fit in the file for 16-bit integers
    #     bx = x.min()
    #     mx = (x.max() - x.min()) / (2**16 - 1)
    #     x -= bx
    #     x /= mx
    #     by = y.min()
    #     my = (y.max() - y.min()) / (2**16 - 1)
    #     y -= by
    #     y /= my
    #     return fgf_yxmb(x=x, y=y, mx=mx, bx=bx, my=my, by=by)


class Backend(roles.BackendRole):
    def __init__(self, backend_configs=None, rescale_configs=None, **kwargs):
        backend_configs = backend_configs or [DEFAULT_AWIPS_CONFIG]
        rescale_configs = rescale_configs or [DEFAULT_RCONFIG]
        self.awips_config_reader = AWIPS2ConfigReader(*backend_configs)
        # self.rescaler = Rescaler(*rescale_configs, **kwargs)
        super(Backend, self).__init__(**kwargs)

    @property
    def known_grids(self):
        return None

    def create_output_from_product(self, gridded_product, tile_count=(1, 1), **kwargs):
        data_type = DTYPE_UINT8
        inc_by_one = False
        fill_value = 0
        grid_def = gridded_product["grid_definition"]

        try:
            awips_info = self.awips_config_reader.get_product_info(gridded_product)
        except NoSectionError as e:
            LOG.error("Could not get information on product from backend configuration file")
            # NoSectionError is not a "StandardError" so it won't be caught normally
            raise RuntimeError(e.message)

        # try:
        #     awips_info.update(self.awips_config_reader.get_grid_info(grid_def))
        # except NoSectionError as e:
        #     LOG.error("Could not get information on grid from backend configuration file")
        #     # NoSectionError is not a "StandardError" so it won't be caught normally
        #     raise RuntimeError(e.message)

        if "filename_scheme" in awips_info:
            # Let individual products have special names if needed (mostly for weird product naming)
            fn_format = awips_info.pop("filename_scheme")
        else:
            fn_format = self.awips_config_reader.get_filename_format()

        output_filename = self.create_output_filename(fn_format,
                                                      grid_name=grid_def["grid_name"],
                                                      rows=grid_def["height"],
                                                      columns=grid_def["width"],
                                                      **gridded_product)

        if os.path.isfile(output_filename):
            if not self.overwrite_existing:
                LOG.error("AWIPS file already exists: %s", output_filename)
                raise RuntimeError("AWIPS file already exists: %s" % (output_filename,))
            else:
                LOG.warning("AWIPS file already exists, will overwrite: %s", output_filename)

        # Create the netcdf file
        try:
            LOG.debug("Scaling %s data to fit in netcdf file...", gridded_product["product_name"])
            # data = self.rescaler.rescale_product(gridded_product, data_type,
            #                                      inc_by_one=inc_by_one, fill_value=fill_value)
            data = gridded_product.get_data_array()
            mask = gridded_product.get_data_mask()
            data = np.ma.masked_array(data, mask=mask)

            LOG.info("Writing product %s to AWIPS NetCDF file", gridded_product["product_name"])
            # create_awips2_netcdf3(output_filename, data, gridded_product["begin_time"], **awips_info)
            # nav = _AttrDict(
            #     earth_equatorial_radius=gridded_product["grid_definition"].proj4_dict["a"],
            #     earth_polar_radius=gridded_product["grid_definition"].proj4_dict["b"],
            #     sub_lon=gridded_product["grid_definition"].proj4_dict["lon_0"],
            #     distance_from_earth_center_to_virtual_satellite=gridded_product["grid_definition"].proj4_dict["h"],
            # )
            fake_scene = FakeHimawariScene(gridded_product)
            tile_shape = (int(data.shape[0] / tile_count[0]), int(data.shape[1] / tile_count[1]))
            tmp_tile = np.ma.zeros(tile_shape, dtype=np.float32)
            tmp_tile.set_fill_value(0)

            # Get X/Y
            # Since our tiles may go over the edge of the original "grid" we
            # need to make sure we calculate X/Y to the edge of all of the tiles
            imaginary_data_size = (tile_shape[0] * tile_count[0], tile_shape[1] * tile_count[1])
            imaginary_grid_def = gridded_product["grid_definition"].copy()
            imaginary_grid_def["height"] = imaginary_data_size[0]
            imaginary_grid_def["width"] = imaginary_data_size[1]
            proj4_info = grid_def.proj4_dict
            if proj4_info["proj"] == "geos":
                xy_units = "microradian"
                micro_factor = 1e6
            else:
                xy_units = "meters"
                micro_factor = 1

            x, y = imaginary_grid_def.get_xy_arrays()
            x = x[0].squeeze()  # all rows should have the same coordinates
            y = y[:, 0].squeeze()  # all columns should have the same coordinates
            # scale the X and Y arrays to fit in the file for 16-bit integers
            bx = x.min()
            mx = (x.max() - x.min()) / (2**16 - 1)
            bx *= micro_factor
            mx *= micro_factor
            # x -= bx
            # x /= mx
            by = y.min()
            my = (y.max() - y.min()) / (2**16 - 1)
            by *= micro_factor
            my *= micro_factor
            # y -= by
            # y /= my

            creation_str = datetime.utcnow().strftime('%Y%j%H%M%S')
            start_str = gridded_product["begin_time"].strftime('%Y%j%H%M%S')
            for ty in range(tile_count[0]):
                for tx in range(tile_count[1]):
                    # store tile data to an intermediate array
                    tmp_tile[:] = fill_value
                    tile_number = ty * tile_count[1] + tx + 1
                    tmp_tile[:] = data[ty * tile_shape[0]: (ty + 1) * tile_shape[0], tx * tile_shape[1]: (tx + 1) * tile_shape[1]]
                    output_filename = "OR_HFD-010-B11-M1C03-T{:03d}_GH8_s{}_c{}.nc".format(tile_number, start_str, creation_str)

                    if tmp_tile.mask.all():
                        LOG.info("Tile %d contains all masked data, skipping...", tile_number)
                        continue
                    LOG.info("Writing tile %d to %s", tile_number, output_filename)

                    tmp_x = x[tx * tile_shape[1]: (tx + 1) * tile_shape[1]]
                    tmp_y = y[ty * tile_shape[0]: (ty + 1) * tile_shape[0]]

                    # fake_scene.navigation = nav
                    attr_helper = AttributeHelper(fake_scene, (ty, tx), tile_count, data.shape)
                    # attr_helper = AttributeHelper(fake_scene, (0, 0), (1, 1), tmp_tile.shape)
                    band = 2
                    nc = SCMI_writer(output_filename, 10, (ty, tx), tile_shape, 'albedo', band, include_rad=False, helper=attr_helper)
                    LOG.debug("Creating dimensions...")
                    nc.create_dimensions()
                    sfao = IMG_SF_AO[band]
                    LOG.debug("Creating variables...")
                    nc.create_variables(*sfao)
                    LOG.debug("Creating global attributes...")
                    nc.set_global_attrs(fake_scene.metadata, None)
                    LOG.debug("Creating projection attributes...")
                    nc.set_projection_attrs(gridded_product["grid_definition"])
                    LOG.debug("Writing image data...")
                    nc.set_image_data(alb=tmp_tile)
                    LOG.debug("Writing X/Y navigation data...")
                    nc.set_fgf(tmp_x, mx, bx, tmp_y, my, by, units=xy_units)
                    nc.close()
        except StandardError:
            LOG.error("Error while filling in NC file with data: %s", output_filename)
            if not self.keep_intermediate and os.path.isfile(output_filename):
                os.remove(output_filename)
            raise

        return output_filename


def add_backend_argument_groups(parser):
    group = parser.add_argument_group(title="Backend Initialization")
    group.add_argument("--backend-configs", nargs="*", dest="backend_configs",
                       help="alternative backend configuration files")
    group.add_argument("--rescale-configs", nargs="*", dest="rescale_configs",
                       help="alternative rescale configuration files")
    group = parser.add_argument_group(title="Backend Output Creation")
    # group.add_argument("--ncml-template",
    #                    help="alternative AWIPS ncml template file from what is configured")
    group.add_argument("--tiles", dest="tile_count", nargs=2, type=int, default=[1, 1],
                       help="Number of tiles to produce in Y (rows) and X (cols) direction respectively")
    return ["Backend Initialization", "Backend Output Creation"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    from polar2grid.core.containers import GriddedScene, GriddedProduct
    parser = create_basic_parser(description="Create SCMI AWIPS compatible NetCDF files")
    subgroup_titles = add_backend_argument_groups(parser)
    parser.add_argument("--scene", required=True, help="JSON SwathScene filename to be remapped")
    parser.add_argument("-p", "--products", nargs="*", default=None,
                        help="Specify only certain products from the provided scene")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(subgroup_titles=subgroup_titles, global_keywords=global_keywords)

    # Logs are renamed once data the provided start date is known
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)

    LOG.info("Loading scene or product...")
    gridded_scene = GriddedScene.load(args.scene)
    if args.products and isinstance(gridded_scene, GriddedScene):
        for k in gridded_scene.keys():
            if k not in args.products:
                del gridded_scene[k]

    LOG.info("Initializing backend...")
    backend = Backend(**args.subgroup_args["Backend Initialization"])
    if isinstance(gridded_scene, GriddedScene):
        backend.create_output_from_scene(gridded_scene, **args.subgroup_args["Backend Output Creation"])
    elif isinstance(gridded_scene, GriddedProduct):
        backend.create_output_from_product(gridded_scene, **args.subgroup_args["Backend Output Creation"])
    else:
        raise ValueError("Unknown Polar2Grid object provided")

if __name__ == '__main__':
    sys.exit(main())
