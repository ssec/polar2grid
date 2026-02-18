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

    polar2grid.sh -r acspo -w geotiff --list-products -f /noaa21/20260218164100-CSPP-L2P_GHRSST-SSTsubskin-VIIRS_N21-ACSPO_V2.80-v02.0-fv01.0.nc

    polar2grid.sh -r acspo -w geotiff --grid-coverage=0.0 -f /aqua/20260216095647-CSPP-L2P_GHRSST-SSTskin-MODIS_A-ACSPO_V2.80-v02.0-fv01.0.nc

    polar2grid.sh -r acspo -w hdf5 -p sst sea_ice_fraction --compress gzip --add-geolocation -g lcc_fit --grid-coverage=.02 -f /metopc/20260211014828-CSPP-L2P_GHRSST-SSTskin-AVHRRF_MC-ACSPO_V2.80-v02.0-fv01.0.nc

    polar2grid.sh -r acspo -w awips_tiled --num-workers 4 --grid-coverage 0 -g lcc_conus_750 --sector-id LCC --letters --compress -f 20260218173600-CSPP-L2P_GHRSST-SSTsubskin-VIIRS_N20*.nc

    polar2grid.sh -r acspo -w awips_tiled -g merc_pacific_300 --sector-id Pacific --letters --compress -f *CSPP-L2P_GHRSST-SSTskin-VIIRS_NPP-ACSPO*.nc
