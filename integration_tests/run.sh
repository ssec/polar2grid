#!/bin/bash

cd $WORKSPACE

source integration_tests/p2g_env/bin/activate
./mod_create_software_bundle.sh test_swbundle
python setup.py install 
export POLAR2GRID_HOME="$WORKSPACE/test_swbundle"

cd "$WORKSPACE/integration_tests"

tar -xzf p2g_test_data.tar.xz
behave --no-logcapture --no-color --no-capture
exit_status=$?
echo $exit_status
source p2g_env/bin/deactivate
exit $exit_status
