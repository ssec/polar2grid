AMI L1B Reader
==============

.. automodule:: polar2grid.readers.ami_l1b
    :noindex:

Command Line Usage
------------------

.. argparse::
    :module: polar2grid.readers.ami_l1b
    :func: add_reader_argument_groups
    :prog: geo2grid.sh -r ami_l1b -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    geo2grid.sh -r ami_l1b -h

    geo2grid.sh -r ami_l1b -w geotiff --list-products -f /data/gk2a/ami

    geo2grid.sh -r ami_l1b -w geotiff --num-workers 8 -f /data/gk2a/ami

    geo2grid.sh -r ami_l1b -w geotiff -p VI005 VI006 VI008 NR013 NR016 true_color -f gk2a_ami*.nc

    geo2grid.sh -r ami_l1b -w geotiff --ll-bbox 125 -15 160 10 -f /ami_data
