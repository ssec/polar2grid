AVHRR Reader
============

.. automodule:: polar2grid.avhrr.avhrr2swath

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.avhrr.avhrr2swath
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh avhrr <writer>
    :passparser:

Execution Examples
-----------------------

.. code-block:: bash

    polar2grid.sh avhrr scmi --list-products -f /l1b/hrpt_noaa18_20170202_2242_60321.l1b 

    polar2grid.sh avhrr gtiff -f ../input/hrpt_M01_20170202_0227_22708.l1b

    polar2grid.sh avhrr gtiff -p band1_vis band4_bt -f /data/hrpt_noaa19_20170202_2042_41144.l1b 

    polar2grid.sh avhrr scmi -p band3a_vis -g lcc_conus_1km --sector-id LCC --letters --compress -f hrpt_M01_20170202_1457_22716.l1b

    polar2grid.sh avhrr scmi --grid-coverage=0 -g polar_alaska_1km --sector-id Polar --letters --compress -f /avhrr

    polar2grid.sh avhrr hdf5 --add-geolocation --grid-configs /home/avhrr/grids/local_grid.conf -g my_grid  -f ../input/hrpt_*.l1b

    polar2grid.sh avhrr binary -p band1_vis band4_bt -g lcc_eu -f /data/avhrr/metoba
    

