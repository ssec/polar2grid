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

    polar2grid.sh -r aws1_mwr_l1b_nc -w geotiff -h

    polar2grid.sh -r aws1_mwr_l1b_nc -w geotiff --list-products -f W_XX-OHB-Stockholm,SAT,AWS1-MWR-1B-RAD_C_OHB__20250724183721_G_D_20250626042546_20250626043506_T_B____.nc

    polar2grid.sh -r aws1_mwr_l1b_nc -w geotiff -f ../aws_input/

    polar2grid.sh -r aws1_mwr_l1b_nc -w awips_tiled -p bt06 bt16 bt19 -g lcc_conus_1km --sector-id LCC --letters --source-name SSEC --compress --num-workers 16 -f /data/*AWS1-MWR-1B-RAD_C_OHB*.nc

    polar2grid.sh -r aws1_mwr_l1b_nc -w hdf5 -p bt15 --add-geolocation --grid-configs /home/mwr/local_grid.yaml -g my_aws_grid  -f ../input/*.nc
