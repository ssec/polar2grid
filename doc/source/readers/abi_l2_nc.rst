ABI L2 NetCDF Reader
====================

.. automodule:: polar2grid.readers.abi_l2_nc
    :noindex:

Command Line Usage
------------------

.. argparse::
    :module: polar2grid.readers.abi_l2_nc
    :func: add_reader_argument_groups
    :prog: geo2grid.sh -r abi_l2_nc -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    geo2grid.sh -r abi_l2_nc -h

    geo2grid.sh -r abi_l2_nc -w geotiff --list-products -f abi/full_disk/CG_ABI-L2-ACHAF-M6_G17_*.nc

    geo2grid.sh -r abi_l2_nc -w geotiff -p TEMP -f CG_ABI-L2-ACHTF-M6_G17_s20223271830316_e20223271839394_c20223271842100.nc

     geo2grid.sh -r abi_l2_nc -w geotiff  -p MVFR_Fog_Prob LIFR_Fog_Prob IFR_Fog_Prob -f ABI-L2-GFLSF-M6_v3r1_g16_s202404231820204_e202404231829524_c202404231836180.nc

    geo2grid.sh -r abi_l2_nc -w geotiff -f /data/conus/CG_ABI-L2-*-M6_G18_s20241141826172*.nc

    geo2grid.sh -r abi_l2_nc -w geotiff -p AOD LST -f /abi/meso1/CG_ABI-L2-AODM1-M6_G18_s2024114182*.nc CG_ABI-L2-LSTM1-M6_G18_s2024114182*.nc
