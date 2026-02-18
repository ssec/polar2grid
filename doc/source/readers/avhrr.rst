AVHRR Reader
============

.. automodule:: polar2grid.readers.avhrr_l1b_aapp
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.avhrr_l1b_aapp
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r avhrr_l1b_aapp -w <writer>
    :passparser:

Execution Examples
------------------

.. code-block:: bash

    polar2grid.sh -r avhrr_l1b_aapp -w awips_tiled --list-products -f /l1b/

    polar2grid.sh -r avhrr_l1b_aapp -w geotiff -h

    polar2grid.sh -r avhrr_l1b_aapp -w geotiff --list-products -f hrpt_M03*.l1b

    polar2grid.sh -r avhrr_l1b_aapp -w geotiff -f hrpt_M03_20251226_1522_37032.l1b

    polar2grid.sh -r avhrr -w geotiff -p band3a_vis band4_bt -f hrpt_M03_20251226_1522_37032.l1b

    polar2grid.sh -r avhrr -w awips_tiled -p band3b_bt -g lcc_conus_1km --sector-id LCC --letters --compress -f hrpt_M01_20251226_0225_68867.l1b

    polar2grid.sh -r avhrr_l1b_aapp -w awips_tiled --num-workers 6 --grid-coverage .002 -g polar_alaska_1km --sector-id Polar --letters --compress -f /avhrr

    polar2grid.sh -r avhrr -w hdf5 --add-geolocation --grid-configs /home/avhrr/grids/local_grid.yaml -g my_grid  -f ../input/hrpt_M01*.l1b

    polar2grid.sh -r avhrr -w binary --num-workers 8 -p band1_vis band4_bt -g lcc_eu -f /data/avhrr/metobc
