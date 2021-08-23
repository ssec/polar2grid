VIIRS EDR Flood Reader
======================

.. automodule:: polar2grid.readers.viirs_edr_flood
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.viirs_edr_flood
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh viirs_edr_flood <writer>
    :passparser:

The end product GeoTIFF file is color enhanced using the color map 
described in the CSPP VIIRS Flood Detection Software Version 1.1 and
shown below.

.. figure:: ../_static/example_images/Flood_Legend.png
    :width: 30%
    :align: center

Please note that since the CSPP VIIRS Flood Detection Product is
a gridded product that has already been reprojected 
(cylindrical equidistant), it requires more time to reproject the 
data onto any other grid.  It is recommended that if users want 
to re-grid the output Flood HDF4 product, that they choose small 
sections of data.

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh viirs_edr_flood gtiff -h

    polar2grid.sh viirs_edr_flood gtiff -g lcc_fit -f 

    

    
