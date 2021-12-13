AHI HimawariCast (HRIT) Reader
==============================

.. automodule:: polar2grid.readers.ahi_hrit
    :noindex:

Command Line Usage
------------------

.. argparse::
    :module: polar2grid.readers.ahi_hrit
    :func: add_reader_argument_groups
    :prog: geo2grid.sh -r ahi_hrit -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    geo2grid.sh -r ahi_hrit -h

    geo2grid.sh -r ahi_hrit -w geotiff --list-products -f /ahi8/hcast/2330

    geo2grid.sh -r ahi_hrit -w geotiff -f /ahi8/hcast/IMG_DK01IR4_201811122330

    geo2grid.sh -r ahi_hrit -w geotiff -p B03 B04 B05 B06 B16 natural_color --num-workers 8 -f /hrit/ahi/

    geo2grid.sh -r ahi_hrit -w geotiff --ll-bbox 125 -15 160 10 -f /data/hsd/IMG_DK01*
