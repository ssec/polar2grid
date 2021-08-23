VIIRS SDR Reader
================

.. automodule:: polar2grid.readers.viirs_sdr
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.viirs_sdr
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r viirs_sdr -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh -r viirs_sdr -w geotiff -f <path to files>/<list of files>

    polar2grid.sh -r viirs_sdr -w geotiff -h

    polar2grid.sh -r viirs_sdr -w geotiff --list-products -f ../sdr/*.h5

    polar2grid.sh -r viirs_sdr -w awips_tiled -p i04 adaptive_dnb dynamic_dnb --sza-threshold=90.0 --letters --compress --sector-id Polar -g polar_alaska_1km -f <path to files>

    polar2grid.sh -r viirs_sdr -w hdf5 --compress gzip --m-bands -f ../sdr/*.h5

    polar2grid.sh -r viirs_sdr -w binary -g lcc_fit -p m15 -f ../sdr/SVM15*.h5 ../sdr/GMTCO*.h5
