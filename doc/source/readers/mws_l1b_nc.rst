MWS Reader
==========

.. automodule:: polar2grid.readers.mws_l1b_nc
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.mws_l1b_nc
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r mws_l1b_nc -w <writer>
    :passparser:

Execution Examples
------------------

.. code-block:: bash

    polar2grid.sh -r mws_l1b_nc -w geotiff -h

    polar2grid.sh -r mws_l1b_nc -w geotiff --list-products -f W_XX-EUMETSAT-Darmstadt,SAT,SGA1-MWS-1B-RAD_C_EUMT_20260819163555_G_V_20260819162503_20260819163453_C_N_T__.nc

    polar2grid.sh -r mws_l1b_nc -w geotiff -f ../mws_input/

    polar2grid.sh -r mws_l1b_nc -w geotiff -p 1 2 24 -g lcc_conus_1km -f /data/*SGA1-MWS-1B-RAD_C_EUMT*.nc

    polar2grid.sh -r mws_l1b_nc -w awips_tiled -p 17 19 -g lcc_conus_1km --sector-id LCC --letters --source-name SSEC --compress --num-workers 16 -f /data/*SGA1-MWS-1B-RAD_C_EUMT*.nc

    polar2grid.sh -r mws_l1b_nc -w hdf5 -p 11 --add-geolocation --grid-configs /home/mws/local_grid.yaml -g my_mws_grid -f ../input/*.nc
