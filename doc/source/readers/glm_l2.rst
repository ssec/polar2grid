GLM L2 Reader
=============

.. automodule:: polar2grid.readers.glm_l2
    :noindex:

Command Line Usage
------------------

.. argparse::
    :module: polar2grid.readers.glm_l2
    :func: add_reader_argument_groups
    :prog: geo2grid.sh -r glm_l2 -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    geo2grid.sh -r glm_l2 -h

    geo2grid.sh -r glm_l2 -w geotiff --list-products -f /data/goes16/glm

    geo2grid.sh -r glm_l2 -w geotiff --num-workers 8 -f /data/goes16/glm

    geo2grid.sh -r glm_l2 -w geotiff -p flash_extent_density minimum_flash_area -f OR_GLM-L2-GLMC*.nc

    geo2grid.sh -r glm_l2 -w geotiff --ll-bbox -95.0 40.0 -85.0 50.0 -f OR_GLM-L2-GLMC*.nc

    geo2grid.sh -r glm_l2 -w geotiff -p average_flash_area total_energy --num-workers 4 --grid-configs=/home/g2g/my_grid.conf -g madison --method nearest -f /data/goes17/glm/
