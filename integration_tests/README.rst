How to run the tests in own environment
=======================================

Navigate to your Polar2Grid directory, then run::

    conda env update -n jenkins_p2g_docs -f build_environment.yml -f jenkins_environment.yml
    conda activate jenkins_p2g_docs
    pip install .
    conda env update -n jenkins_p2g_swbundle -f build_environment.yml
    conda activate jenkins_p2g_swbundle
    # Creates a folder with the necessary scripts to run the tests.
    ./create_conda_software_bundle.sh polar2grid-`date +%Y%m%d-%H%M%S`
    conda activate jenkins_p2g_docs
    # If not already in your .bash_profile.
    export POLAR2GRID_HOME=polar2grid-`date +%Y%m%d-%H%M%S`/bin
    cd integration_tests
    # Runs the tests.
    behave --no-logcapture --no-capture --no-color -D datapath=/path/to/test/data

To run a specific test, add the argument ``--name TESTNAME`` when running behave. The test names can be
found in the feature files (for example: ``--name VIIRS_L1B`` would skip all tests except VIIRS_L1B).

How Jenkins runs the tests
==========================

Jenkins runs a script that follows similar steps as above. The script can be found in ``integration_tests/run.sh``.

Jenkins home is on bumi.ssec.wisc.edu using port 8080, and data can be found in bumi:/data/test_data
