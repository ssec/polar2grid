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

    geo2grid.sh -r abi_l2_nc -w geotiff --list-products -f abi/full_disk/CG_ABI-L2-*-M6_G19*.nc

    geo2grid.sh -r abi_l2_nc -w geotiff -p TEMP -f CG_ABI-L2-ACHTF-M6_G19_s20261181500205_e20261181509525_c20261181512030.nc

    geo2grid.sh -r abi_l2_nc -w geotiff  -p MVFR_Fog_Prob LIFR_Fog_Prob IFR_Fog_Prob -f ABI-L2-GFLSM-M6_v3r1_g19_s202604281500278_e202604281500347_c202604281501310.nc

    geo2grid.sh -r abi_l2_nc -w geotiff -f /data/conus/CG_ABI-L2-*C-M6_G19_s20261181501170_*.nc

    geo2grid.sh -r abi_l2_nc -w geotiff -p AOD LST -f /abi/meso1/CG_ABI-L2-AODM1-M6_G18_s2024114182*.nc CG_ABI-L2-LSTM1-M6_G18_s2024114182*.nc

    geo2grid.sh -r abi_l2_nc -w geotiff -p PRES Phase -f CG_ABI-L2-ACTPC-M6_G19_s20261181501*.nc CG_ABI-L2-CTPC-M6_G19_s20261181501*.nc
