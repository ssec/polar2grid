AMSR2 L1B Reader
================

.. automodule:: polar2grid.readers.amsr2_l1b
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.amsr2_l1b
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r amsr2_l1b -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh -r amsr2_l1b -w geotiff --list-products-all -f ../data/*L1DLBTBR*.h5

    polar2grid.sh -r amsr2_l1b -w geotiff  -f <path to files>/<AMSR2 Level 1B filename>

    polar2grid.sh -r amsr2_l1b -w geotiff -g lcc_fit --fill-value 0 -f ../data/GW1AM2_202209121053_051D_L1DLBTBR_1110110.h5

    polar2grid.sh -r amsr2_l1b -w geotiff --extra-config-path $POLAR2GRID_HOME/example_enhancements/amsr2_png --fill-value 0 -f ../gcom_data/

    polar2grid.sh -r amsr2_l1b -w awips_tiled --list-products -f /amsr2/GW1AM2_202209120729_019D_L1DLBTBR_2220220.h5

    polar2grid.sh -r amsr2_l1b -w awips_tiled -g lcc_conus_1km -p btemp_36.5h btemp_89.0av --sector-id LCC --letters --compress -f GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5
