#!/usr/bin/env bash
### Run simple tests to verify viirs2awips will run properly ###
# Should be renamed run.sh in the corresponding test tarball


oops() {
    echo "OOPS: $*"
    echo "FAILURE"
    exit 1
}

run_test() {
    echo "Running test for data in $2..."
    viirs2awips.sh -g $1 -d $2
    if [ $? -ne 0 ]; then
        echo "ERROR: viirs2awips.sh did not complete test $2 successfully"
        echo "ERROR: Won't remove test directory, check it for more information"
        echo "FAILURE"
        exit 2
    fi
}

# Setup viirs2awips environment
if [ -z "$POLAR2GRID_HOME" ]; then
    oops "POLAR2GRID_HOME needs to be defined"
fi
source $POLAR2GRID_HOME/bin/polar2grid_env.sh

# Find out where the tests are relative to this script
TEST_BASE="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Base directory for all test cases is $TEST_BASE"

# Make sure we can call viirs2awips.sh before making any test directories
which viirs2awips.sh || oops "viirs2awips.sh is not in PATH"

# Check if they specified a different working directory
if [ $# -ne 1 ]; then
    WORK_DIR=./p2g-v2a-ak-tests-$$
else
    echo "Will use $1 directory, but won't delete it"
    WORK_DIR=$1
fi

echo "Making temporary test directory $WORK_DIR"
mkdir -p $WORK_DIR || oops "Could not create test directory '$WORK_DIR'"
cd $WORK_DIR

# Run tests for each test data directory in the base directory
for DDIR in $TEST_BASE/*; do
    if [ -d $DDIR ] && [ `basename $DDIR` != "verify" ]; then
        # Make a unique working test directory
        TDIR=`basename $DDIR`-$$
        echo "Making temporary working directory $TDIR"
        mkdir -p $TDIR || oops "Couldn't make $TDIR test directory"
        pushd $TDIR

        run_test 203 $DDIR
        # Move all NetCDF files here
        mv SSEC_AWIPS_VIIRS-* ../ || oops "No NC files created for $DDIR in $TDIR"

        popd
        echo "Removing test dir $TDIR"
        rm -r $TDIR || oops "Couldn't remove $TDIR test directory"
    fi
done

# Generate NC product images
$POLAR2GRID_HOME/ShellB3/bin/python -m polar2grid.plot_ncdata --vmin=0 --vmax=255 || oops "Could not generate png images from NC files.\n\tNC files were still created however."

# End of all tests
echo "SUCCESS"

