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

import sys
from datetime import datetime, timedelta
from netCDF4 import Dataset

import logging
import numpy as np
import os

from polar2grid.core import roles
from ConfigParser import NoSectionError, NoOptionError

LOG = logging.getLogger(__name__)
# AWIPS 2 seems to not like data values under 0
AWIPS_USES_NEGATIVES = False
DEFAULT_OUTPUT_PATTERN = '{source_name}_AII_{satellite}_{instrument}_{product_name}_{sector_id}_T{tile_id}_{begin_time:%Y%m%d_%H%M}.nc'
DEFAULT_CONFIG_FILE = os.environ.get("AWIPS_CONFIG_FILE", "polar2grid.awips:scmi_backend.ini")

# misc. global attributes
SCMI_GLOBAL_ATT = dict(
    satellite_id=None,  # GOES-H8
    pixel_y_size=None,  # km
    start_date_time=None,  # 2015181030000,  # %Y%j%H%M%S
    pixel_x_size=None,  # km
    product_name=None,  # "HFD-010-B11-M1C01",
    production_location=None,  # "MSC",
)


UNIT_CONV = {
    'micron': 'microm',
    'mm h-1': 'mm/h',
    '1': '*1',
    'none': '*1',
    'percent': '%',
    'Kelvin': 'kelvin',
    'K': 'kelvin',
}


# Lettered Grids are predefined/static tile grids starting with A
# in the upper-left cell, going right until all cells are filled
# Map proj_type -> (upper_left_extent, lower_right_extent, tile_width, tile_height)
LETTERED_GRIDS = {
    'lcc': ((-140, 55), (-50, 15), 5000, 5000),
    'stere': ((130, 80), (-120, 50), 5000, 5000),
    'mercator': ((-180, 50), (-50, 10), 5000, 5000),
}


