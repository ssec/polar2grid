#!/usr/bin/env bash
### Run simple tests to verify viirs2awips will run properly ###
# Should be renamed run.sh in the corresponding test tarball


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

# Generate NC product images
$POLAR2GRID_HOME/ShellB3/bin/python -m polar2grid.plot_ncdata $@ || oops "Could not generate png images from NC files."

# End of all tests
echo "SUCCESS"

