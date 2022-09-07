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

    geo2grid.sh -r abi_l2_nc -w geotiff --list-products -f /data/goes16/abi

    geo2grid.sh -r abi_l2_nc -w geotiff -p HT -f OR_ABI-L2-ACHAC*.nc
