#!/usr/bin/env python3
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
"""Add a colortable to an existing GeoTIFF.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2016 University of Wisconsin SSEC. All rights reserved.
:date:         July 2016
:license:      GNU GPLv3

"""
import os
import sys
import numpy as np
import gdal
from trollimage.colormap import Colormap


def parse_color_table_file(f):
    """Colormap files are comma-separated 'integer,R,G,B,A' text files.

    A basic greyscale example for an 8-bit GeoTIFF would be::

        0,0,0,0,255
        1,1,1,1,255
        ...
        254,254,254,254,255
        255,255,255,255,255

    Where the `...` represents the lines in between, meaning every input
    GeoTIFF value has a corresponding RGBA value specified. The first value
    is the input GeoTIFF value, followed by R (red), G (green), B (blue),
    and A (alpha).

    This script will also linearly interpolate between two values.
    So the above colormap file could also be written in just two lines::

        0,0,0,0,255
        255,255,255,255,255

    Often times you may want to have the 0 value as a transparent 'fill' value
    and continue the colormap after that. This can be done by doing the
    following::

        # 0 is a fill value
        0,0,0,0,0
        # 1 starts at bright red
        1,255,0,0,255
        # and we end with black at the end
        255,0,0,0,255

    .. note::

        Not all image viewers will obey the transparent (alpha) settings

    Blank lines are allowed as well as spaces between line elements.

    """
    ct = []
    with open(f, "r") as ct_file:
        prev_idx = None
        for line in ct_file:
            if line.startswith("#") or not line:
                continue
            parts = [int(x.strip()) for x in line.split(",")]
            assert len(parts) == 5
            if prev_idx is None:
                # this is the first line we're adding, prefill everything before
                prev_idx = 0
                while prev_idx <= parts[0]:
                    ct.append([prev_idx] + parts[1:])
                    prev_idx += 1
            elif parts[0] != prev_idx + 1:
                # interpolate from the previous to the current
                num_samples = parts[0] - prev_idx
                r_interp = np.linspace(ct[-1][1], parts[1], num_samples).astype(np.int)
                g_interp = np.linspace(ct[-1][2], parts[2], num_samples).astype(np.int)
                b_interp = np.linspace(ct[-1][3], parts[3], num_samples).astype(np.int)
                a_interp = np.linspace(ct[-1][4], parts[4], num_samples).astype(np.int)
                interp_idx = 0
                while prev_idx < parts[0]:
                    prev_idx += 1
                    ct.append(
                        [
                            prev_idx,
                            r_interp[interp_idx],
                            g_interp[interp_idx],
                            b_interp[interp_idx],
                            a_interp[interp_idx],
                        ]
                    )
                    interp_idx += 1
            else:
                ct.append(parts)
            prev_idx = parts[0]

    if prev_idx < 255:
        last_entry = ct[-1]
        ct.extend([last_entry] * (255 - prev_idx))
    return ct


def load_color_table_file_to_colormap(ct_file):
    """Load a text colormap file and create a trollimage.Colormap object.

    If the provided pathname includes ``$POLAR2GRID_HOME`` it will be replaced
    with the current environment variable value of ``POLAR2GRID_HOME``.

    """
    from trollimage.colormap import Colormap

    p2g_home = os.getenv("POLAR2GRID_HOME", "")
    ct_file = ct_file.replace("$POLAR2GRID_HOME", p2g_home)
    ct_file = ct_file.replace("$GEO2GRID_HOME", p2g_home)
    if ct_file.endswith(".npy") or ct_file.endswith(".npz"):
        # binary colormap files (RGB, RGBA, VRGB, VRGBA)
        from satpy.enhancements import create_colormap

        cmap = create_colormap({"filename": ct_file})
    else:
        # P2G style colormap text files
        ct = parse_color_table_file(ct_file)
        entries = ((e[0] / 255.0, [x / 255.0 for x in e[1:]]) for e in ct)
        cmap = Colormap(*entries)
    return cmap


def create_colortable(ct_file_or_entries):
    """Create GDAL ColorTable object from Colormap object."""
    if isinstance(ct_file_or_entries, str):
        ct_entries = parse_color_table_file(ct_file_or_entries)
    elif isinstance(ct_file_or_entries, Colormap):
        ct_entries = enumerate(ct_file_or_entries.colors)
        ct_entries = (((x,) + tuple(int(c * 255.0) for c in color)) for x, color in ct_entries)
    else:
        ct_entries = ct_file_or_entries

    ct = gdal.ColorTable()
    for entry in ct_entries:
        ct.SetColorEntry(entry[0], tuple(entry[1:]))

    return ct


def add_colortable(gtiff, ct):
    num_bands = gtiff.RasterCount
    if num_bands in (2, 4):
        # don't add a color table to alpha bands
        num_bands -= 1
    for band_num in range(num_bands):
        gtiff.GetRasterBand(band_num + 1).SetColorTable(ct)


def get_parser():
    import argparse

    description = "Add a GeoTIFF colortable to an existing single-band GeoTIFF."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("ct_file", help="Color table file to apply (CSV of (int, R, G, B, A)")
    parser.add_argument("geotiffs", nargs="+", help="Geotiff files to apply the color table to")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    ct = create_colortable(args.ct_file)
    for geotiff_fn in args.geotiffs:
        gtiff = gdal.Open(geotiff_fn, gdal.GF_Write)
        add_colortable(gtiff, ct)


if __name__ == "__main__":
    sys.exit(main())
