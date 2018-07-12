#!/bin/bash

export PATH=/data/users/kkolman/miniconda2/bin:$PATH
#export POLAR2GRID_HOME=/data/dist/polar2grid-swbundle-2.2.1b0

conda remove -y --name p2g_test --all
conda create -y -c conda-forge -n p2g_test python=3 behave
source activate p2g_test
cd "$WORKSPACE"
./create_software_bundle.sh test_swbundle /data/dist/ShellB3-Linux-x86_64-CentOS6-20161115-rGIT95e89b0c-portable-core-polar2grid.tar.xz
export POLAR2GRID_HOME="$WORKSPACE/test_swbundle"
cd "$WORKSPACE"/integration_tests
behave --no-logcapture --no-color --no-capture
exit_status=$?
source deactivate p2g_test
exit $exit_status
