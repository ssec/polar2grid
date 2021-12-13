VIRR L1B Reader
===============

.. automodule:: polar2grid.readers.virr_l1b
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.virr_l1b
    :func: add_reader_argument_groups
    :prog: polar2grid.sh virr_l1b <writer>
    :passparser:

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh virr_l1b gtiff -h

    polar2grid.sh virr_l1b hdf5 --list-products -f tf2019230221957.FY3B-L_VIRRX_L1B.HDF

    polar2grid.sh virr_l1b gtiff -f ../l1b/*.HDF

    polar2grid.sh virr_l1b gtiff -p 1 10 2 3 4 -f /viir/data/*FY3B-L_VIRRX_L1B.HDF

    polar2grid.sh virr_l1b scmi -g lcc_conus_750 --sector-id LCC --compress --letters -p -p 1 2 3 4 5 -f /viir/data/tf*.HDF

    polar2grid.sh virr_l1b binary -p 1 5 10 9 -g lcc_fit -f ../l1b/tf2019230221957.FY3B-L_VIRRX_L1B.HDF

    polar2grid.sh virr_l1b gtiff --sza-threshold 50 -f tf2019286095509.FY3B-L_VIRRX_L1B.HDF
