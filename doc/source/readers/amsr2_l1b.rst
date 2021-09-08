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

    polar2grid.sh -r amsr2_l1b -w geotiff -h

    polar2grid.sh -r amsr2_l1b -w geotiff  -f <path to files>/<AMSR2 Level 1B filename>

    polar2grid.sh -r amsr2_l1b -w geotiff -g lcc_fit -f ../data/GW1AM2_201607201808_128A_L1DLBTBR_1110110.h5

    polar2grid.sh -r amsr2_l1b -w geotiff --rescale-configs $POLAR2GRID_HOME/rescale_configs/amsr2_png.ini -g lcc_fit -f ../data/GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5

    polar2grid.sh -r amsr2_l1b -w awips_tiled --list-products -f /amsr2/GW1AM2_201607201808_128A_L1DLBTBR_1110110.h5

   polar2grid.sh -r amsr2_l1b -w awips_tiled -g lcc_conus_1km -p btemp_36.5h btemp_89.0av --sector-id LCC --letters --compress -f GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5

