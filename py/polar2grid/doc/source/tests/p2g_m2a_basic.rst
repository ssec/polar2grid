modis2awips Basic
=================

Delivered as a tarball (``p2g-m2a-basic-tests-<version>.tar.gz``) and can be "installed" by
first untarring it::

    tar -xzf p2g-m2a-basic-tests-<version>.tar.gz

then it can be run using the ``run.sh`` script that is inside the untarred
directory::

    p2g-m2a-basic-tests-<version>/run.sh [destination directory]

.. warning::

    Do NOT run ``run.sh`` from the ``p2g-m2a-basic-tests-<version>`` directory.

where ``destination directory`` is an optional directory name where the test
products should be placed.  By default the products are placed in
``./p2g-m2a-basic-tests-PID``.  Where ``PID`` is a unique identifier created by
the run script.  This command will create NetCDF files and
png images.  If it completes successfully is should print out
``SUCCESS`` as the last line of output.

You can visually compare the png images or you can run the verify
script::

    p2g-m2a-basic-tests-<version>/verify.sh <destination directory>

where ``destination directory`` is the same as for ``run.sh``.  This will
compare the NetCDF files created to NetCDF files that are known to be
correct (stored in the ``p2g-m2a-basic-tests-<version>/verify`` directory.  The comparison
allows for a difference of ``1`` in the AWIPS NetCDF files due to the unlikely
possibility that different machines produce slightly different floating point
results.

Test cases:

    - modis_aqua_12226_1846:
        :Start Time: August 13th, 2012 18:46 UTC
        :End Time: August 13th, 2012 18:46 UTC
        :Inputs: 1000m
        :Forced Grid: 211e

