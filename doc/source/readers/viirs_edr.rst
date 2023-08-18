VIIRS EDR Reader
================

.. automodule:: polar2grid.readers.viirs_edr
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.viirs_edr
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r viirs_edr -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh -r viirs_edr -w geotiff -f <path to files>/<list of files>

    polar2grid.sh -r viirs_edr -w geotiff -h

    polar2grid.sh -r viirs_edr -w geotiff --list-products -f ../edr/*.h5

    polar2grid.sh -r viirs_edr -w geotiff -p true_color_surf false_color_surf --num-workers 8 --no-tiled -f ../edr/*.h5


Product Explanation
-------------------

TODO
