#!/usr/bin/env bash
### VIIRS2AWIPS WRAPPER ###

if [ -z "$POLAR2GRID_HOME" ]; then 
  export POLAR2GRID_HOME="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
fi

# Setup necessary environments
source $POLAR2GRID_HOME/bin/viirs2awips_env.sh

# Call the python module to do the processing, passing all arguments
$POLAR2GRID_HOME/ShellB3/bin/python -m polar2grid.viirs2awips -vv $@