class NumberedTileGenerator(object):
    def __init__(self, grid_definition, data,
                 tile_shape=None, tile_count=None):
        self.grid_definition = grid_definition
        self.data = data

        # get tile shape, number of tiles, etc.
        self._get_tile_properties(tile_shape, tile_count)
        # X and Y coordinates of the whole image
        self.x, self.y = self._get_xy_arrays()
        # scaling parameters for the overall images X and Y coordinates
        # they must be the same for all X and Y variables for all tiles
        # and must be stored in the file as 0, 1, 2, 3, ...
        # (X factor, X offset, Y factor, Y offset)
        self.mx, self.bx, self.my, self.by = self._get_xy_scaling_parameters()

    def _get_tile_properties(self, tile_shape, tile_count):
        if tile_shape is not None:
            tile_shape = (int(min(tile_shape[0], self.data.shape[0])), int(min(tile_shape[1], self.data.shape[1])))
            tile_count = (int(np.ceil(self.data.shape[0] / tile_shape[0])), int(np.ceil(self.data.shape[1] / tile_shape[1])))
        else:
            tile_shape = (int(np.ceil(self.data.shape[0] / float(tile_count[0]))), int(np.ceil(self.data.shape[1] / float(tile_count[1]))))

        # number of pixels per each tile
        self.tile_shape = tile_shape
        # number of tiles in each direction (rows, columns)
        self.tile_count = tile_count
        # number of tiles in the entire image
        self.total_tiles = tile_count[0] * tile_count[1]
        # number of pixels in the whole image (rows, columns)
        self.image_shape = (self.tile_shape[0] * self.tile_count[0],
                            self.tile_shape[1] * self.tile_count[1])

    def _get_xy_arrays(self):
        gd = self.grid_definition
        ts = self.tile_shape
        tc = self.tile_count
        # Since our tiles may go over the edge of the original "grid" we
        # need to make sure we calculate X/Y to the edge of all of the tiles
        imaginary_data_size = (ts[0] * tc[0], ts[1] * tc[1])
        imaginary_grid_def = gd.copy()
        imaginary_grid_def["height"] = imaginary_data_size[0]
        imaginary_grid_def["width"] = imaginary_data_size[1]

        x, y = imaginary_grid_def.get_xy_arrays()
        x = x[0].squeeze()  # all rows should have the same coordinates
        y = y[:, 0].squeeze()  # all columns should have the same coordinates
        # scale the X and Y arrays to fit in the file for 16-bit integers
        # AWIPS is dumb and requires the integer values to be 0, 1, 2, 3, 4
        # Max value of a signed 16-bit integer is 32767 meaning
        # 32768 values.
        if x.shape[0] > 2**15:
            # awips uses 0, 1, 2, 3 so we can't use the negative end of the variable space
            raise ValueError("X variable too large for AWIPS-version of 16-bit integer space")
        if y.shape[0] > 2**15:
            # awips uses 0, 1, 2, 3 so we can't use the negative end of the variable space
            raise ValueError("Y variable too large for AWIPS-version of 16-bit integer space")
        return x, y

    def _get_xy_scaling_parameters(self):
        """Get the X/Y coordinate limits for the full resulting image"""
        gd = self.grid_definition
        bx = self.x.min()
        mx = gd['cell_width']
        by = self.y.min()
        my = gd['cell_height']
        return mx, bx, my, by

    def _tile_number(self, ty, tx):
        # e.g.
        # 001 002 003 004
        # 005 006 ...
        return ty * self.tile_count[1] + tx + 1

    def _tile_identifier(self, ty, tx):
        return "T{:03d}".format(self._tile_number(ty, tx))

    def __call__(self, fill_value=np.nan):
        x = self.x
        y = self.y
        ts = self.tile_shape
        tc = self.tile_count
        tmp_tile = np.ma.zeros(ts, dtype=np.float32)
        tmp_tile.set_fill_value(fill_value)
        for ty in range(tc[0]):
            for tx in range(tc[1]):
                tile_id = self._tile_identifier(ty, tx)
                tile_row_offset = ty * ts[0]
                tile_column_offset = tx * ts[1]

                # store tile data to an intermediate array
                # the tile may be larger than the remaining data, handle that:
                max_row_idx = min((ty + 1) * ts[0], self.data.shape[0]) - (ty * ts[0])
                max_col_idx = min((tx + 1) * ts[1], self.data.shape[1]) - (tx * ts[1])
                tmp_tile[:] = fill_value
                tmp_tile[:max_row_idx, :max_col_idx] = self.data[
                                                       ty * ts[0]: (ty + 1) * ts[0],
                                                       tx * ts[1]: (tx + 1) * ts[1]
                                                       ]

                if tmp_tile.mask.all():
                    LOG.info("Tile %d contains all masked data, skipping...", tile_id)
                    continue
                tmp_x = x[tx * ts[1]: (tx + 1) * ts[1]]
                tmp_y = y[ty * ts[0]: (ty + 1) * ts[0]]

                yield tile_row_offset, tile_column_offset, tile_id, tmp_x, tmp_y, tmp_tile


