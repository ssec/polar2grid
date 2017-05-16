VIIRS L1B Reader
================

.. automodule:: polar2grid.readers.viirs_l1b

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.viirs_l1b
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh viirs_l1b <writer>
    :passparser:

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh viirs_l1b gtiff -h 

    polar2grid.sh viirs_l1b gtiff --list-products -f ../l1b/*.nc

    polar2grid.sh viirs_l1b gtiff -p m01 -f /data/VL1BM_snpp_d20170117_t191800_c20170118003207.nc /data/VGEOM_snpp_d20170117_t191800_c20170118003158.nc

    polar2grid.sh viirs_l1b awips -g 211e 211w -p adaptive_dnb dynamic_dnb --night-fraction=.04 -f /data

    polar2grid.sh viirs_l1b gtiff -p true_color false_color -f /viirs_l1b/*.nc
