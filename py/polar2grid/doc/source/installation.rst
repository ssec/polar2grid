Installation
============

The polar2grid python package can be installed in 2 types of environments,
as an individually installed python package or as part of the polar2grid
software bundle.  The software bundle is the preferred, recommended,
and intended method of installing the polar2grid software for
non-developmental use.

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

polar2grid Test Bundles
-----------------------

Test scripts are available to test the installation of the polar2grid
software bundle.  The following are descriptions of each test case bundle
and instructions on how to install and run them.

.. toctree::
    :numbered:

    tests/p2g_v2a_ak
    tests/p2g_v2g_basic