class LetteredTileGenerator(NumberedTileGenerator):
    def __init__(self, grid_definition, data, cell_size=(5000, 5000),
                 num_subtiles=4):
        super(LetteredTileGenerator, self).__init__(
            grid_definition, data, tile_count=(1, 1))
        self.num_subtiles = num_subtiles
        self.cell_size = cell_size
        # lon/lat
        self.ll_extents = (-135, 20)
        self.ur_extents = (-60, 60)

    def create_grid(self):
        gd = self.grid_definition
        x, y = gd.get_xy()

        ll_corner = self.ll_extents
        ur_corner = self.ur_extents
        cw = abs(gd['cell_width'])
        ch = abs(gd['cell_height'])
        cs = self.cell_size  # column width, row height
        p = self.grid_definition.proj
        ll_xy = p(*ll_corner)
        ur_xy = p(*ur_corner)
        # Tile numbering/naming starts from the upper left corner
        ul_xy = (ll_xy[0], ur_xy[1])

        # Adjust the upper-left corner to 'perfectly' match the data
        shift_x = float(x.min() - ll_xy[0]) % cw  # could be negative
        shift_y = float(y.max() - ll_xy[1]) % ch  # could be negative
        ul_xy = (ul_xy[0] + shift_x, ul_xy[1] + shift_y)

        # need X/Y for *whole* tiles
        max_cols = int(np.ceil((ur_xy[0] - ul_xy[0]) / cs[0])) + 1
        max_rows = int(np.ceil((ul_xy[1] - ll_xy[0]) / cs[1])) + 1
        min_col = max(int(np.floor((x.min() - ul_xy[0]) / cs[0])), 0)
        max_col = min(int(np.ceil((x.max() - ul_xy[0]) / cs[0])), max_cols)
        min_row = max(int(np.floor((ul_xy[1] - y.max()) / cs[1])), 0)
        max_row = min(int(np.ceil((ul_xy[1] - y.min()) / cs[1])), max_rows)
        num_cols = max_col - min_col + 1
        num_rows = max_row - min_row + 1

        # right_extent = ul_xy[0] + num_cols * cs[0]
        # bottom_extent = ul_xy[1] - num_rows * cs[1]
        # # the new *actual* extents of the grid based on the upper-left origin
        # ur_xy = (right_extent, ul_xy[1])
        # ll_xy = (ul_xy[0], bottom_extent)
        if num_cols * num_rows > 26:
            raise ValueError("Too many lettered grid cells. Max 26")

        num_pixels_x = int(np.abs(np.ceil(cs[0] / cw)))
        num_pixels_y = int(np.abs(np.ceil(cs[1] / ch)))






        x, y = imaginary_grid_def.get_xy_arrays()
        x = x[0].squeeze()  # all rows should have the same coordinates
        y = y[:, 0].squeeze()  # all columns should have the same coordinates
        # scale the X and Y arrays to fit in the file for 16-bit integers
        # AWIPS is dumb and requires the integer values to be 0, 1, 2, 3, 4
        # Max value of a signed 16-bit integer is 32767 meaning
        # 32768 values.
        if x.shape[0] > 2**15:
            # awips uses 0, 1, 2, 3 so we can't use the negative end of the variable space
            raise ValueError("X variable too large for AWIPS-version of 16-bit integer space")
        bx = x.min()
        mx = gd['cell_width']
        if y.shape[0] > 2**15:
            # awips uses 0, 1, 2, 3 so we can't use the negative end of the variable space
            raise ValueError("Y variable too large for AWIPS-version of 16-bit integer space")
        by = y.min()
        my = gd['cell_height']
        return x, mx, bx, y, my, by

    def __call__(self, x, y, fill_value=np.nan):
        cw = abs(self.grid_definition['cell_width'])
        ch = abs(self.grid_definition['cell_height'])
        cs = self.cell_size  # column width, row height
        p = self.grid_definition.proj
        ll_xy = p(*ll_corner)
        ur_xy = p(*ur_corner)
        # Tile numbering/naming starts from the upper left corner
        ul_xy = (ll_xy[0], ur_xy[1])

        # Adjust the upper-left corner to 'perfectly' match the data
        shift_x = float(x.min() - ll_xy[0]) % cw  # could be negative
        shift_y = float(y.max() - ll_xy[1]) % ch  # could be negative
        ul_xy = (ul_xy[0] + shift_x, ul_xy[1] + shift_y)

        # need X/Y for *whole* tiles
        max_cols = int(np.ceil((ur_xy[0] - ul_xy[0]) / cs[0])) + 1
        max_rows = int(np.ceil((ul_xy[1] - ll_xy[0]) / cs[1])) + 1
        min_col = max(int(np.floor((x.min() - ul_xy[0]) / cs[0])), 0)
        max_col = min(int(np.ceil((x.max() - ul_xy[0]) / cs[0])), max_cols)
        min_row = max(int(np.floor((ul_xy[1] - y.max()) / cs[1])), 0)
        max_row = min(int(np.ceil((ul_xy[1] - y.min()) / cs[1])), max_rows)
        num_cols = max_col - min_col + 1
        num_rows = max_row - min_row + 1

        # right_extent = ul_xy[0] + num_cols * cs[0]
        # bottom_extent = ul_xy[1] - num_rows * cs[1]
        # # the new *actual* extents of the grid based on the upper-left origin
        # ur_xy = (right_extent, ul_xy[1])
        # ll_xy = (ul_xy[0], bottom_extent)
        if num_cols * num_rows > 26:
            raise ValueError("Too many lettered grid cells. Max 26")

        num_pixels_x = int(np.abs(np.ceil(cs[0] / cw)))
        num_pixels_y = int(np.abs(np.ceil(cs[1] / ch)))
        tmp_tile = np.ma.zeros((num_pixels_y, num_pixels_x), dtype=np.float32)
        tmp_tile.set_fill_value(fill_value)
        tmp_x = np.ma.zeros((num_pixels_x,), dtype=np.float32)
        tmp_y = np.ma.zeros((num_pixels_y,), dtype=np.float32)

        # where does the data fall in our lettered grid
        for gy in range(min_row, max_row + 1):
            for gx in range(min_col, max_col + 1):
                tile_id = self._tile_identifier(gy, gx)
                x_left = ul_xy[0] + gx * cs[0]
                x_right = x_left + cs[0]
                y_top = ul_xy[1] - gy * cs[1]
                y_bot = y_top - cs[1]
                x_mask = (x >= x_left) & (x < x_right)
                y_mask = (y > y_bot) & (y <= y_top)
                if not x_mask.any() or not y_mask.any():
                    # no data in this tile
                    continue
                x_min_idx = np.argmin(x[x_mask])
                x_max_idx = np.argmax(x[x_mask])
                y_min_idx = np.argmin(y[y_mask])
                y_max_idx = np.argmax(y[y_mask])
                # theoretically we can precompute the X/Y now
                # instead of taking the x/y data and mapping it
                # to the tile
                tmp_x[:] = np.arange(x_left, x_right, cw)
                tmp_y[:] = np.arange(y_top, y_bot, -ch)
                data_x_idx_min = np.nonzero(tmp_x == x[x_min_idx])[0]
                data_x_idx_max = np.nonzero(tmp_x == x[x_max_idx])[0]
                data_y_idx_min = np.nonzero(tmp_y == y[y_min_idx])[0]
                data_y_idx_max = np.nonzero(tmp_y == y[y_max_idx])[0]
                # now put the data in the grid tile
                tmp_tile[data_y_idx_max:data_y_idx_min, data_x_idx_min:data_x_idx_max] = self.data[(y_mask, x_mask)]

                yield gy * num_pixels_y, gx * num_pixels_x, tile_id, tmp_x, tmp_y, tmp_tile


