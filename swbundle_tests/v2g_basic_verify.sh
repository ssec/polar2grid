#!/usr/bin/env bash
### Verify simple test products with known products ###
# Should be renamed verify.sh in the corresponding test tarball
#
# Copyright (C) 2013 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    January 2013
#     University of Wisconsin-Madison 
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu

oops() {
    echo "OOPS: $*"
    echo "FAILURE"
    exit 1
}

# Setup viirs2gtiff environment
if [ -z "$POLAR2GRID_HOME" ]; then
    oops "POLAR2GRID_HOME needs to be defined"
fi
if [ ! -d "$POLAR2GRID_HOME" ]; then
    oops "POLAR2GRID_HOME does not exist: $POLAR2GRID_HOME"
fi

source $POLAR2GRID_HOME/bin/polar2grid_env.sh || oops "Could not find 'bin/polar2grid_env.sh' in POLAR2GRID_HOME"

# Find out where the tests are relative to this script
TEST_BASE="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Base directory for all test cases is $TEST_BASE"
VERIFY_BASE=$TEST_BASE/verify

# Check if they specified a different working directory
if [ $# -ne 1 ]; then
    oops "Must specify a working directory"
else
    echo "Will use $1 directory"
    WORK_DIR=$1
fi

if [ ! -d $WORK_DIR ]; then
    oops "Working directory $WORK_DIR does not exist"
fi

# Run tests for each test data directory in the base directory
BAD_COUNT=0
for VFILE in $VERIFY_BASE/*; do
    WFILE=$WORK_DIR/`basename $VFILE`
    if [ ! -f $WFILE ]; then
        oops "ERROR: Could not find output file $WFILE"
        BAD_COUNT=$(($BAD_count + 1))
        continue
    fi
    echo "Comparing $WFILE to known valid file"
    $POLAR2GRID_HOME/ShellB3/bin/python <<EOF
from osgeo import gdal
import numpy

work_gtiff  = gdal.Open("$WFILE", gdal.GA_ReadOnly)
valid_gtiff = gdal.Open("$VFILE", gdal.GA_ReadOnly)

work_data = work_gtiff.GetRasterBand(1).ReadAsArray()
valid_data = valid_gtiff.GetRasterBand(1).ReadAsArray()

if work_data.shape != valid_data.shape:
    print "ERROR: Data shape for '$WFILE' is not the same as the valid '$VFILE'"
    sys.exit(1)

total_pixels = work_data.shape[0] * work_data.shape[1]
equal_pixels = len(numpy.nonzero( work_data == valid_data )[0])
if equal_pixels != total_pixels:
    print "FAIL: %d pixels out of %d pixels are different" % (total_pixels-equal_pixels,total_pixels)
    sys.exit(2)
print "SUCCESS: %d pixels out of %d pixels are different" % (total_pixels-equal_pixels,total_pixels)
EOF
    [ $? -eq 0 ] || BAD_COUNT=$(($BAD_COUNT + 1))
done

if [ $BAD_COUNT -ne 0 ]; then
    oops "$BAD_COUNT files were found to be unequal"
fi

# End of all tests
echo "All files passed"
echo "SUCCESS"

