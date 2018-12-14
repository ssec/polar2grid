ABI L1B Reader
==============

.. automodule:: polar2grid.readers.abi_l1b

Command Line Usage
------------------

.. argparse::
    :module: polar2grid.readers.abi_l1b
    :func: add_reader_argument_groups
    :prog: geo2grid.sh -r abi_l1b -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    geo2grid.sh -r abi_l1b -h 

    geo2grid.sh -r abi_l1b -w geotiff --list-products -f /goes16/abi

    geo2grid.sh -r abi_l1b -w geotiff --num-workers 8 -f /data/goes16/abi

    geo2grid.sh -r abi_l1b -w geotiff -p C02 C03 C04 C05 C06 true_color -f OR_ABI-L1b-RadC*.nc

    geo2grid.sh -r abi_l1b -w geotiff --ll-bbox -95.0 40.0 -85.0 50.0 -f OR_ABI-L1b-RadC*.nc

    geo2grid.sh -r abi_l1b -w geotiff -p airmass dust --num-workers 4 --grid-configs=/home/g2g/my_grid.conf -g madison --method nearest -f /data/goes17/abi/
