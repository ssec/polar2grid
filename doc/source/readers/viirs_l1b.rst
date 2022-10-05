VIIRS L1B Reader
================

.. automodule:: polar2grid.readers.viirs_l1b
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.viirs_l1b
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r viirs_l1b -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh -r viirs_l1b -w geotiff -h

    polar2grid.sh -r viirs_l1b -w geotiff --list-products -f ../data/*.nc

    polar2grid.sh -r viirs_l1b -w geotiff -p m01 -f /l1b/VJ102MOD.A2022257.1748.001.2022258055009.nc l1b/VJ103MOD.A2022257.1748.001.2022258054957.nc

    polar2grid.sh -r viirs_l1b -w hdf5 -g lcc_fit --add-geolocation -p i01 i02 -f VNP02IMG.A2022257.1842*.nc VNP03MOD.A2022257.1842*.nc

    polar2grid.sh -r viirs_l1b -w geotiff -p true_color false_color -f VNP02*.A2022257.1842*.nc VNP03*.A2022257.1842*.nc
