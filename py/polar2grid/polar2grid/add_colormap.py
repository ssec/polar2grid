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
"""Add a colortable to an existing geotiff

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2016 University of Wisconsin SSEC. All rights reserved.
:date:         July 2016
:license:      GNU GPLv3

"""
import sys
import numpy as np
import gdal


def parse_color_table_file(f):
    ct = []
    with open(f, "r") as ct_file:
        prev_idx = None
        for line in ct_file:
            if line.startswith("#"):
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
                    ct.append([prev_idx,
                               r_interp[interp_idx],
                               g_interp[interp_idx],
                               b_interp[interp_idx],
                               a_interp[interp_idx]])
                    interp_idx += 1
            else:
                ct.append(parts)
            prev_idx = parts[0]

    if prev_idx < 255:
        last_entry = ct[-1]
        ct.extend([last_entry] * (255 - prev_idx))
    return ct


def create_colortable(ct_file):
    ct_entries = parse_color_table_file(ct_file)
    ct = gdal.ColorTable()
    for entry in ct_entries:
        ct.SetColorEntry(entry[0], tuple(entry[1:]))

    return ct


def add_colortable(gtiff, ct):
    for band_num in range(gtiff.RasterCount):
        gtiff.GetRasterBand(band_num + 1).SetColorTable(ct)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Add colortable to existing geotiff")
    parser.add_argument("ct_file",
                        help="Color table file to apply (CSV of (int, R, G, B, A)")
    parser.add_argument("geotiffs", nargs="+",
                        help="Geotiff files to apply the color table to")
    args = parser.parse_args()

    ct = create_colortable(args.ct_file)
    for geotiff_fn in args.geotiffs:
        gtiff = gdal.Open(geotiff_fn, gdal.GF_Write)
        add_colortable(gtiff, ct)

if __name__ == "__main__":
    sys.exit(main())