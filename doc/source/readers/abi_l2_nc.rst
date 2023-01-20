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

    geo2grid.sh -r abi_l2_nc -w geotiff -f /data/conus/CG_ABI-L2-ACH?C-M6_G16*.nc

    geo2grid.sh -r abi_l2_nc -w geotiff -f /abi/meso1/CG_ABI-L2-ACHAM1-M6_G17_s20223271830588_e20223271831056_c20223271831440.nc
