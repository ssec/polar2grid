#!/usr/bin/env bash
### VIIRS2AWIPS ENVIRONMENT SETUP ###

# Only load the environment if it hasn't been done already
if [ -z "$POLAR2GRID_REV" ]; then
    if [ -z "$POLAR2GRID_HOME" ]; then 
      export POLAR2GRID_HOME="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
    fi

    EGG_LOC=$POLAR2GRID_HOME/python

    export PATH=$POLAR2GRID_HOME/bin:$PATH
    export PYTHONPATH=$EGG_LOC:$PYTHONPATH

    # Script config file locations
    #if [ -z "$VIIRS_GRIDS_CONFIG" ]; then
    #  export VIIRS_GRIDS_CONFIG=$PKG_BASE/awips/awips_grids.conf
    #fi

    #if [ -z "$VIIRS_ANCIL_DIR" ]; then
    #  export VIIRS_ANCIL_DIR=$PKG_BASE/grids/
    #fi

    #if [ -z "$VIIRS_SHAPE_CONFIG" ]; then
    #  export VIIRS_SHAPE_CONFIG=$PKG_BASE/awips/awips_shapes.conf
    #fi

    export POLAR2GRID_REV="$Id$"
fi

