AWS MWR Reader
==============

.. automodule:: polar2grid.readers.aws1_mwr_l1b_nc
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.aws1_mwr_l1b_nc
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r aws1_mwr_l1b_nc -w <writer>
    :passparser:

Execution Examples
------------------

.. code-block:: bash

    polar2grid.sh -r aws1_mwr_l1b_nc -w awips_tiled --list-products -f /l1b/

    polar2grid.sh -r aws1_mwr_l1b_nc -w geotiff -f ../input/

    polar2grid.sh -r aws1_mwr_l1b_nc -w geotiff -p btemp03 btemp04  -f /data/*.nc

    polar2grid.sh -r aws1_mwr_l1b_nc -w awips_tiled -p btemp03 -g lcc_conus_1km --sector-id LCC --letters --compress -f hrpt_noaa18_20220918_1708_89324.l1b

    polar2grid.sh -r aws1_mwr_l1b_nc -w awips_tiled --num-workers 6 --grid-coverage .002 -g polar_alaska_1km --sector-id Polar --letters --compress -f /aws1_mwr

    polar2grid.sh -r aws1_mwr_l1b_nc -w hdf5 --add-geolocation --grid-configs /home/mwr/grids/local_grid.yaml -g my_grid  -f ../input/

    polar2grid.sh -r aws1_mwr_l1b_nc -w binary --num-workers 8 -p btemp01 btemp04 -g lcc_eu -f /data/
