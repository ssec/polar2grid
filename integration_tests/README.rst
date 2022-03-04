How to run the tests in your own environment
============================================

Navigate to your Polar2Grid directory, then run::

    conda env update -n jenkins_p2g_docs -f build_environment.yml
    conda env update -n jenkins_p2g_docs -f jenkins_environment.yml
    conda activate jenkins_p2g_docs
    pip install .
    conda env update -n jenkins_p2g_swbundle -f build_environment.yml
    conda activate jenkins_p2g_swbundle
    # Creates a folder with the necessary scripts to run the tests.
    ./create_conda_software_bundle.sh polar2grid-`date +%Y%m%d-%H%M%S`
    conda activate jenkins_p2g_docs
    export POLAR2GRID_HOME=polar2grid-`date +%Y%m%d-%H%M%S`
    cd integration_tests
    # Runs the tests.
    behave --no-logcapture --no-capture --no-color -D datapath=/path/to/test/data

To run a specific test, add the argument ``--name TESTNAME`` when running behave. The test names can be
found in the feature files (for example: ``--name VIIRS_L1B`` would skip all tests except VIIRS_L1B).

How to add tests
================
Tests are found under ``integration_tests/features/``. There are two test files, ``geo2grid.feature`` and
``polar2grid.feature``. Each is composed hierarchically in this way: A ``Feature`` which contains a
name and description, a ``Scenario Outline`` which details how the tests are ran, and finally ``Examples``
with each containing a name and the specifics to pass into ``Scenario Outline`` (command, source, output).
`command` should be the full shell command that you want to run with the `-f` flag last. source and output are
directories containing input and expected output files respectively. To add a test, simply add another line to
an existing ``Examples`` block or make a new ``Examples`` block following the format that is already there.
For more information please see the official behave documentation:
https://behave.readthedocs.io/en/latest/tutorial.html

How Jenkins runs the tests
==========================

Jenkins runs a script that follows similar steps as above. The script can be found in ``integration_tests/run.sh``.

Jenkins home is on bumi.ssec.wisc.edu using port 8080, and data can be found in bumi:/data/test_data

How to upgrade the version of Python used by Jenkins
====================================================

Jenkins and the released software bundle are based on two conda
environments: ``jenkins_p2g_docs`` and ``jenkins_p2g_docs``. Both
of these environments currently live in:
``/var/lib/jenkins/mambaforge/envs/``. In order to upgrade the version of
Python that the software bundle will use we must upgrade these environments.
However, a simple ``conda update`` rarely works with an update of Python
itself. To work around this we must delete the environments.

1. Update the version of python in the ``build_environment.yml`` file in the
   root of this repository.
2. Login to ``bumi`` and switch to the root account (``sudo -iu root``).
3. Run ``sudo -u jenkins /var/lib/jenkins/mambaforge/bin/conda update -n base conda``
   to update conda itself.
4. Run ``sudo -u jenkins /var/lib/jenkins/mambaforge/bin/conda env remove -n jenkins_p2g_docs``.
5. Run ``sudo -u jenkins /var/lib/jenkins/mambaforge/bin/conda env remove -n jenkins_p2g_swbundle``.
6. Rerun the CI jobs from the Jenkins web UI.
