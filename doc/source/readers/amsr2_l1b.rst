AMSR2 L1B Reader
================

.. automodule:: polar2grid.readers.amsr2_l1b

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.amsr2_l1b
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh amsr2_l1b <writer>
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh amsr2_l1b gtiff -h

    polar2grid.sh amsr2_l1b gtiff  -f <path to files>/<AMSR2 Level 1B filename>

    polar2grid.sh amsr2_l1b gtiff -g lcc_fit -f ../data/GW1AM2_201607201808_128A_L1DLBTBR_1110110.h5

    polar2grid.sh amsr2_l1b gtiff --rescale-configs $POLAR2GRID_HOME/rescale_configs/amsr2_png.ini -g lcc_fit -f ../data/GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5

    polar2grid.sh amsr2_l1b scmi --list-products -f /amsr2/GW1AM2_201607201808_128A_L1DLBTBR_1110110.h5

   polar2grid.sh amsr2_l1b scmi -g lcc_conus_1km -p btemp_36.5h btemp_89.0av --sector-id LCC --letters --compress -f GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5

