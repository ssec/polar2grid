viirs2awips Alaska Basic
========================

Delivered as a tarball (``p2g-v2a-ak-test-<version>.tar.gz``) and can be "installed" by
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

