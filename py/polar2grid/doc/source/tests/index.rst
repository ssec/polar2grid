Unit Tests
----------

Polar2grid provides unit tests for testing individual polar2grid components or
entire glue scripts. Some of these tests require the user to provide sample
datasets for the software to process. The following sections describe each output
dataset, the input dataset they require, and the commands that are run.

Unit tests are run from a python module. With a properly setup environment
they can be run from the command line::

    python -m polar2grid.test <base_dir> <output_directory>

For more information and other command line options::

    python -m polar2grid.test -h

# TODO
