#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2013-2021 Space Science and Engineering Center (SSEC),
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
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
"""Simple script to plot AWIPS NetCDF files onto a png file using matplotlib."""
import os
import sys
from glob import glob

import matplotlib.cm as cm
from matplotlib import pyplot as plt
from netCDF4 import Dataset

__docformat__ = "restructuredtext en"

import matplotlib
import numpy as np

matplotlib.use("agg")

DEF_DIR = "."
DEF_PAT = "SSEC_AWIPS_*"

DEF_VMIN = 0
DEF_VMAX = 255
DEF_DPI = 100


def _open_file_and_get_var_data(file_name, var_name, var_type=np.uint8):
    """Open a file and get the variable from it, converting it to var_type.

    Note: uint8 is the default type which converts AWIPS data to something more plottable.
    """
    dataset = Dataset(file_name, "r")
    data_var = dataset.variables[var_name]
    data_var.set_auto_maskandscale(False)
    data = data_var[:]
    data = data.astype(var_type)
    data = np.ma.masked_array(data, data == 0)

    return data


def _plt_basic_imshow_fig(data, vmin, vmax, cmap=cm.bone, title="image", background_color="white"):
    """Plot a basic imshow figure using the given data, bounds, and colormap."""
    # Create a new figure everytime so things don't get shared
    figure = plt.figure()
    axes = figure.add_subplot(111, facecolor=background_color)

    # Plot the data
    print(data.min(), data.max())
    plt.imshow(data, vmin=vmin, vmax=vmax, cmap=cmap)

    # Add a colorbar and force the colormap
    plt.colorbar()

    # Add the title
    axes.set_title(title)

    return figure


def plot_file_patterns(
    base_dir=DEF_DIR, base_pat=DEF_PAT, vmin=DEF_VMIN, vmax=DEF_VMAX, dpi_to_use=DEF_DPI, background_color="white"
):
    glob_pat = os.path.join(base_dir, base_pat)
    for nc_name in glob(glob_pat):
        nc_name = os.path.split(nc_name)[1]
        print("Drawing for NC name %s" % (nc_name,))

        # Get the data from the file
        data = _open_file_and_get_var_data(nc_name, "image")

        # plot and save our figure
        figure = _plt_basic_imshow_fig(data, vmin, vmax, title=nc_name, background_color=background_color)
        figure.savefig("plot_ncdata.%s.png" % nc_name, dpi=dpi_to_use)
        plt.close()


def rough_compare(path1, path2, vmin=DEF_VMIN, vmax=DEF_VMAX, dpi_to_use=DEF_DPI):
    """Compare two data sets using various basic checks and draw some images."""
    data1 = _open_file_and_get_var_data(path1, "image")
    data2 = _open_file_and_get_var_data(path2, "image")

    diff = np.zeros(data1.shape, dtype=np.int32)
    diff[:] = data1[:]
    diff = diff - data2

    # make a picture of the first data set
    fig = _plt_basic_imshow_fig(data1, vmin, vmax, title="data set 1", cmap=cm.Paired)
    fig.savefig("plot_ncdata.Set1.png", dpi=dpi_to_use)
    plt.close()

    # make a picture of the second data set
    fig = _plt_basic_imshow_fig(data2, vmin, vmax, title="data set 2", cmap=cm.Paired)
    fig.savefig("plot_ncdata.Set2.png", dpi=dpi_to_use)
    plt.close()

    # make a picture of the difference
    fig = _plt_basic_imshow_fig(diff, np.min(diff), np.max(diff), title="difference", cmap=cm.Spectral)
    fig.savefig("plot_ncdata.diff.png", dpi=dpi_to_use)
    plt.close()

    # make a picture of the difference in a more restricted range
    diff[diff > 10.0] = 10.0
    diff[diff < -10.0] = -10.0
    fig = _plt_basic_imshow_fig(diff, np.min(diff), np.max(diff), title="difference, restricted", cmap=cm.Spectral)
    fig.savefig("plot_ncdata.diff_r.png", dpi=dpi_to_use)
    plt.close()


def get_parser():
    from argparse import ArgumentParser

    description = """This script will read a series of NetCDF3 files created using the AWIPS
backend and plot the data on a b/w color scale.  It searches for any NetCDF
files with the prefix ``SSEC_AWIPS_``."""
    parser = ArgumentParser(description=description)
    parser.add_argument(
        "--vmin",
        dest="vmin",
        default=None,
        type=int,
        help="Specify minimum brightness value. Defaults to minimum value of data.",
    )
    parser.add_argument(
        "--vmax",
        dest="vmax",
        default=None,
        type=int,
        help="Specify maximum brightness value. Defaults to maximum value of data.",
    )
    parser.add_argument(
        "-p",
        "--pat",
        dest="base_pat",
        default=DEF_PAT,
        help="Specify the glob pattern of NetCDF files to look for. Defaults to '%s'" % DEF_PAT,
    )
    parser.add_argument(
        "-d",
        "--dpi",
        dest="dpi",
        default=100,
        type=float,
        help="Specify the dpi for the resulting figure, higher dpi will result in larger figures and longer run times",
    )
    parser.add_argument(
        "-c",
        dest="do_compare",
        default=False,
        action="store_true",
        help="Include this flag if you wish to compare two specific files",
    )
    parser.add_argument(
        "--background-color", default="white", help="Specify a background color to easier see transparent values"
    )
    parser.add_argument(
        "search_dir", default=None, nargs="*", help="Directory to search for NetCDF3 files, default is '.'"
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    files_temp = None
    base_dir = None
    if args.search_dir is None or len(args.search_dir) == 0:
        base_dir = DEF_DIR
    elif len(args.search_dir) == 1:
        base_dir = args.search_dir[0]
    elif len(args.search_dir) == 2:
        files_temp = (args.search_dir[0], args.search_dir[1])
    else:
        print("ERROR: 0, 1, or 2 arguments are allowed for 'search_dir', not %d" % (len(args.search_dir),))
        return -1

    if files_temp is None:
        return plot_file_patterns(
            base_dir=base_dir,
            base_pat=args.base_pat,
            background_color=args.background_color,
            vmin=args.vmin,
            vmax=args.vmax,
            dpi_to_use=args.dpi,
        )
    else:
        return rough_compare(files_temp[0], files_temp[1], vmin=args.vmin, vmax=args.vmax, dpi_to_use=args.dpi)


if __name__ == "__main__":
    sys.exit(main())
