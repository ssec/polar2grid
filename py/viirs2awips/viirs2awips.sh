#!/bin/bash
### VIIRS2AWIPS WRAPPER ###
# Assumes that it is called from the temporary directory where files should be placed

PROJECT_DIR=$PWD

if [ -z "$POLAR2GRID_HOME" ]; then 
  export POLAR2GRID_HOME="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
fi
#echo "POLAR2GRID_HOME is " $POLAR2GRID_HOME

EGG_LOC=$POLAR2GRID_HOME/polar2grid
PKG_BASE=$EGG_LOC/polar2grid
export PYTHONPATH=$EGG_LOC:$PYTHONPATH
#echo "PYTHONPATH is " $PYTHONPATH
export PATH=$POLAR2GRID_HOME/ms2gt/bin:$PATH
#echo "PATH is " $PATH

# Script config file locations
if [ -z "$VIIRS_GRIDS_CONFIG" ]; then
  export VIIRS_GRIDS_CONFIG=$PKG_BASE/awips_grids.conf
fi

if [ -z "$VIIRS_ANCIL_DIR" ]; then
  export VIIRS_ANCIL_DIR=$PKG_BASE/grids/
fi

if [ -z "$VIIRS_SHAPE_CONFIG" ]; then
  export VIIRS_SHAPE_CONFIG=$PKG_BASE/awips_shapes.conf
fi

# Go back to the directory this was called from
cd $PROJECT_DIR

# Test configs/Egg installation
#$POLAR2GRID_HOME/ShellB3/bin/python -m polar2grid.awips_config

# Call the python module to do the processing, passing all arguments
$POLAR2GRID_HOME/ShellB3/bin/python -m polar2grid.viirs2awips -vv $@
