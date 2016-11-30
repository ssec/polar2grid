#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2016 Space Science and Engineering Center (SSEC),
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
# Written by David Hoese    July 2016
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Script to add coastlines and borders to a geotiff while also creating a PNG.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2016 University of Wisconsin SSEC. All rights reserved.
:date:         July 2016
:license:      GNU GPLv3

"""

import os
import sys
import logging
import gdal
import osr
from pycoast import ContourWriter
from PIL import Image, ImageFont
from pyproj import Proj


try:
    # try getting setuptools/distribute's version of resource retrieval first
    from pkg_resources import resource_filename as get_resource_filename
except ImportError:
    print("WARNING: Missing 'pkg_resources' dependency")

    def get_resource_filename(mod_name, resource_name):
        if mod_name != 'polar2grid.fonts':
            raise ValueError('Can only import resources from polar2grid (missing pkg_resources dependency)')
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'fonts', resource_name)

LOG = logging.getLogger(__name__)
PYCOAST_DIR = os.environ.get("GSHHS_DATA_ROOT")


def get_parser():
    import argparse
    parser = argparse.ArgumentParser(description="Convert a geotiff to PNG and add coastlines and borders",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_argument_group("coastlines")
    group.add_argument("--add-coastlines", action="store_true",
                       help="Add coastlines")
    group.add_argument("--coastlines-resolution", choices="clihf", default='i',
                       help="Resolution of coastlines to add (crude, low, intermediate, high, full)")
    group.add_argument("--coastlines-level", choices=range(1, 7), type=int, default=4,
                       help="Level of detail from the selected resolution dataset")
    group.add_argument("--coastlines-outline", default=["yellow"], nargs="*",
                       help="Color of coastline lines (color name or 3 RGB integers)")
    group.add_argument("--coastlines-fill", default=None, nargs="*",
                       help="Color of land")

    group = parser.add_argument_group("rivers")
    group.add_argument("--add-rivers", action="store_true",
                       help="Add rivers grid")
    group.add_argument("--rivers-resolution", choices="clihf", default='c',
                       help="Resolution of rivers to add (crude, low, intermediate, high, full)")
    group.add_argument("--rivers-level", choices=range(0, 11), type=int, default=5,
                       help="Level of detail for river lines")
    group.add_argument("--rivers-outline", default=['blue'], nargs="*",
                       help="Color of river lines (color name or 3 RGB integers)")

    group = parser.add_argument_group("grid")
    group.add_argument("--add-grid", action="store_true",
                       help="Add lat/lon grid")
    group.add_argument("--grid-text", action="store_true",
                       help="Add labels to lat/lon grid")
    group.add_argument("--grid-text-size", default=32, type=int,
                       help="Lat/lon grid text font size")
    group.add_argument("--grid-font", default="Vera.ttf",
                       help="Path to TTF font (polar2grid provided or custom path)")
    group.add_argument("--grid-fill", nargs="*", default=["cyan"],
                       help="Color of grid text (color name or 3 RGB integers)")
    group.add_argument("--grid-outline", nargs="*", default=["cyan"],
                       help="Color of grid lines (color name or 3 RGB integers)")
    group.add_argument("--grid-minor-outline", nargs="*", default=["cyan"],
                       help="Color of tick lines (color name or 3 RGB integers)")
    group.add_argument("--grid-D", nargs=2, default=(10., 10.), type=float,
                       help="Degrees between grid lines (lon, lat)")
    group.add_argument("--grid-d", nargs=2, default=(2., 2.), type=float,
                       help="Degrees between tick lines (lon, lat)")
    group.add_argument("--grid-lon-placement", choices=["tl", "lr", "lc", "cc"], default="tb",
                       help="Longitude label placement")
    group.add_argument("--grid-lat-placement", choices=["tl", "lr", "lc", "cc"], default="lr",
                       help="Latitude label placement")

    group = parser.add_argument_group("borders")
    group.add_argument("--add-borders", action="store_true",
                       help="Add country and/or region borders")
    group.add_argument("--borders-resolution", choices="clihf", default='i',
                       help="Resolution of borders to add (crude, low, intermediate, high, full)")
    group.add_argument("--borders-level", choices=range(1, 4), default=2, type=int,
                       help="Level of detail for border lines")
    group.add_argument("--borders-outline", default=['white'], nargs="*",
                       help="Color of border lines (color name or 3 RGB integers)")

    parser.add_argument("--shapes-dir", default=PYCOAST_DIR,
                        help="Specify alternative directory for coastline shape files (default: GSHSS_DATA_ROOT)")
    parser.add_argument("-o", "--output", dest="output_filename", nargs="+",
                        help="Specify the output filename (default replace '.tif' with '.png')")
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
                        help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument("input_tiff", nargs="+",
                        help="Input geotiff(s) to process")

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(3, args.verbosity)])

    if args.output_filename is None:
        args.output_filename = [x[:-3] + "png" for x in args.input_tiff]
    else:
        assert args.output_filename == args.input_tiff, "Output filenames must be equal to number of input tiffs"

    if not (args.add_borders or args.add_coastlines or args.add_grid or args.add_rivers):
        LOG.error("Please specify one of the '--add-X' options to modify the image")
        return -1

    for input_tiff, output_filename in zip(args.input_tiff, args.output_filename):
        LOG.info("Creating {} from {}".format(output_filename, input_tiff))
        gtiff = gdal.Open(input_tiff)
        proj4_str = osr.SpatialReference(gtiff.GetProjection()).ExportToProj4()
        ul_x, res_x, _, ul_y, _, res_y = gtiff.GetGeoTransform()
        half_pixel_x = res_x / 2.
        half_pixel_y = res_y / 2.
        area_extent = (
            ul_x - half_pixel_x,  # lower-left X
            ul_y + res_y * gtiff.RasterYSize - half_pixel_y,  # lower-left Y
            ul_x + res_x * gtiff.RasterXSize + half_pixel_x,  # upper-right X
            ul_y + half_pixel_y,  # upper-right Y
        )
        p = Proj(proj4_str)
        if p.is_latlong():
            # convert lat/lons to radians
            area_extent = p(area_extent[0], area_extent[1]) + p(area_extent[2], area_extent[3])
        img = Image.open(input_tiff).convert('RGB')
        area_def = (proj4_str, area_extent)

        cw = ContourWriter(args.shapes_dir)

        if args.add_coastlines:
            outline = args.coastlines_outline[0] if len(args.coastlines_outline) == 1 else tuple(int(x) for x in args.coastlines_outline)
            if args.coastlines_fill:
                fill = args.coastlines_fill[0] if len(args.coastlines_fill) == 1 else tuple(int(x) for x in args.coastlines_fill)
            else:
                fill = None
            cw.add_coastlines(img, area_def, resolution=args.coastlines_resolution, level=args.coastlines_level,
                              outline=outline, fill=fill)

        if args.add_rivers:
            outline = args.rivers_outline[0] if len(args.rivers_outline) == 1 else tuple(int(x) for x in args.rivers_outline)
            cw.add_rivers(img, area_def,
                          resolution=args.rivers_resolution, level=args.rivers_level,
                          outline=outline)

        if args.add_borders:
            outline = args.borders_outline[0] if len(args.borders_outline) == 1 else tuple(int(x) for x in args.borders_outline)
            cw.add_borders(img, area_def, resolution=args.borders_resolution, level=args.borders_level, outline=outline)

        if args.add_grid:
            try:
                font = ImageFont.truetype(args.grid_font, args.grid_text_size)
            except IOError:
                font_path = get_resource_filename('polar2grid.fonts', args.grid_font)
                if not os.path.exists(font_path):
                    raise ValueError("Font path does not exist: {}".format(font_path))
                font = ImageFont.truetype(font_path, args.grid_text_size)

            outline = args.grid_outline[0] if len(args.grid_outline) == 1 else tuple(int(x) for x in args.grid_outline)
            minor_outline = args.grid_minor_outline[0] if len(args.grid_minor_outline) == 1 else tuple(int(x) for x in args.grid_minor_outline)
            fill = args.grid_fill[0] if len(args.grid_fill) == 1 else tuple(int(x) for x in args.grid_fill)
            cw.add_grid(img, area_def, args.grid_D, args.grid_d, font,
                        fill=fill, outline=outline, minor_outline=minor_outline,
                        lon_placement=args.grid_lon_placement,
                        lat_placement=args.grid_lat_placement)

        img.save(output_filename)

if __name__ == "__main__":
    sys.exit(main())
