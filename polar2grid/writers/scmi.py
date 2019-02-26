#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2018 Space Science and Engineering Center (SSEC),
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
#     Written by David Hoese    March 2016
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""The SCMI AWIPS writer is used to create AWIPS compatible tiled NetCDF4
files. The Advanced Weather Interactive Processing System (AWIPS) is a
program used by the United States National Weather Service (NWS) and others
to view
different forms of weather imagery. Sectorized Cloud and Moisture Imagery
(SCMI) is a netcdf format accepted by AWIPS to store one image broken up
in to one or more "tiles". Once AWIPS is configured for specific products
the SCMI NetCDF writer can be used to provide compatible products to the
system. The files created by this writer are compatible with AWIPS II.

The SCMI writer takes remapped image data and creates an
AWIPS-compatible NetCDF4 file. The SCMI writer and the AWIPS client may
need to be configured to make things appear the way the user wants in
the AWIPS client. The SCMI writer can only produce files for datasets mapped
to areas with specific projections:

    - Lambert Conformal Conic (`+proj=lcc`)
    - Geostationary (`+proj=geos`)
    - Mercator (`+proj=merc`)
    - Polar Stereographic (`+proj=stere`)

This is a limitation of the AWIPS client and not of the SCMI writer.

Numbered versus Lettered Grids
------------------------------

By default the SCMI writer will save tiles by number starting with '1'
representing the upper-left image tile. Tile numbers then increase
along the column and then on to the next row.

By specifying ``--letters`` on the command line, tiles can be designated with a
letter. Lettered grids or sectors are preconfigured in the SCMI writer
configuration file (`scmi.yaml` in SatPy). The lettered tile locations are
static and will not change with the data being written to them. Each lettered
tile is split in to a certain number of subtiles (`--letter-subtiles`),
default 2 rows by 2 columns. Lettered tiles are meant to make it easier for
receiving AWIPS clients/stations to filter what tiles they receive; saving
time, bandwidth, and space.

Any tiles (numbered or lettered) not containing any valid data are not
created.

 .. warning::

     The SCMI writer does not default to using any grid. Therefore, it is recommended to specify
     one or more grids for remapping by using the `-g` flag.

"""
import logging

LOG = logging.getLogger(__name__)


def add_writer_argument_groups(parser):
    DEFAULT_OUTPUT_PATTERN = '{source_name}_AII_{platform_name}_{sensor}_{name}_{sector_id}_{tile_id}_{start_time:%Y%m%d_%H%M}.nc'
    group_1 = parser.add_argument_group(title='SCMI Writer')
    # group_1.add_argument('--file-pattern', default=DEFAULT_OUTPUT_PATTERN,
    #                      help="custom file pattern to save dataset to")
    group_1.add_argument("--compress", action="store_true",
                         help="zlib compress each netcdf file")
    group_1.add_argument("--fix-awips", action="store_true",
                         help="modify NetCDF output to work with the old/broken AWIPS NetCDF library")
    # Saving specific keyword arguments
    # group_2 = parser.add_argument_group(title='Writer Save')
    group_1.add_argument("--tiles", dest="tile_count", nargs=2, type=int, default=[1, 1],
                         help="Number of tiles to produce in Y (rows) and X (cols) direction respectively")
    group_1.add_argument("--tile-size", dest="tile_size", nargs=2, type=int, default=None,
                         help="Specify how many pixels are in each tile (overrides '--tiles')")
    group_1.add_argument("--letters", dest="lettered_grid", action='store_true',
                         help="Create tiles from a static letter-based grid based on the product projection")
    group_1.add_argument("--letter-subtiles", nargs=2, type=int, default=(2, 2),
                         help="Specify number of subtiles in each lettered tile: \'row col\'")
    group_1.add_argument("--source-name", default='SSEC',
                         help="specify processing source name used in attributes and filename (default 'SSEC')")
    group_1.add_argument("--sector-id", required=True,
                         help="specify name for sector/region used in attributes and filename (example 'LCC')")
    return group_1, None