class SCMIConfigReader(roles.INIConfigReader):
    # Fields used to match a product object to it's correct configuration
    id_fields = (
        "product_name",
        "data_kind",
        "satellite",
        "instrument",
        "grid_name",
        "units",
        "reader",
    )

    def __init__(self, *scmi_configs, **kwargs):
        kwargs["section_prefix"] = kwargs.get("section_prefix", "scmi:")
        kwargs["float_kwargs"] = set()
        kwargs["boolean_kwargs"] = set()
        LOG.debug("Loading SCMI configuration files:\n\t%s", "\n\t".join(scmi_configs))
        super(SCMIConfigReader, self).__init__(*scmi_configs, **kwargs)

    def get_config_options(self, **kwargs):
        kwargs = dict((k, kwargs.get(k, None)) for k in self.id_fields)
        return super(SCMIConfigReader, self).get_config_options(**kwargs)


class AttributeHelper(object):
    """
    helper object which wraps around a HimawariScene to provide SCMI attributes
    """
    def __init__(self, dataset):
        self.dataset = dataset

    def apply_attributes(self, nc, table, prefix=''):
        """
        apply fixed attributes, or look up attributes needed and apply them
        """
        for name, value in sorted(table.items()):
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
        return self.dataset["begin_time"] + timedelta(minutes=int(os.environ.get("DEBUG_TIME_SHIFT", 0)))

    def _product_name(self):
        return self.dataset["product_name"]

    def _global_product_name(self):
        return self._product_name()

    def _global_pixel_x_size(self):
        return self.dataset["grid_definition"]["cell_width"] / 1000.

    def _global_pixel_y_size(self):
        return self.dataset["grid_definition"]["cell_height"] / 1000.

    def _global_start_date_time(self):
        when = self._scene_time()
        return when.strftime('%Y-%m-%dT%H:%M:%S')

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
    _kind = None  # 'albedo', 'brightness_temp'
    _band = None
    _include_fgf = True
    _fill_value = 0
    row_dim_name, col_dim_name = 'y', 'x'
    y_var_name, x_var_name = 'y', 'x'
    image_var_name = 'data'
    fgf_y = None
    fgf_x = None
    projection = None

    def __init__(self, filename, include_fgf=True, helper=None, compress=False):
        self._nc = Dataset(filename, 'w')
        self._include_fgf = include_fgf
        self._compress = compress
        self.helper = helper

    def create_dimensions(self, lines, columns):
        # Create Dimensions
        _nc = self._nc
        _nc.createDimension(self.row_dim_name, lines)
        _nc.createDimension(self.col_dim_name, columns)

    def create_variables(self, bitdepth, fill_value, scale_factor=None, add_offset=None,
                         valid_min=None, valid_max=None):
        fgf_coords = "%s %s" % (self.y_var_name, self.x_var_name)

        self.image_data = self._nc.createVariable(self.image_var_name, 'u2', dimensions=(self.row_dim_name, self.col_dim_name), fill_value=fill_value, zlib=self._compress)
        self.image_data.coordinates = fgf_coords
        self.apply_data_attributes(bitdepth, scale_factor, add_offset,
                                   valid_min=valid_min, valid_max=valid_max)

        if self._include_fgf:
            self.fgf_y = self._nc.createVariable(self.y_var_name, 'i2', dimensions=(self.row_dim_name,), zlib=self._compress)
            self.fgf_x = self._nc.createVariable(self.x_var_name, 'i2', dimensions=(self.col_dim_name,), zlib=self._compress)

    def apply_data_attributes(self, bitdepth, scale_factor, add_offset,
                              valid_min=None, valid_max=None):
        # NOTE: grid_mapping is set by `set_projection_attrs`
        self.image_data.scale_factor = np.float32(scale_factor)
        self.image_data.add_offset = np.float32(add_offset)
        u = self.helper.dataset.get('units', '1')
        self.image_data.units = UNIT_CONV.get(u, u)
        file_bitdepth = self.image_data.dtype.itemsize * 8
        is_unsigned = self.image_data.dtype.kind == 'u'
        if not AWIPS_USES_NEGATIVES and not is_unsigned:
            file_bitdepth -= 1
            is_unsigned = True

        if bitdepth >= file_bitdepth:
            bitdepth = file_bitdepth
            num_fills = 1
        else:
            bitdepth = bitdepth
            num_fills = 0
        if valid_min is not None and valid_max is not None:
            self.image_data.valid_min = valid_min
            self.image_data.valid_max = valid_max
        elif not is_unsigned:
            # signed data type
            self.image_data.valid_min = -2**(bitdepth - 1)
            # 1 less for data type (65535), another 1 less for fill value (fill value = max file value)
            self.image_data.valid_max = 2**(bitdepth - 1) - 1 - num_fills
        else:
            # unsigned data type
            self.image_data.valid_min = 0
            self.image_data.valid_max = 2**bitdepth - 1 - num_fills

        if "standard_name" in self.helper.dataset:
            self.image_data.standard_name = self.helper.dataset["standard_name"]
        elif self.helper.dataset["data_kind"] in ["reflectance", "albedo"]:
            self.image_data.standard_name = "toa_bidirectional_reflectance"
        else:
            self.image_data.standard_name = self.helper.dataset["data_kind"]

    def set_fgf(self, x, mx, bx, y, my, by, units='meters', downsample_factor=1):
        # assign values before scale factors to avoid implicit scale reversal
        LOG.debug('y variable shape is {}'.format(self.fgf_y.shape))
        self.fgf_y.scale_factor = np.float64(my * float(downsample_factor))
        self.fgf_y.add_offset = np.float64(by)
        self.fgf_y.units = units
        self.fgf_y.standard_name = "projection_y_coordinate"
        self.fgf_y[:] = y

        self.fgf_x.scale_factor = np.float64(mx * float(downsample_factor))
        self.fgf_x.add_offset = np.float64(bx)
        self.fgf_x.units = units
        self.fgf_x.standard_name = "projection_x_coordinate"
        self.fgf_x[:] = x

    def set_image_data(self, data, fill_value):
        LOG.info('writing image data')
        # note: autoscaling will be applied to make int16
        assert(hasattr(data, 'mask'))
        self.image_data[:, :] = np.require(data.filled(fill_value), dtype=np.float32)

    def set_projection_attrs(self, grid_def):
        """
        assign projection attributes per GRB standard
        """
        proj4_info = grid_def.proj4_dict
        if proj4_info["proj"] == "geos":
            p = self.projection = self._nc.createVariable("fixedgrid_projection", 'i4')
            self.image_data.grid_mapping = "fixedgrid_projection"
            p.short_name = grid_def["grid_name"]
            p.grid_mapping_name = "geostationary"
            p.sweep_angle_axis = proj4_info.get("sweep", "x")
            p.perspective_point_height = proj4_info['h']
            p.latitude_of_projection_origin = np.float32(0.0)
            p.longitude_of_projection_origin = np.float32(proj4_info.get('lon_0', 0.0))  # is the float32 needed?
        elif proj4_info["proj"] == "lcc":
            p = self.projection = self._nc.createVariable("lambert_projection", 'i4')
            self.image_data.grid_mapping = "lambert_projection"
            p.short_name = grid_def["grid_name"]
            p.grid_mapping_name = "lambert_conformal_conic"
            p.standard_parallel = proj4_info["lat_0"]  # How do we specify two standard parallels?
            p.longitude_of_central_meridian = proj4_info["lon_0"]
            p.latitude_of_projection_origion = proj4_info.get('lat_1', proj4_info['lat_0'])  # Correct?
        elif proj4_info['proj'] == 'stere':
            p = self.projection = self._nc.createVariable("polar_projection", 'i4')
            self.image_data.grid_mapping = "polar_projection"
            p.short_name = grid_def["grid_name"]
            p.grid_mapping_name = "polar_stereographic"
            p.standard_parallel = proj4_info["lat_ts"]
            p.straight_vertical_longitude_from_pole = proj4_info.get("lon_0", 0.0)
            p.latitude_of_projection_origion = proj4_info["lat_0"]  # ?
        elif proj4_info['proj'] == 'merc':
            p = self.projection = self._nc.createVariable("mercator_projection", 'i4')
            self.image_data.grid_mapping = "mercator_projection"
            p.short_name = grid_def["grid_name"]
            p.grid_mapping_name = "mercator"
            p.standard_parallel = proj4_info.get('lat_ts', proj4_info.get('lat_0', 0.0))
            p.longitude_of_projection_origin = proj4_info.get("lon_0", 0.0)
        else:
            raise ValueError("SCMI can not handle projection '{}'".format(proj4_info['proj']))

        p.semi_major = np.float32(proj4_info["a"])
        p.semi_minor = np.float32(proj4_info["b"])
        p.false_easting = np.float32(proj4_info.get("x", 0.0))
        p.false_northing = np.float32(proj4_info.get("y", 0.0))

    def set_global_attrs(self, physical_element, awips_id, sector_id,
                         creating_entity, total_tiles, total_pixels,
                         tile_row, tile_column,
                         tile_height, tile_width):
        self._nc.Conventions = "CF-1.7"
        self._nc.creator = "UW SSEC - CSPP Polar2Grid"
        self._nc.creation_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        # name as it shows in the product browser (physicalElement)
        self._nc.physical_element = physical_element
        self._nc.satellite_id = creating_entity
        # identifying name to match against AWIPS common descriptions (ex. "AWIPS_product_name")
        self._nc.awips_id = awips_id
        self._nc.sector_id = sector_id
        self._nc.tile_row_offset = tile_row
        self._nc.tile_column_offset = tile_column
        self._nc.product_tile_height = tile_height
        self._nc.product_tile_width = tile_width
        self._nc.number_product_tiles = total_tiles[0] * total_tiles[1]
        self._nc.product_rows = total_pixels[0]
        self._nc.product_columns = total_pixels[1]

        self.helper.apply_attributes(self._nc, SCMI_GLOBAL_ATT, '_global_')

    def close(self):
        self._nc.sync()
        self._nc.close()
        self._nc = None


