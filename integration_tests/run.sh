#!/bin/bash
# script for jenkins to run tests on polar2grid

#export PATH=/data/users/kkolman/miniconda2/bin:$PATH

cd "$WORKSPACE"

mkdir integration_tests/jenkins_p2g_env
# environment already has polar2grid installed on it
tar -xzf /data/users/kkolman/integration_tests/polar2grid/integration_tests/jenkins_p2g_env.tar.gz -C $WORKSPACE/integration_tests/jenkins_p2g_env

#conda remove -y --name jp2g_env --all
#conda create -y -c conda-forge -n jp2g_env python=3 behave numpy netcdf4 gdal scipy h5py pyhdf
#source activate jp2g_env
source integration_tests/jenkins_p2g_env/bin/activate

#pip install "satpy<0.9" pyorbital
./mod_create_software_bundle.sh test_swbundle
#python setup.py install   # once you get the env to download from an external source, but already installed in p2g_env
#export POLAR2GRID_HOME="/data/users/kkolman/integration_tests/polar2grid/test_swbundle5"
export POLAR2GRID_HOME="$WORKSPACE/test_swbundle"
cd "$WORKSPACE/integration_tests"
behave --no-logcapture --no-color --no-capture -D datapath=/data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data
exit $?
