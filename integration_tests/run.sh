#!/bin/bash
# Script for jenkins to run tests on polar2grid.

rm -rf /data/users/wroberts/docs
cd "$WORKSPACE"
# Activate conda for bash.
/data/users/davidh/anaconda3/bin/conda init bash
# Restart the shell to enable conda.
source ~/.bashrc
conda remove -y -n jenkins_p2g_env --all
conda env update -n jenkins_p2g_env -f build_environment.yml
conda activate jenkins_p2g_env

time=`date +"%Y%m%d-%H%M%S"`
tarball_name=polar2grid-swbundle-$time
./create_conda_software_bundle.sh $WORKSPACE/$tarball_name
export POLAR2GRID_HOME="$WORKSPACE/$tarball_name"
cd "$WORKSPACE/integration_tests"
behave --no-logcapture --no-color --no-capture -D datapath=/data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data
# Only run by Jenkins if build was successful.
if [ $? = 0 ]
then
    mkdir /tmp/polar2grid-$time
    # Save software bundle.
    for fn in /tmp/polar2grid-*
    do
        rm -rf $fn
    done
    cp -r $POLAR2GRID_HOME /tmp/polar2grid-$time
    # Make docs.
    conda install -y sphinx
    pip install sphinx-argparse
    cd "$WORKSPACE"/doc
    make html
    cp -r "$WORKSPACE"/doc/build/html /tmp/polar2grid-$time
fi
exit $?