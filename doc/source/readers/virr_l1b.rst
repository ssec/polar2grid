VIRR L1B Reader
===============

.. automodule:: polar2grid.readers.virr_l1b

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.virr_l1b
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh virr_l1b <writer>
    :passparser:

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh virr_l1b gtiff -h
