How to run the tests in own environment
=======================================

Navigate to your Polar2Grid directory, then run::

    conda env update -n jenkins_p2g_docs -f build_environment.yml
    conda env update -n jenkins_p2g_docs -f jenkins_environment.yml
    conda activate jenkins_p2g_docs
    pip install .
    conda env update -n jenkins_p2g_swbundle -f build_environment.yml
    conda activate jenkins_p2g_swbundle
    ./create_conda_software_bundle.sh polar2grid-YYYYMMDD-HHmmSS                                    # Creates a folder with the necessary scripts to run the tests
    conda activate jenkins_p2g_docs
    export POLAR2GRID_HOME=polar2grid-YYYYMMDD-HHmmSS                                               # If not already in your .bash_profile
    cd integration_tests
    behave --no-logcapture --no-capture --no-color -D datapath=/path/to/test/data                   # Runs the tests

To run a specific test, add the argument ``--name TESTNAME`` when running behave. The test names can be
found in the feature file.

How Jenkins runs the tests
==========================

Jenkins runs a script that follows the same steps as above. The script can be found in ``integration_tests/run.sh``.

Jenkins home is on bumi.ssec.wisc.edu using port 8080, and data can be found in
bumi:/data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data

