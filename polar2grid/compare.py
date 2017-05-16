#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
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
#     Written by David Hoese    December 2014
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""Script for comparing backend outputs. Generic enough to handle any
supported backend's output.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2014
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

import sys

import logging
import numpy

LOG = logging.getLogger(__name__)


def compare_array(array1, array2, threshold=1.0):
    """Compare 2 binary arrays per pixel

    Two pixels are considered different if the absolute value of their
    difference is greater than 1. This function assumes the arrays are
    in useful data types, which may cause erroneous results. For example,
    if both arrays are unsigned integers and the different results in a
    negative value overflow will occur and the threshold will likely not
    be met.

    :arg array1:        numpy array for comparison
    :arg array2:        numpy array for comparison
    :keyword threshold: float threshold

    :returns: number of different pixels
    """
    if array1.shape != array2.shape:
        LOG.error("Data shapes were not equal")
        raise ValueError("Data shapes were not equal")

    total_pixels = array1.shape[0] * array1.shape[1]
    equal_pixels = numpy.count_nonzero(numpy.isclose(array1, array2, rtol=0, atol=threshold, equal_nan=True))
    diff_pixels = total_pixels - equal_pixels
    if diff_pixels != 0:
        LOG.warning("%d pixels out of %d pixels are different" % (diff_pixels, total_pixels))
    else:
        LOG.info("%d pixels out of %d pixels are different" % (diff_pixels, total_pixels))

    return diff_pixels


def compare_binary(fn1, fn2, shape, dtype, threshold=1.0, **kwargs):
    array1 = numpy.memmap(fn1, shape=shape, dtype=dtype, mode='r')
    array2 = numpy.memmap(fn2, shape=shape, dtype=dtype, mode='r')

    return compare_array(array1, array2, threshold=threshold)


def compare_geotiff(gtiff_fn1, gtiff_fn2, threshold=1.0, **kwargs):
    """Compare 2 single banded geotiff files

    .. note::

        The binary arrays will be converted to 32-bit floats before
        comparison.

    """
    from osgeo import gdal

    gtiff1 = gdal.Open(gtiff_fn1, gdal.GA_ReadOnly)
    gtiff2 = gdal.Open(gtiff_fn2, gdal.GA_ReadOnly)

    array1 = gtiff1.GetRasterBand(1).ReadAsArray().astype(numpy.float32)
    array2 = gtiff2.GetRasterBand(1).ReadAsArray().astype(numpy.float32)

    return compare_array(array1, array2, threshold=threshold)


def compare_ninjo_tiff(tiff_fn1, tiff_fn2, threshold=1.0, **kwargs):
    from .ninjo.ninjo_backend import libtiff

    tiff1 = libtiff.TIFF.open(tiff_fn1)
    tiff2 = libtiff.TIFF.open(tiff_fn2)

    array1 = tiff1.read_tiles().astype(numpy.float32)
    array2 = tiff2.read_tiles().astype(numpy.float32)
    
    return compare_array(array1, array2, threshold=threshold)


def compare_awips_netcdf(nc1_name, nc2_name, threshold=1.0, **kwargs):
    """Compare 2 8-bit AWIPS-compatible NetCDF3 files

    .. note::

        The binary arrays will be converted to 32-bit floats before
        comparison.

    """
    from netCDF4 import Dataset
    nc1 = Dataset(nc1_name, "r")
    nc2 = Dataset(nc2_name, "r")
    image1_var = nc1.variables["image"]
    image2_var = nc2.variables["image"]
    image1_var.set_auto_maskandscale(False)
    image2_var.set_auto_maskandscale(False)
    image1_data = image1_var[:].astype(numpy.uint8).astype(numpy.float32)
    image2_data = image2_var[:].astype(numpy.uint8).astype(numpy.float32)
    
    return compare_array(image1_data, image2_data, threshold=threshold)

type_name_to_compare_func = {
    "binary": compare_binary,
    "gtiff": compare_geotiff,
    "geotiff": compare_geotiff,
    "ninjo": compare_ninjo_tiff,
    "awips": compare_awips_netcdf,
}


def _file_type(str_val):
    str_val = str_val.lower()
    if str_val in type_name_to_compare_func:
        return type_name_to_compare_func[str_val]

    print "ERROR: Unknown file type '%s'" % (str_val,)
    print "Possible file types: \n\t%s" % ("\n\t".join(type_name_to_compare_func.keys()))
    raise ValueError("Unknown file type '%s'" % (str_val,))


def main(argv=sys.argv[1:]):
    from argparse import ArgumentParser
    from polar2grid.core import str_to_dtype
    parser = ArgumentParser(description="Compare two files per pixel")
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
                        help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument('--threshold', dest='threshold', type=float, default=1.0,
                        help="specify threshold for comparison differences")
    parser.add_argument('--shape', dest="shape", type=int, nargs=2,
                        help="'rows cols' for binary file comparison only")
    parser.add_argument('--dtype', dest='dtype', type=str_to_dtype,
                        help="Data type for binary file comparison only")
    parser.add_argument('file_type', type=_file_type,
                        help="type of files being compare")
    parser.add_argument('file1',
                        help="filename of the first file to compare")
    parser.add_argument('file2',
                        help="filename of the second file to compare")
    args = parser.parse_args(argv)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(3, args.verbosity)])
    kwargs = {"shape": tuple(args.shape), "dtype": args.dtype}

    num_diff = args.file_type(args.file1, args.file2, threshold=args.threshold, **kwargs)

    if num_diff == 0:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
