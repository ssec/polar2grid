MERSI-LL L1B Reader
===================

.. automodule:: polar2grid.readers.mersi_ll_l1b
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.mersi_ll_l1b
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r mersi_ll_l1b -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh -r mersi_ll_l1b -w geotiff -h

    polar2grid.sh -r mersi_ll_l1b -w geotiff --list-products -f tf2019259173245.FY3E-X_MERSI*.HDF

    polar2grid.sh -r mersi_ll_l1b -w geotiff -p 1 2 3 4 6 7 -f tf2019233172521.FY3E-X_MERSI_0250M_L1B.HDF tf2019233172521.FY3E-X_MERSI_1000M_L1B.HDF tf2019233172521.FY3E-X_MERSI_GEOQK_L1B.HDF tf2019233172521.FY3E-X_MERSI_GEO1K_L1B.HDF

    polar2grid.sh -r mersi_ll_l1b -w geotiff -p 1 2 -g lcc_fit -f ../mersi/tf2019259173245.FY3E-X_MERSI*.HDF

    polar2grid.sh -r mersi_ll_l1b -w hdf5 -p 3 4 5 --grid-configs ${HOME}/my_grid.yaml -g shanghai seoul -f ../data/*.HDF

    polar2grid.sh -r mersi_ll_l1b -w binary --sza-threshold=90  -p 1 -f tf2019226095418.FY3E-X_MERSI_*.HDF
