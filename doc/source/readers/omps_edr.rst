OMPS EDR Reader
===============

.. automodule:: polar2grid.readers.omps_edr
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.omps_edr
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r omps_edr -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh -r omps_edr -w geotiff -h

    polar2grid.sh -r omps_edr -w geotiff --list-products -f V8TOZ-EDR_v4r3_j01_s202604071740387_e202604071741162_c202604071754380.nc

    polar2grid.sh -r omps_edr -w geotiff -f /omps/edr/

    polar2grid.sh -r omps_edr -w geotiff -p ColumnAmountO3 --filter-by-error-flag -f ../omps/V8TOZ-EDR_v4r3_j01_*.nc

    polar2grid.sh -r omps_edr -w geotiff -p s_ColumnamountSO2_PBL --no-filter-negative-so2 -f ../omps/V8TOS-EDR_v4r5_j02_*.nc

    polar2grid.sh -r omps_edr -w geotiff -p AerosolIndex Reflectivity331 -g lcc_fit -f ../omps/*.nc

    polar2grid.sh -r omps_edr -w hdf5 -p s_ColumnamountSO2_PBL --grid-configs ${HOME}/my_grid.yaml -g my_omps_grid -f /data/*.nc
