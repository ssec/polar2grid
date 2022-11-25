AGRI L1 Reader
==============

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

    geo2grid.sh -r agri_fy4a_l1 -w geotiff -p C01 C02 true_color -f FY4A-_AGRI--*.HDF

    geo2grid.sh -r agri_fy4a_l1 -w geotiff --ll-bbox 105.0 10.0 130.0 30.0 -f FY4A-_AGRI--*.HDF

    geo2grid.sh -r agri_fy4a_l1 -w geotiff -p airmass dust --num-workers 4 --grid-configs=/home/g2g/my_grid.conf -g south_china_sea --method nearest -f /data/fy4a/agri/
