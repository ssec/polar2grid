METimage Reader
===============

.. automodule:: polar2grid.readers.metimage_l1b_nc
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.metimage_l1b_nc
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r metimage_l1b_nc -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh -r metimage_l1b_nc -w geotiff -h

    polar2grid.sh -r metimage_l1b_nc -w geotiff --list-products -f /metimage/

    polar2grid.sh -r metimage_l1b_nc -w geotiff -f /metimage/W_XX-EUMETSAT-Darmstadt,SAT,SGA1-VII-1B-RAD*.nc

    polar2grid.sh -r metimage_l1b_nc -w geotiff -p vii_668 vii_10690 true_color -f /metimage/

    polar2grid.sh -r metimage_l1b_nc -w geotiff --orthorectify -g lcc_fit -f /metimage/

    polar2grid.sh -r metimage_l1b_nc -w awips_tiled -p true_color --num-workers 6 --grid-coverage .002 -g polar_alaska_1km --sector-id Polar --letters --compress -f /metimage/

    polar2grid.sh -r metimage_l1b_nc -w hdf5 --add-geolocation -p vii_10690 vii_12020 -f /metimage/
