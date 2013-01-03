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
for VFILE in $VERIFY_BASE/*; do
    WFILE=$WORK_DIR/`basename $VFILE`
    if [ ! -f $WFILE ]; then
        oops "Could not find output file $WFILE"
    fi
    echo "Comparing $WFILE to known valid file"
    diff $WFILE $VFILE || oops "$WFILE was different than expected"
done

# End of all tests
echo "SUCCESS"

