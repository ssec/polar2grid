#!/bin/bash
# script for jenkins to run tests on polar2grid

cd "$WORKSPACE"
mkdir -p integration_tests/jenkins_p2g_env

# environment already has polar2grid installed on it
tar -xzf /data/users/kkolman/integration_tests/polar2grid/integration_tests/tarballs/jenkins_p2g_env.tar.gz -C integration_tests/jenkins_p2g_env
chmod +x integration_tests/jenkins_p2g_env/bin/activate
ls -l integration_tests/jenkins_p2g_env/bin/activate
source integration_tests/jenkins_p2g_env/bin/activate
tarball_name="polar2grid-swbundle-`date +"%Y%m%d-%H%M%S"`"
./create_conda_software_bundle.sh ${tarball_name}
export POLAR2GRID_HOME="$WORKSPACE/$tarball_name"
cd "$WORKSPACE/integration_tests"
behave --no-logcapture --no-color --no-capture -D datapath=/data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data
exit $?
