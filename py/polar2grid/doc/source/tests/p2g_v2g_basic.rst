viirs2gtiff Basic
=================

This test is delivered as a tarball (``p2g-v2g-basic-tests-<version>.tar.gz``) and can be
"installed" by untarring it::

    tar -xzf p2g-v2g-basic-tests-<version>.tar.gz

then it can be run using the ``run.sh`` script that is inside the untarred
directory::

    p2g-v2g-basic-tests-<version>/run.sh [destination directory]

.. warning::

    Do NOT run ``run.sh`` from the ``p2g-v2g-basic-tests-<version>`` directory.

where ``destination directory`` is an optional directory name where the test
products should be placed. By default the products are placed in
``./p2g-v2g-basic-tests-PID``. Where ``PID`` is a unique identifier created by
the run script. This command will create Geotiff files.  If it completes
successfully it should print out ``SUCCESS`` as the last line of output.

You can visually compare the geotiff images or you can run the verify script::

    p2g-v2g-basic-tests-<version>/verify.sh <destination directory>

where ``destination directory`` is the same as for ``run.sh``. This will
compare the geotiff files created to geotiff files that are known to be
correct (stored in the ``p2g-v2g-basic-tests-<version>/verify`` directory.
Each pixel is compared and a message is printed stating a ``SUCCESS`` or
a ``FAIL`` and how many pixels differed. Small differences with floating
point operations on some machines may cause a few pixels to differ, but
this is unlikely.

Test cases:

    - ak_20120408:
        :Start Time: April 8th, 2012 13:11 UTC
        :End Time: April 8th, 2012 13:21 UTC
        :Bands: DNB,I04
        :Fog Created: No
        :Forced Grid: :ref:`wgs84_fit`
        :Orbit Number: 02315

    - econus_20120928:
        :Start Time: September 28th, 2012 07:26 UTC
        :End Time: September 28th, 2012 07:39 UTC
        :Bands: DNB,I04
        :Fog Created: No
        :Forced Grid: :ref:`wgs84_fit`
        :Orbit Number: 00001

