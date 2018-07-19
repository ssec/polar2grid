#!/bin/bash

export PATH=/data/users/kkolman/miniconda2/bin:$PATH
#export POLAR2GRID_HOME=/data/dist/polar2grid-swbundle-2.2.1b0

conda remove -y --name p2g_env --all

conda create -y -c conda-forge -n p2g_env python=3 behave satpy netcdf4 gdal 
cd "$WORKSPACE"
source activate p2g_env

#conda install -c anaconda pyyaml

#conda install -c conda-forge pyresample pyorbital satpy #pyshp #aggdraw pycoast #numpy netcdf4 pyhdf scipy pyproj matplotlib sphinx h5py setuptools trollimage

#python setup.py install

#/data/users/kkolman/integration_tests/polar2grid/create_software_bundle.sh test_swbundle

mkdir -p p2g_conda_env
conda pack -n p2g_env
chmod 664 p2g_env.tar.gz
mv p2g_env.tar.gz ./p2g_conda_env

exit


/data/users/kkolman/integration_tests/polar2grid/mcreate_software_bundle.sh test_swbundle /data/dist/ShellB3-Linux-x86_64-CentOS6-20161115-rGIT95e89b0c-portable-core-polar2grid.tar.xz
#./create_software_bundle.sh test_swbundle /data/dist/ShellB3-Linux-x86_64-CentOS6-20170313-rGIT3fd7cee5-portable-core-polar2grid.tar.xz
export POLAR2GRID_HOME="$WORKSPACE/test_swbundle"
cd "$WORKSPACE"/integration_tests
behave --no-logcapture --no-color --no-capture
exit_status=$?
source deactivate p2g_env
exit $exit_status
