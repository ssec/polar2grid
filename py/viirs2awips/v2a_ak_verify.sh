#!/usr/bin/env bash
### Verify simple test products with known products ###
# Should be renamed verify.sh in the corresponding test tarball

oops() {
    echo "OOPS: $*"
    echo "FAILURE"
    exit 1
}

# Setup viirs2awips environment
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
    WORK_DIR=./p2g-v2a-ak-tests
else
    echo "Will use $1 directory"
    WORK_DIR=$1
fi

if [ ! -d $WORK_DIR ]; then
    oops "Working directory $WORK_DIR does not exist"
fi

# Run tests for each test data directory in the base directory
for VFILE in $VERIFY_BASE/*; do
    WFILE=$WORK_DIR/`basename $VFILE`
    if [ ! -f $WFILE ]; then
        oops "Could not find output file $WFILE"
    fi
    diff $VFILE $WFILE || oops "$WFILE was different than expected"
    $POLAR2GRID_HOME/ShellB3/bin/python <<EOF
from netCDF4 import Dataset
import numpy
import sys

nc1_name  = "$VFILE"
nc2_name  = "$WFILE"
threshold = 1

nc1 = Dataset(nc1_name, "r")
nc2 = Dataset(nc2_name, "r")
image1_var = nc1.variables["image"]
image2_var = nc2.variables["image"]
image1_var.set_auto_maskandscale(False)
image2_var.set_auto_maskandscale(False)
if len(numpy.nonzero(numpy.abs(image2_var[:] - image1_var[:]) >= threshold)[0]) != 0:
    sys.exit(1)
else:
    sys.exit(0)

EOF
[ $? -eq 0 ] || oops "$WFILE" was different than expected"

done

# End of all tests
echo "SUCCESS"

