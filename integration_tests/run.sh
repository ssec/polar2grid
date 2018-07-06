#!/bin/bash
#python integration_tests.py /data/dist/polar2grid-swbundle-2.2.1b0/bin/ config.yaml

#source activate int_tests
#behave --no-color --no-logcapture --no-capture

export PATH=/data/users/kkolman/miniconda2/bin:$PATH

conda remove -y --name p2g_test --all
conda create -y -c conda-forge -n p2g_test python=3 behave
source activate p2g_test
cd /data/users/kkolman/integration_tests/polar2grid/integration_tests
behave --no-logcapture --no-color --no-capture "$WORKSPACE"/integration_tests/features
exit_status=$?
source deactivate p2g_test
exit $exit_status