class Backend(roles.BackendRole):
    def __init__(self, backend_configs=None, rescale_configs=None,
                 compress=False, fix_awips=False, **kwargs):
        backend_configs = backend_configs or [DEFAULT_CONFIG_FILE]
        self.awips_config_reader = SCMIConfigReader(*backend_configs, empty_ok=True)
        self.compress = compress
        self.fix_awips = fix_awips
        super(Backend, self).__init__(**kwargs)

    @property
    def known_grids(self):
        return None

    def _calc_factor_offset(self, data=None, dtype=np.int16, bitdepth=None,
                            min=None, max=None, num_fills=1,
                            flag_meanings=False):
        if num_fills > 1:
            raise NotImplementedError("More than one fill value is not implemented yet")

        dtype = np.dtype(dtype)
        file_bitdepth = dtype.itemsize * 8
        is_unsigned = dtype.kind == 'u'
        if not AWIPS_USES_NEGATIVES and not is_unsigned:
            file_bitdepth -= 1
            is_unsigned = True

        if bitdepth is None:
            bitdepth = file_bitdepth
        if bitdepth >= file_bitdepth:
            bitdepth = file_bitdepth
        else:
            # don't take away from the data bitdepth if there is room in
            # file data type to allow for extra fill values
            num_fills = 0
        if min is None:
            min = data.min()
        if max is None:
            max = data.max()

        if not is_unsigned:
            # max value
            fills = [2**(file_bitdepth - 1) - 1]
        else:
            # max value
            fills = [2**file_bitdepth - 1]

        if flag_meanings:
            data = data.astype(dtype)
            # AWIPS doesn't like Identity conversion so we can't have
            # a factor of 1 and an offset of 0
            mx = 0.5
            bx = 0
        else:
            mx = float(max - min) / (2**bitdepth - 1 - num_fills)
            bx = min
            if not is_unsigned:
                bx += 2**(bitdepth - 1) * mx

        return fills, mx, bx, data

    def _fix_awips_file(self, fn):
        # hack to get files created by new NetCDF library
        # versions to be read by AWIPS buggy java version
        # of NetCDF
        LOG.info("Modifying SCMI NetCDF file to work with AWIPS")
        import h5py
        h = h5py.File(fn, 'a')
        if '_NCProperties' in h.attrs:
            del h.attrs['_NCProperties']
        h.close()

    def create_output_from_product(self, gridded_product, sector_id=None,
                                   source_name=None, output_pattern=None,
                                   tile_count=(1, 1), tile_size=None,
                                   # tile_offset=(0, 0),
                                   lettered_grid=False,
                                   **kwargs):
        dtype = np.dtype(np.uint16)
        dtype_str = 'uint2'
        fill_value = np.nan
        grid_def = gridded_product["grid_definition"]

        try:
            awips_info = self.awips_config_reader.get_config_options(**gridded_product)
            physical_element = awips_info.get('physical_element', gridded_product['product_name'])
            awips_id = "AWIPS_" + gridded_product['product_name']
            if source_name:
                awips_info['source_name'] = source_name
            if "{" in physical_element:
                physical_element = physical_element.format(**gridded_product)
            def_ce = "{}-{}".format(gridded_product["satellite"].upper(), gridded_product["instrument"].upper())
            creating_entity = awips_info.get('creating_entity', def_ce)
        except NoSectionError as e:
            LOG.error("Could not get information on product from backend configuration file")
            # NoSectionError is not a "StandardError" so it won't be caught normally
            raise RuntimeError(e.message)

        # Create the netcdf file
        created_files = []
        try:
            LOG.debug("Scaling %s data to fit in netcdf file...", gridded_product["product_name"])
            data = gridded_product.get_data_array()
            mask = gridded_product.get_data_mask()
            data = np.ma.masked_array(data, mask=mask)

            bit_depth = gridded_product.setdefault("bit_depth", 16)
            valid_min = gridded_product.get('valid_min')
            if valid_min is None:
                valid_min = np.nanmin(data)
            valid_max = gridded_product.get('valid_max')
            if valid_max is None:
                valid_max = np.nanmax(data)

            LOG.debug("Using product valid min {} and valid max {}".format(valid_min, valid_max))
            fills, factor, offset, data = self._calc_factor_offset(
                data=data,
                bitdepth=bit_depth,
                min=valid_min,
                max=valid_max,
                dtype=dtype,
                flag_meanings='flag_meanings' in gridded_product)

            LOG.info("Writing product %s to AWIPS SCMI NetCDF file", gridded_product["product_name"])

            if lettered_grid:
                tile_gen = LetteredTileGenerator(
                    gridded_product['grid_definition'],
                    data,
                )
            else:
                tile_gen = NumberedTileGenerator(
                    gridded_product['grid_definition'],
                    data,
                    tile_shape=tile_size,
                    tile_count=tile_count,
                )

            attr_helper = AttributeHelper(gridded_product)
            for trow, tcol, tile_id, tmp_x, tmp_y, tmp_tile in tile_gen(fill_value=fill_value):
                if "{" in output_pattern:
                    # format the filename
                    of_kwargs = gridded_product.copy(as_dict=True)
                    of_kwargs['data_type'] = dtype_str
                    of_kwargs["begin_time"] += timedelta(minutes=int(os.environ.get("DEBUG_TIME_SHIFT", 0)))
                    output_filename = self.create_output_filename(output_pattern,
                                                                  grid_name=grid_def["grid_name"],
                                                                  rows=grid_def["height"],
                                                                  columns=grid_def["width"],
                                                                  source_name=awips_info.get('source_name'),
                                                                  sector_id=sector_id,
                                                                  tile_id=tile_id,
                                                                  **of_kwargs)
                else:
                    output_filename = output_pattern
                if os.path.isfile(output_filename):
                    if not self.overwrite_existing:
                        LOG.error("AWIPS file already exists: %s", output_filename)
                        raise RuntimeError("AWIPS file already exists: %s" % (output_filename,))
                    else:
                        LOG.warning("AWIPS file already exists, will overwrite: %s", output_filename)
                created_files.append(output_filename)

                LOG.info("Writing tile '%s' to '%s'", tile_id, output_filename)

                nc = SCMI_writer(output_filename, helper=attr_helper,
                                 compress=self.compress)
                LOG.debug("Creating dimensions...")
                nc.create_dimensions(tmp_tile.shape[0], tmp_tile.shape[1])
                LOG.debug("Creating variables...")
                nc.create_variables(bit_depth, fills[0], factor, offset)
                LOG.debug("Creating global attributes...")
                nc.set_global_attrs(physical_element, awips_id, sector_id, creating_entity,
                                    tile_gen.tile_count, tile_gen.image_shape,
                                    trow, tcol, tmp_tile.shape[0], tmp_tile.shape[1])
                LOG.debug("Creating projection attributes...")
                nc.set_projection_attrs(gridded_product["grid_definition"])
                LOG.debug("Writing image data...")
                np.clip(tmp_tile, valid_min, valid_max, out=tmp_tile)
                nc.set_image_data(tmp_tile, fills[0])
                LOG.debug("Writing X/Y navigation data...")
                nc.set_fgf(tmp_x, tile_gen.mx, tile_gen.bx,
                           tmp_y, tile_gen.my, tile_gen.by, units='meters')
                nc.close()

                if self.fix_awips:
                    self._fix_awips_file(output_filename)
        except StandardError:
            last_fn = created_files[-1] if created_files else "N/A"
            LOG.error("Error while filling in NC file with data: %s", last_fn)
            for fn in created_files:
                if not self.keep_intermediate and os.path.isfile(fn):
                    os.remove(fn)
            raise

        return created_files[-1]


