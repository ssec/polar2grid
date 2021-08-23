ACSPO SST Reader
================

.. automodule:: polar2grid.readers.acspo
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.acspo
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r acspo -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh -r aspo -w geotiff -h

    polar2grid.sh -r acspo -w geotiff --list-products -f /snpp/20170401174600-STAR-L2P_GHRSST-SSTskin-VIIRS_NPP-ACSPO_V2.40-v02.0-fv01.0.nc

    polar2grid.sh -r acspo -w geotiff --grid-coverage=0.0 -f ../aqua/20170401191500-STAR-L2P_GHRSST-SSTskin-MODIS_A*.nc

    polar2grid.sh -r acspo -w hdf5 -p sst sea_ice_fraction --compress gzip --add-geolocation -g lcc_fit --grid-coverage=.02 -f /noaa18/20170401194729-STAR-L2P_GHRSST-SSTskin-AVHRR19_D-ACSPO_V2.40-v02.0-fv01.0.nc

    polar2grid.sh -r acspo -w awips_tiled --letters --compress -g lcc_conus_750 --sector-id LCC  --grid-coverage=0.0 -f 20171112192000-STAR-L2P_GHRSST-SSTskin-VIIRS_NPP-ACSPO_V2.40-v02.0-fv01.0.nc

    polar2grid.sh -r acspo -w awips_tiled -g merc_pacific_300 --sector-id Pacific --letters --compress -f *STAR-L2P_GHRSST-SSTskin-VIIRS_NPP-ACSPO*.nc
