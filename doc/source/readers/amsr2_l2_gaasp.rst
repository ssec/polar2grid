AMSR2 GAASP Level 2 Reader
==========================

.. automodule:: polar2grid.readers.amsr2_l2_gaasp
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.amsr2_l2_gaasp
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r amsr2_l2_gaasp -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh -r viirs_edr -w geotiff -f <path to files>/<list of files>

    polar2grid.sh -r viirs_edr -w geotiff -h

    polar2grid.sh -r viirs_edr -w geotiff --list-products -f ../edr/*.nc

    polar2grid.sh -r viirs_edr -w geotiff -p true_color_surf false_color_surf --num-workers 8 -f ../edr/edr/SurfRefl*.nc

    polar2grid.sh -r viirs_edr -w hdf5 --add-geolocation --dtype float32 -p NDVI EVI --maximum-weight-mode -f SurfRefl*.nc

    polar2grid.sh -r viirs_edr -w awips_tiled -p AOD550 CldTopHght CldTopTemp  -g lcc_conus_300 --sector-id LCC --letters --compress -f /viirs/JRR-AOD_v3r0_j01_s202406051854471_e202406051856116_c202406052204237.nc /viirs/JRR-CloudHeight_v3r0_j01_s202406051854471_e202406051856116_c202406052204237.nc
