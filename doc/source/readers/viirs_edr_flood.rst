VIIRS EDR Flood Reader
======================

.. automodule:: polar2grid.readers.viirs_edr_flood

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.viirs_edr_flood
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh viirs_edr_flood <writer>
    :passparser:

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh viirs_edr_flood gtiff -h