def add_backend_argument_groups(parser):
    group = parser.add_argument_group(title="Backend Initialization")
    group.add_argument("--backend-configs", nargs="*", dest="backend_configs",
                       help="alternative backend configuration files")
    group.add_argument("--compress", action="store_true",
                       help="zlib compress each netcdf file")
    group.add_argument("--fix-awips", action="store_true",
                       help="modify NetCDF output to work with the old/broken AWIPS NetCDF library")
    group = parser.add_argument_group(title="Backend Output Creation")
    group.add_argument("--tiles", dest="tile_count", nargs=2, type=int, default=[1, 1],
                       help="Number of tiles to produce in Y (rows) and X (cols) direction respectively")
    group.add_argument("--tile-size", dest="tile_size", nargs=2, type=int, default=None,
                       help="Specify how many pixels are in each tile (overrides '--tiles')")
    # group.add_argument('--tile-offset', nargs=2, default=(0, 0),
    #                    help="Start counting tiles from this offset ('row_offset col_offset')")
    group.add_argument("--letters", dest="lettered_grid", action='store_true',
                       help="Create tiles from a static letter-based grid based on the product projection")
    group.add_argument("--output-pattern", default=DEFAULT_OUTPUT_PATTERN,
                       help="output filenaming pattern")
    group.add_argument("--source-name", default='SSEC',
                       help="specify processing source name used in attributes and filename (default 'SSEC')")
    group.add_argument("--sector-id", required=True,
                       help="specify name for sector/region used in attributes and filename (example 'LCC')")
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
