#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2016-2022 Space Science and Engineering Center (SSEC),
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
"""Add a colortable to an existing GeoTIFF."""

import os
import sys

import numpy as np
import rasterio
from trollimage.colormap import Colormap


def load_color_table_file_to_colormap(ct_file):
    """Load a text colormap file and create a trollimage.Colormap object.

    If the provided pathname includes ``$POLAR2GRID_HOME`` it will be replaced
    with the current environment variable value of ``POLAR2GRID_HOME``.

    """
    from satpy.enhancements import create_colormap

    p2g_home = os.getenv("POLAR2GRID_HOME", "")
    ct_file = ct_file.replace("$POLAR2GRID_HOME", p2g_home)
    ct_file = ct_file.replace("$GEO2GRID_HOME", p2g_home)
    cmap = create_colormap({"filename": ct_file})
    return cmap


def create_colortable(ct_file_or_entries):
    """Create GDAL ColorTable object from Colormap object."""
    if isinstance(ct_file_or_entries, str):
        ct_file_or_entries = load_color_table_file_to_colormap(ct_file_or_entries)
    if isinstance(ct_file_or_entries, Colormap):
        values = np.arange(256)
        new_colors = ct_file_or_entries.colorize(values)
        new_colors = np.clip(new_colors, 0.0, 1.0)
        ct_file_or_entries = (
            (color_idx,) + tuple(np.round(new_colors[:, color_idx] * 255.0)) for color_idx in range(new_colors.shape[1])
        )

    ct_dict = {entry[0]: tuple(entry[1:]) for entry in ct_file_or_entries}
    return ct_dict


def add_colortable(gtiff_ds, ct_dict):
    num_bands = gtiff_ds.count
    if num_bands in (2, 4):
        # don't add a color table to alpha bands
        num_bands -= 1
    for band_num in range(num_bands):
        gtiff_ds.write_colormap(band_num + 1, ct_dict)


def get_parser():
    import argparse

    description = "Add a GeoTIFF colortable to an existing single-band GeoTIFF."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("ct_file", help="Color table file to apply (CSV of (int, R, G, B, A)")
    parser.add_argument("geotiffs", nargs="+", help="Geotiff files to apply the color table to")
    return parser


def main(argv=sys.argv[1:]):
    parser = get_parser()
    args = parser.parse_args(argv)

    ct = create_colortable(args.ct_file)
    for geotiff_fn in args.geotiffs:
        gtiff_ds = rasterio.open(geotiff_fn, "r+")
        add_colortable(gtiff_ds, ct)


if __name__ == "__main__":
    sys.exit(main())
