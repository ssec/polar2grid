#!/usr/bin/env python3
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

from os.path import exists
import sys

import logging
import numpy

LOG = logging.getLogger(__name__)


def compare_array(array1, array2, atol=0., rtol=0., margin_of_error=0.):
    """Compare 2 binary arrays per pixel

    Two pixels are considered different if the absolute value of their
    difference is greater than 1. This function assumes the arrays are
    in useful data types, which may cause erroneous results. For example,
    if both arrays are unsigned integers and the different results in a
    negative value overflow will occur and the threshold will likely not
    be met.

    :arg array1:        numpy array for comparison
    :arg array2:        numpy array for comparison
    :keyword atol: float threshold

    :returns: number of different pixels
    """
    if array1.shape != array2.shape:
        LOG.error("Data shapes were not equal")
        raise ValueError("Data shapes were not equal")

    total_pixels = array1.size
    equal_pixels = numpy.count_nonzero(numpy.isclose(array1, array2, rtol=rtol, atol=atol, equal_nan=True))
    diff_pixels = total_pixels - equal_pixels
    if diff_pixels > margin_of_error / 100 * total_pixels:
        LOG.warning("%d pixels out of %d pixels are different" % (diff_pixels, total_pixels))
        return 1
    LOG.info("%d pixels out of %d pixels are different" % (diff_pixels, total_pixels))
    return 0


def compare_binary(fn1, fn2, shape, dtype, atol=0., margin_of_error=0., **kwargs):
    array1 = numpy.memmap(fn1, shape=shape, dtype=dtype, mode='r')
    array2 = numpy.memmap(fn2, shape=shape, dtype=dtype, mode='r')

    return compare_array(array1, array2, atol=atol, margin_of_error=margin_of_error)


def compare_geotiff(gtiff_fn1, gtiff_fn2, atol=0., margin_of_error=0., **kwargs):
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

    return compare_array(array1, array2, atol=atol, margin_of_error=margin_of_error)


def compare_awips_netcdf(nc1_name, nc2_name, atol=0., margin_of_error=0., **kwargs):
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

    return compare_array(image1_data, image2_data, atol=atol, margin_of_error=margin_of_error)


def compare_netcdf(nc1_name, nc2_name, variables, atol=0., margin_of_error=0., **kwargs):
    from netCDF4 import Dataset
    nc1 = Dataset(nc1_name, "r")
    nc2 = Dataset(nc2_name, "r")
    num_diff = 0
    for v in variables:
        image1_var = nc1[v]
        image2_var = nc2[v]
        image1_var.set_auto_maskandscale(False)
        image2_var.set_auto_maskandscale(False)
        LOG.debug("Comparing data for variable '{}'".format(v))
        num_diff += compare_array(image1_var, image2_var, atol=atol, margin_of_error=margin_of_error)
    return num_diff

type_name_to_compare_func = {
    "binary": compare_binary,
    "gtiff": compare_geotiff,
    "geotiff": compare_geotiff,
    "awips": compare_awips_netcdf,
    "netcdf": compare_netcdf,
}


def _file_type(str_val):
    str_val = str_val.lower()
    if str_val in type_name_to_compare_func:
        return type_name_to_compare_func[str_val]

    print("ERROR: Unknown file type '%s'" % (str_val,))
    print("Possible file types: \n\t%s" % ("\n\t".join(type_name_to_compare_func.keys())))
    raise ValueError("Unknown file type '%s'" % (str_val,))


def main(argv=sys.argv[1:]):
    from argparse import ArgumentParser
    from polar2grid.core.dtype import str_to_dtype
    parser = ArgumentParser(description="Compare two files per pixel")
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
                        help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument('--atol', type=float, default=0.,
                        help="specify threshold for comparison differences (see numpy.isclose 'atol' parameter)")
    parser.add_argument('--rtol', type=float, default=0.,
                        help="specify relative tolerance for comparison (see numpy.isclose 'rtol' parameter)")
    parser.add_argument('--shape', dest="shape", type=int, nargs=2, default=(None, None),
                        help="'rows cols' for binary file comparison only")
    parser.add_argument('--dtype', type=str_to_dtype,
                        help="Data type for binary file comparison only")
    parser.add_argument('--variables', nargs='+',
                        help='NetCDF variables to read and compare')
    parser.add_argument('--margin-of-error', type=float, default=0.,
                        help='percent of total pixels that can be wrong')
    parser.add_argument('file_type', type=_file_type,
                        help="type of files being compare")
    parser.add_argument('file1',
                        help="filename of the first file to compare")
    parser.add_argument('file2',
                        help="filename of the second file to compare")
    args = parser.parse_args(argv)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(3, args.verbosity)])
    kwargs = {"shape": tuple(args.shape), "dtype": args.dtype, 'variables': args.variables}

    if not exists(args.file1):
        LOG.error('Could not find file {}'.format(args.file1))
        return 1
    if not exists(args.file2):
        LOG.error('Could not find file {}'.format(args.file2))
        return 1
    return args.file_type(args.file1, args.file2, atol=args.atol, rtol=args.rtol,
                          margin_of_error=args.margin_of_error, **kwargs)


if __name__ == "__main__":
    sys.exit(main())
