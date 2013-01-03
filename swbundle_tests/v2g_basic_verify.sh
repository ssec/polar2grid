#!/usr/bin/env bash
### Verify simple test products with known products ###
# Should be renamed verify.sh in the corresponding test tarball

oops() {
    echo "OOPS: $*"
    echo "FAILURE"
    exit 1
}

# Setup viirs2gtiff environment
if [ -z "$POLAR2GRID_HOME" ]; then
    oops "POLAR2GRID_HOME needs to be defined"
fi
source $POLAR2GRID_HOME/bin/polar2grid_env.sh

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
        oops "Could not find output file $WFILE"
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

