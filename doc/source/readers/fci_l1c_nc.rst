FCI L1c NetCDF Reader
=====================

.. automodule:: polar2grid.readers.fci_l1c_nc
    :noindex:

Command Line Usage
------------------

.. argparse::
    :module: polar2grid.readers.fci_l1c_nc
    :func: add_reader_argument_groups
    :prog: geo2grid.sh -r fci_l1c_nc -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    geo2grid.sh -r fci_l1c_nc -h

    geo2grid.sh -r fci_l1c_nc -w geotiff --list-products -f /data/mtg/fci

    geo2grid.sh -r fci_l1c_nc -w geotiff --num-workers 8 -f /data/mtg/fci

    geo2grid.sh -r fci_l1c_nc -w geotiff -p vis_04 vis_05 vis_06 vis_08 nir_13 nir_16 true_color -f *_N_JLS_C_0072*.nc

    geo2grid.sh -r fci_l1c_nc -w geotiff --ll-bbox 10 -15 40 10 -f /fci_data
