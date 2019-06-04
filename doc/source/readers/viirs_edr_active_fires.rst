VIIRS EDR Active Fires Reader
=============================

.. automodule:: polar2grid.readers.viirs_edr_active_fires

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.viirs_edr_active_fires
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh viirs_edr_active_fires <writer>
    :passparser:

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh viirs_edr_active_fires gtiff -h
