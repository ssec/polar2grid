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
"""Take a NetCDF file compatible with AWIPS or NCEP grids and replace
all image data with an array of NaNs.  The output file should be used
as a template: copied to a new location and then filled with actual
image data.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2014
:license:      GNU GPLv3
"""
import os
import sys
import shutil
import logging
from netCDF4 import Dataset

LOG = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.DEBUG)
    usage = """
Usage: python nc_to_template.py <input nc> <output nc>
"""
    args = sys.argv[1:]
    if len(args) != 2:
        LOG.error("Requires 2 arguments: input file and output file")
        print(usage)
        return -1

    input_file = os.path.abspath(args[0])
    output_file = os.path.abspath(args[1])

    if not os.path.exists(input_file):
        LOG.error("Input file %s does not exist" % input_file)
        return -1

    if os.path.exists(output_file):
        LOG.error("Output file %s already exists" % output_file)
        return -1

    # Copy the original to the template location
    try:
        LOG.debug("Copying input file to output file location")
        shutil.copyfile(input_file, output_file)
    except OSError:
        LOG.error("Could not move input file to output location", exc_info=1)
        return -1

    # Open the template file
    try:
        LOG.debug("Opening output file to fill in data")
        nc = Dataset(output_file, "a")#, format="NETCDF3_CLASSIC")
    except OSError:
        LOG.error("Error trying to open NC file")
        try:
            LOG.debug("Trying to remove file that couldn't be opened %s" % output_file)
            os.remove(output_file)
        except OSError:
            LOG.warning("Bad output file could not be removed %s" % output_file)
        finally:
            return -1

    if nc.file_format != "NETCDF3_CLASSIC":
        LOG.warning("Expected file format NETCDF3_CLASSIC got %s" % nc.file_format)

    # Change the data to all NaNs
    if "image" not in nc.variables:
        LOG.error("NC variable 'image' does not exist in %s" % input_file)
        return -1

    columns,rows = nc.variables["image"].shape
    del nc.variables["image"]
    #nc.variables["image"][:] = repeat(repeat([[nan]], columns, axis=1), rows, axis=0)
    nc.variables["validTime"][:] = 0
    nc.close()

    LOG.info("Template created successfully")
    return 0
    
if __name__ == "__main__":
    sys.exit(main())
