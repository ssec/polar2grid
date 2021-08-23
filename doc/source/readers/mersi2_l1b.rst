MERSI-2 L1B Reader
==================

.. automodule:: polar2grid.readers.mersi2_l1b
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.mersi2_l1b
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh mersi2_l1b <writer>
    :passparser:

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh mersi2_l1b gtiff -h

    polar2grid.sh mersi2_l1b gtiff --list-products -f tf2019259173245.FY3D-X_MERSI*.HDF
 
    polar2grid.sh mersi2_l1b gtiff -p 1 2 3 4 6 7 20 25 -f tf2019233172521.FY3D-X_MERSI_0250M_L1B.HDF tf2019233172521.FY3D-X_MERSI_1000M_L1B.HDF tf2019233172521.FY3D-X_MERSI_GEOQK_L1B.HDF tf2019233172521.FY3D-X_MERSI_GEO1K_L1B.HDF

    polar2grid.sh mersi2_l1b gtiff -p true_color false_color -g lcc_fit -f ../mersi/tf2019259173245.FY3D-X_MERSI*.HDF

    polar2grid.sh mersi2_l1b hdf5 -p 20 21 22 23 24 25  --grid-configs ${HOME}/my_grid.conf -g shanghai seoul -f ../data/*.HDF

    polar2grid.sh mersi2_l1b binary --sza-threshold=90  -p 1 2 3 4 6 7 20 25 -f tf2019226095418.FY3D-X_MERSI_*.HDF 
