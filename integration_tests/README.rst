How to run the tests in own environment
=======================================

Navigate to your Polar2Grid directory, then run::

    cd integration_tests
    tar -xzf p2g_env.tar.xz                                                                         # Extracts the conda environment to be used 
    source integration_tests/p2g_env/bin/activate                                                   # Activates the conda environment
    ./create_software_bundle.sh software_bundle                                                     # Creates a folder with the necessary scripts to run the tests
    export POLAR2GRID_HOME=/path/to/polar2grid/dir/software_bundle                                  # If not already in your .bash_profile
    cd integration_tests 
    tar -xzf p2g_test_data.tar.xz                                                                   # Extracts the test data
    behave --no-logcapture --no-capture --no-color -D datapath=/path/to/test/data script="script"   # For the script, specify either geo2grid or polar2grid for the tests

To run a specific test, add the argument ``--name TESTNAME`` when running behave. The test names can be
found in the feature file.

How Jenkins runs the tests
==========================

Jenkins runs a script that follows the same steps as above with the exception of extracting the test data from a tarball. The
script can be found in ``integration_tests/run.sh``.

