AGRI FY-4A L1 Reader
====================

.. automodule:: polar2grid.readers.agri_fy4a_l1
    :noindex:

Command Line Usage
------------------

.. argparse::
    :module: polar2grid.readers.agri_fy4a_l1
    :func: add_reader_argument_groups
    :prog: geo2grid.sh -r agri_fy4a_l1 -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    geo2grid.sh -r agri_fy4a_l1 -h

    geo2grid.sh -r agri_fy4a_l1 -w geotiff --list-products -f /data/fy4a/agri

    geo2grid.sh -r agri_fy4a_l1 -w geotiff --num-workers 8 -f /data/fy4a/agri

    geo2grid.sh -r agri_l1 -w geotiff -p C02 C03 C08 C10 C12 -f FY4A-_AGRI--*.HDF

    geo2grid.sh -r agri_l1 -w geotiff --ll-bbox 100 20 120 40 -p true_color -f /data/*.HDF
