AHI Himawari Standard Data (HSD) Reader
=======================================

.. automodule:: polar2grid.readers.ahi_hsd
    :noindex:

Command Line Usage
------------------

.. argparse::
    :module: polar2grid.readers.ahi_hsd
    :func: add_reader_argument_groups
    :prog: geo2grid.sh -r ahi_hsd -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    geo2grid.sh -r ahi_hsd -h

    geo2grid.sh -r ahi_hsd -w geotiff --list-products -f /ahi8/data/

    geo2grid.sh -r ahi_hsd -w geotiff -f HS_H08_20181112_2330_B01_R301_R10_S0101.DAT

    geo2grid.sh -r ahi_hsd -w geotiff -p B02 B03 B04 B05 B06 true_color --num-workers 8 -f /data/hsd/2330/*FLDK*.DAT

    geo2grid.sh -r ahi_hsd -w geotiff -p B09 B10 B11 B12 B13 natural_color -f /ahi8/HS_H08_20181112_2330_*R303*.DAT

    geo2grid.sh -r ahi_hsd -w geotiff --ll-bbox 125 -15 160 10 -f /data/hsd/*FLDK*.DAT

    geo2grid.sh -r ahi_hsd -w geotiff -p true_color natural_color --num-workers 4 \
        --grid-configs=/geo/my_grid.conf -g perth --method nearest -f /data/hsd/*FLDK*.DAT
