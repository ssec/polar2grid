Installation
============

.. include:: global.rst

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
completely self-contained and does not have any outside dependencies.

Once the software bundle tarball is on the destination system it can be
installed first by untarring it::

    tar -xzf polar2grid_softwarebundle.tar.gz

Next, add this line to your ``.bash_profile``::

    export POLAR2GRID_HOME=/path/to/softwarebundle

Without any other work, polar2grid "companion" scripts (as opposed to the
python package scripts) must be used to run any processing of
satellite data to gridded data format. These "companion" scripts setup the
rest of the environment and provide command line defaults.

See :doc:`Glue Scripts <glue_scripts/index>` for more information on running polar2grid.
The glue script documentation assumes the above for command line examples, but
to reduce typing the following can also be added to your ``.bash_profile``::

    export PATH=$POLAR2GRID_HOME/bin:$PATH

which allows you to remove the ``$POLAR2GRID_HOME/bin/`` portion of the
command line examples.

See the :doc:`Developer's Guide </dev_guide>` for python package installing or
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

viirs2awips Alaska Basic
########################

Delivered as a tarball (``p2g-v2a-ak-testsi-<version>.tar.gz``) and can be "installed" by
first untarring it::

    tar -xzf p2g-v2a-ak-tests-<version>.tar.gz

then it can be run using the ``run.sh`` script that is inside the untarred
directory::

    p2g-v2a-ak-tests-<version>/run.sh [destination directory]

.. warning::

    Do NOT run ``run.sh`` from the ``p2g-v2a-ak-tests-<version>`` directory.

where ``destination directory`` is an optional directory name where the test
products should be placed.  By default the products are placed in
``./p2g-v2a-ak-tests-PID``.  Where ``PID`` is a unique identifier created by
the run script.  This command will create NetCDF files and
png images.  If it completes successfully is should print out
``SUCCESS`` as the last line of output.

You can visually compare the png images or you can run the verify
script::

    p2g-v2a-ak-tests-<version>/verify.sh <destination directory>

where ``destination directory`` is the same as for ``run.sh``.  This will
compare the NetCDF files created to NetCDF files that are known to be
correct (stored in the ``p2g-v2a-ak-tests-<version>/verify`` directory.  The comparison
allows for a difference of ``1`` in the AWIPS NetCDF files due to the unlikely
possibility that different machines produce slightly different floating point
results.

Test cases:

    - ak_20120408:
        :Start Time: April 8th, 2012 13:11 UTC
        :End Time: April 8th, 2012 13:26 UTC
        :Bands: DNB,I01,I03,I04,I05
        :Fog Created: Yes
        :Forced Grid: 203
        :Orbit Number: 02315

.. versionchanged:: 1.0.2
    Updated verified data for ms2gt0.23a

.. versionchanged:: 1.0.3
    Updated verified data for ms2gt0.24a and new command-line syntax

viirs2gtiff Alaska Basic
########################

This test is delivered as a tarball (``p2g-v2g-ak-tests-<version>.tar.gz``) and can be
"installed" by untarring it::

    tar -xzf p2g-v2g-ak-<version>.tar.gz

then it can be run using the ``run.sh`` script that is inside the untarred
directory::

    p2g-v2g-ak-tests-<version>/run.sh [destination directory]

.. warning::

    Do NOT run ``run.sh`` from the ``p2g-v2g-ak-<version>`` directory.

where ``destination directory`` is an optional directory name where the test
products should be placed. By default the products are placed in
``./p2g-v2g-ak-tests-PID``. Where ``PID`` is a unique identifier created by
the run script. This command will create Geotiff files.  If it completes
successfully it should print out ``SUCCESS`` as the last line of output.

You can visually compare the geotiff images or you can run the verify script::

    p2g-v2g-ak-tests-<version>/verify.sh <destination directory>

where ``destination directory`` is the same as for ``run.sh``. This will
compare the geotiff files created to geotiff files that are known to be
correct (stored in the ``p2g-v2g-ak-tests-<version>/verify`` directory. The
comparison uses the UNIX ``diff`` utility so the files must be exact. This may
cause some machines to fail the comparison due to small differences with
floating point operations.

Test cases:

    - ak_20120408:
        :Start Time: April 8th, 2012 13:11 UTC
        :End Time: April 8th, 2012 13:21 UTC
        :Bands: DNB,I04
        :Fog Created: No
        :Forced Grid: :doc:`wgs84_fit <grids>`
        :Orbit Number: 02315

viirs2gtiff East Conus Basic
############################

This test is delivered as a tarball (``p2g-v2g-econus-<version>.tar.gz``) and
can be "installed" by untarring it::

    tar -xzf p2g-v2g-econus-<version>.tar.gz

then it can be run using the ``run.sh`` script that is inside the untarred
directory::

    p2g-v2g-econus-tests-<version>/run.sh [destination directory]

.. warning::

    Do NOT run ``run.sh`` from the ``p2g-v2g-econus-<version>`` directory.

where ``destination directory`` is an optional directory name where the test
products should be placed. By default the products are placed in
``./p2g-v2g-econus-tests-PID``. Where ``PID`` is a unique identifier created
by the run script. This command will create Geotiff files. If it completes
successfully it should print out ``SUCCESS`` as the last line of output.

You can visually compare the geotiff images or you can run the verify script::

    p2g-v2g-econus-<version>/verify.sh <destination directory>

where ``destination directory`` is the same as for ``run.sh``. This will
compare geotiff files created to geotiff files that are known to be
correct (stored in the ``p2g-v2g-econus-tests-<version>/verify`` directory.
The comparison uses the UNIX ``diff`` utility so the files must be exact. This
may cause some machines to fail the comparison due to small differences with
floating point operations.

Test cases:

    - econus_20120928:
        :Start Time: September 28th, 2012 07:26 UTC
        :End Time: September 28th, 2012 07:39 UTC
        :Bands: DNB,I04
        :Fog Created: No
        :Forced Grid: :doc:`wgs84_fit <grids>`
        :Orbit Number: 00001




