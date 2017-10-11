#!/usr/bin/env python
# encoding: utf-8
"""Utility to mimic ms2gt's gridloc program, but for PROJ.4 grids.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2012
:license:      GNU GPLv3
"""
from polar2grid.core.proj import Proj

__docformat__ = "restructuredtext en"

import numpy

import sys
import logging

log = logging.getLogger(__name__)


def parse_geotiff(gtiff_file):
    """Read a geotiff file and return the grid information in it.
    """
    from osgeo import gdal
    from osr import SpatialReference

    g = gdal.Open(gtiff_file)
    srs = SpatialReference(g.GetProjection())
    proj4_str = srs.ExportToProj4()
    gtransform = g.GetGeoTransform()
    origin_x,x_psize,_,origin_y,_,y_psize = gtransform
    width = g.RasterXSize
    height = g.RasterYSize
    return proj4_str,width,height,origin_x,origin_y,x_psize,y_psize


def create_nav_binaries(lon_fn, lat_fn, proj4_str, width, height,
        origin_x, origin_y,
        x_psize, y_psize, psize_radians=False):
    """Create longitude and latitude binaries from the projection definition
    provided.
    """
    p = Proj(proj4_str)

    # Open the files and a memory mapped array
    lon_file = numpy.memmap(lon_fn, dtype=numpy.float32, mode="w+", shape=(abs(height),abs(width)))
    lat_file = numpy.memmap(lat_fn, dtype=numpy.float32, mode="w+", shape=(abs(height),abs(width)))


    cols = numpy.arange(width)
    for row in range(height):
        grid_x = cols * x_psize + origin_x
        grid_y = numpy.repeat(row * y_psize + origin_y, width)
        if "longlat" in proj4_str and not psize_radians:
            lon_file[row] = grid_x[:]
            lat_file[row] = grid_y[:]
        else:
            lons,lats = p(grid_x, grid_y, inverse=True)
            lon_file[row] = lons[:]
            lat_file[row] = lats[:]


def main():
    from argparse import ArgumentParser
    description = """Create latitude and longitude binary files from a PROJ.4
grid.
"""
    parser = ArgumentParser(description=description)
    parser.add_argument("--gtiff", dest="gtiff_file",
            help="Specify a geotiff as the starting point instead of the projection")
    parser.add_argument("--origin", dest="grid_origin", nargs=2, type=float,
            help="Specify the x and y coordinates of the grid origin in projection space")
    parser.add_argument("--psize", dest="pixel_size", nargs=2, type=float,
            help="Specify the x and y pixel sizes of the grid units in projection units")
    parser.add_argument("--gsize", dest="grid_size", nargs=2, type=int,
            help="Specify the width and height of the grid in number of pixels")
    parser.add_argument("--proj", dest="proj4_str",
            help="Specify the PROJ.4 string describing the projection")
    parser.add_argument("--degrees", dest="psize_radians", default=True, action="store_false",
            help="The pixel sizes are in degrees not radians")
    parser.add_argument("output_names", nargs=2,
            help="Specify the names of the longitude and latitude binary files respectively")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    if args.gtiff_file is None:
        # they need to specify all of the arguments
        if args.grid_origin is None or args.pixel_size is None or \
                args.proj4_str is None or args.grid_size is None:
            log.error("If a geotiff is not provided all 4 grid parameters must be specified (origin, pixel size, grid size, PROJ.4 string")
            return -1
        proj4_str = args.proj4_str
        origin_x,origin_y = args.grid_origin
        x_psize,y_psize = args.pixel_size
        width,height = args.grid_size
        psize_radians = args.psize_radians
    else:
        proj4_str,width,height,origin_x,origin_y,x_psize,y_psize = parse_geotiff(args.gtiff_file)
        psize_radians = False

    create_nav_binaries(args.output_names[0], args.output_names[1],
            proj4_str, width, height,
            origin_x, origin_y, x_psize, y_psize, psize_radians=psize_radians)

if __name__ == "__main__":
    sys.exit(main())

