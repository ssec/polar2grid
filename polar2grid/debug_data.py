#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2019-2022 Space Science and Engineering Center (SSEC),
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
"""Produce various text and image outputs for debugging input data."""

import logging
import sys

import dask
import dask.array as da
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from satpy import Scene

matplotlib.use("agg")

LOG = logging.getLogger(__name__)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Produce various debug images and text about input data.")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="count",
        default=0,
        help="each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)",
    )
    parser.add_argument("reader", help="Satpy reader to use")
    parser.add_argument("product", help="Product to load")
    parser.add_argument("files", nargs="*", help="Files to load data from")
    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(3, args.verbosity)])

    dask.config.set(num_workers=4)
    scn = Scene(reader=args.reader, filenames=args.files)
    scn.load([args.product])
    data = scn[args.product].compute()
    start_time = data.attrs["start_time"]
    lons, lats = da.compute(*data.attrs["area"].get_lonlats())

    print("## Longitude:")
    print("   Minimum: ", np.nanmin(lons))
    print("   Maximum: ", np.nanmax(lons))
    print("   Has NaNs: ", np.isnan(lons).any())
    print("   Shape: ", lons.shape)
    print("   Data Type: ", lons.dtype)
    fig, ax = plt.subplots()
    img = ax.imshow(lons, vmin=-180, vmax=180)
    cbar = fig.colorbar(img)
    ax.set_title("Longitude")
    cbar.set_label("Degrees")
    fig.savefig("longitude_{:%Y%m%d_%H%M%S}.png".format(start_time))

    print("## Latitude:")
    print("   Minimum: ", np.nanmin(lats))
    print("   Maximum: ", np.nanmax(lats))
    print("   Has NaNs: ", np.isnan(lats).any())
    print("   Shape: ", lats.shape)
    print("   Data Type: ", lats.dtype)
    fig, ax = plt.subplots()
    img = ax.imshow(lats, vmin=-90, vmax=90)
    cbar = fig.colorbar(img)
    ax.set_title("Latitude")
    cbar.set_label("Degrees")
    fig.savefig("latitude_{:%Y%m%d_%H%M%S}.png".format(start_time))

    print("## {}:".format(args.product))
    print("   Minimum: ", np.nanmin(data))
    print("   Maximum: ", np.nanmax(data))
    print("   Has NaNs: ", np.isnan(data).values.any().item())
    print("   Shape: ", data.shape)
    print("   Data Type: ", data.dtype)
    print("   Attributes: ", "\n      ".join("{}: {}".format(k, v) for k, v in data.attrs.items()))
    fig, ax = plt.subplots()
    img = ax.imshow(data)
    cbar = fig.colorbar(img)
    ax.set_title(args.product)
    cbar.set_label(data.attrs.get("units", "<unknown>"))
    fig.savefig("{}_{:%Y%m%d_%H%M%S}.png".format(args.product, start_time))


if __name__ == "__main__":
    sys.exit(main())
