How to run the tests in own environment
=======================================

Navigate to your Polar2Grid directory, then run::
    source integration_tests/p2g_env/bin/activate                       # Activates the python environment
    ./mod_create_software_bundle.sh software_bundle                     # Creates a folder with the necessary scripts to run the tests
    export POLAR2GRID_HOME=/path/to/polar2grid/dir/software_bundle      # If not already in your .bash_profile
    python setup.py install                                             # Installs Polar2Grid
    cd integration_tests
    tar -xzf p2g_test_data.tar.xz                                       # Extracts the test data
    behave --no-logcapture --no-capture --no-color                      # Runs the tests

To run a specific test, add the argument ``--name TESTNAME`` when running behave.





