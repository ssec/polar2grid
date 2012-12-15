#!/usr/bin/env bash
### VIIRS2AWIPS ENVIRONMENT SETUP ###

# Only load the environment if it hasn't been done already
if [ -z "$POLAR2GRID_REV" ]; then
    if [ -z "$POLAR2GRID_HOME" ]; then 
      export POLAR2GRID_HOME="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
    fi

    # Add all polar2grid scripts to PATH
    export PATH=$POLAR2GRID_HOME/bin:$PATH
    # Add ShellB3 to PATH
    export PATH=$POLAR2GRID_HOME/ShellB3/bin:$PATH
    # Don't let someone else's PYTHONPATH mess us up
    unset PYTHONPATH

    export POLAR2GRID_REV="$Id$"
fi

