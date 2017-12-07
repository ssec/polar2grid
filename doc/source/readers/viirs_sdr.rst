VIIRS SDR Reader
================

.. automodule:: polar2grid.viirs.swath

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.viirs.swath
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh viirs_sdr <writer>
    :passparser:

.. versionchanged:: 2.1
    The reader name has been changed to ``viirs_sdr`` although ``viirs`` is still
    supported for the time being.

Examples:

.. code-block:: bash

    polar2grid.sh viirs_sdr gtiff -f <path to files>/<list of files>

    viirs2awips.sh -g 211e 211w -f ../sdr/*.h5

    polar2grid.sh viirs_sdr gtiff -h

    polar2grid.sh viirs_sdr gtiff --list-products -f ../sdr/*.h5

    polar2grid.sh viirs_sdr scmi -p i04 adaptive_dnb dynamic_dnb --sza-threshold=90.0 --letters --compress --sector-id Polar -g polar_alaska_1km -f <path to files>

    polar2grid.sh viirs_sdr hdf5 --compress gzip --m-bands -f ../sdr/*.h5

    polar2grid.sh viirs_sdr binary -g lcc_fit -p m15 -f ../sdr/SVM15*.h5 ../sdr/GMTCO*.h5
