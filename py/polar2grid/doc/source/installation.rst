Installation
============

The polar2grid python package can be installed in 2 types of environments,
as an individually installed python package or as part of the polar2grid
software bundle.  The software bundle is the preferred, recommended,
and intended method of installing the polar2grid software for
non-developmental use.

Polar2grid provides unit tests for most of its components including sample
datasets that can be run and verified against expected output. For more
information on unit tests, verifying your installation, and running the
tests see the :doc:`tests/index` page.

polar2grid Software Bundle Install
----------------------------------

The polar2grid software bundle is a pre-compiled set of software required
to run the polar2grid scripts.  It includes a minimal python 2.7 install,
with the various packages required by the polar2grid python package. It is
self-contained except for minimal system dependencies (system libraries that
come with most Linux operating systems). Besides the python
packages used with polar2grid and the libraries those depend on, the software
bundle provides statically compiled ms2gt utilities. The ms2gt utilities will
operate on a wider range of systems because they are statically compiled.
The software bundle is only
supported on x86_64 RHEL systems, but may work on other Linux systems as well.

Once the software bundle tarball is on the destination system it can be
installed first by untarring it::

    tar -xzf polar2grid_softwarebundle.tar.gz

Next, add this line to your ``.bash_profile``::

    export POLAR2GRID_HOME=/path/to/softwarebundle

Without any other work, polar2grid :term:`bundle scripts` (as opposed to the
python package scripts) must be used to run any processing of
satellite data to gridded data format. These :term:`bundle scripts` setup the
rest of the environment and provide command line defaults.

See :doc:`Glue Scripts <glue_scripts/index>` for more information on running polar2grid.
The glue script documentation assumes the above for command line examples, but
to reduce typing the following can also be added to your ``.bash_profile``::

    export PATH=$POLAR2GRID_HOME/bin:$PATH

which allows you to remove the ``$POLAR2GRID_HOME/bin/`` portion of the
command line examples.

See the :doc:`Developer's Guide <dev_guide/index>` for python package installing or
other options for running polar2grid scripts.

polar2grid Software Bundle Uninstall/Upgrade
--------------------------------------------

To uninstall the polar2grid software bundle, simply remove the software
bundle directory that was originally created::

    rm -r /path/to/softwarebundle

If you are permanently removing polar2grid you should also remove the
``POLAR2GRID_HOME`` line from your ``.bash_profile`` file.

If you are updating polar2grid first uninstall polar2grid by removing the
directory as above, then follow the installation instructions making sure
to update the ``POLAR2GRID_HOME`` line in your ``.bash_profile`` to point to
the new software bundle directory.

Python Package Install
----------------------

If you would like more control over your python/polar2grid environment
you can install the polar2grid python package like any basic python egg:

    ``easy_install -f http://larch.ssec.wisc.edu/cgi-bin/repos.cgi polar2grid``

Installing polar2grid in this way does require, however, that the ms2gt
utilities ``ll2cr`` and ``fornav`` must be in your $PATH environment
variable. The newest version of ms2gt used by polar2grid is available
`here <http://www.ssec.wisc.edu/~davidh/polar2grid/ms2gt/>`_. Once
untarred (``tar -xzf <tar.gz file>``), the binaries are located in the
``bin`` directory.
The polar2grid python package also has python package dependencies, but those
will be installed automatically.

Installing from Source
----------------------

To use the most recent changes and bug fixes of polar2grid you can install the
packages directly from the source. This method allows you to customize your
python and dependency locations to your preference. Installing from source
code is the same method used by developers of polar2grid and as such the
instructions mention contributing to the project, but this is entirely
optional.

This method is the only way to run polar2grid on non-Linux systems since the
software bundle is only available for Linux. This means that there will be
no wrapper shell scripts (`viirs2gtiff.sh`), but that python modules must
be called directly,
ex. :doc:`python -m polar2grid.viirs2gtiff <glue_scripts/index>`.
This also means that dependencies will have to be installed by the user since
ShellB3 is Linux only.

Instruction can be found here: :doc:`dev_guide/dev_env`
