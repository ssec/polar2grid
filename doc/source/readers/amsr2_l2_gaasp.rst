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

    polar2grid.sh -r amsr2_l2_gaasp -w geotiff -f <path to files>/<list of files>

    polar2grid.sh -r amsr2_l2_gaasp -w geotiff -h

    polar2grid.sh -r amsr2_l2_gaasp -w geotiff --list-products -f gaasp/*.nc

    polar2grid.sh -r amsr2_l2_gaasp -w geotiff -p SST WSPD CLW TPW --num-workers 8 -f gaasp/AMSR2-OCEAN*.nc

    polar2grid.sh -r amsr2_l2_gaasp -w geotiff -g polar_alaska -p SWE Snow_Depth Soil_Moisture --fill-value 0 -f  AMSR2-SNOW_v2r2_GW1_s202601292227100_e202601292237440_c202601292245210.nc AMSR2-SOIL_v2r2_GW1_s202601292227100_e202601292237440_c202601292245210.nc

    polar2grid.sh -r amsr2_l2_gaasp -w hdf5 --add-geolocation --dtype float32 -p Rain_Rate -f AMSR2-PRECIP_v2r2_GW1_s202602020736030_e202602020746510_c202602020759490.nc
