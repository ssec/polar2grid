#!/bin/bash
# script for jenkins to run tests on polar2grid

cd "$WORKSPACE"

# environment already has polar2grid installed on it
old_list=`/data/users/davidh/anaconda3/bin/conda list -n jenkins_p2g_env`
/data/users/davidh/anaconda3/bin/conda env update -n jenkins_p2g_env -f build_environment.yml
/data/users/davidh/anaconda3/bin/conda install -n jenkins_p2g_env behave
new_list=`/data/users/davidh/anaconda3/bin/conda list -n jenkins_p2g_env`
echo $new_list
/data/users/davidh/anaconda3/bin/conda init bash
source ~/.bashrc
source activate jenkins_p2g_env
if [ "$old_list" != "$new_list" ]; then
    tarball_name="polar2grid-swbundle-`date +"%Y%m%d-%H%M%S"`"
    ./create_conda_software_bundle.sh "$WORKSPACE/$tarball_name"
    export POLAR2GRID_HOME="$WORKSPACE/$tarball_name"
fi
cd "$WORKSPACE/integration_tests"
behave --no-logcapture --no-color --no-capture -D datapath=/data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data
exit $?
