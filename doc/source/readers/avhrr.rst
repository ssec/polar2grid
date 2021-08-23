AVHRR Reader
============

.. automodule:: polar2grid.readers.avhrr_l1b_aapp
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.avhrr_l1b_aapp
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r avhrr -w <writer>
    :passparser:

Execution Examples
-----------------------

.. code-block:: bash

    polar2grid.sh -r avhrr -w awips_tiled --list-products -f /l1b/hrpt_noaa18_20170202_2242_60321.l1b

    polar2grid.sh avhrr gtiff -f ../input/hrpt_M01_20170202_0227_22708.l1b

    polar2grid.sh avhrr gtiff -p band1_vis band4_bt -f /data/hrpt_noaa19_20170202_2042_41144.l1b 

    polar2grid.sh avhrr awips_tiled -p band3a_vis -g lcc_conus_1km --sector-id LCC --letters --compress -f hrpt_M01_20170202_1457_22716.l1b

    polar2grid.sh avhrr awips_tiled --grid-coverage=0 -g polar_alaska_1km --sector-id Polar --letters --compress -f /avhrr

    polar2grid.sh avhrr hdf5 --add-geolocation --grid-configs /home/avhrr/grids/local_grid.conf -g my_grid  -f ../input/hrpt_*.l1b

    polar2grid.sh avhrr binary -p band1_vis band4_bt -g lcc_eu -f /data/avhrr/metoba
    

