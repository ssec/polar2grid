MODIS L2 Reader
================

.. automodule:: polar2grid.readers.modis_l2
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.modis_l2
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r modis_l2 -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh -r modis_l2 -w geotiff -f <path to files>/<list of files>

    polar2grid.sh -r modis_l2 -w geotiff -h

    polar2grid.sh -r modis_l2 -w geotiff --list-products -f /data
