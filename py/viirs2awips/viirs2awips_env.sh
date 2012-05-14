#!/usr/bin/env bash
### VIIRS2AWIPS ENVIRONMENT SETUP ###

if [ -z "$POLAR2GRID_HOME" ]; then 
  export POLAR2GRID_HOME="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
fi
#echo "POLAR2GRID_HOME is " $POLAR2GRID_HOME

EGG_LOC=$POLAR2GRID_HOME/polar2grid
PKG_BASE=$EGG_LOC/polar2grid
export PYTHONPATH=$EGG_LOC:$PYTHONPATH
#echo "PYTHONPATH is " $PYTHONPATH
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


