VIIRS EDR Active Fires Reader
=============================

.. automodule:: polar2grid.readers.viirs_edr_active_fires
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.viirs_edr_active_fires
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r viirs_edr_active_fires -w <writer>
    :passparser:

Some output GeoTIFF fire products are color enhanced:

AFIMG 

    confidence_cat - Low (Yellow), Nominal (Orange), High (Red)

        power - 1 - 250 and above (MW) Yellow->Red

AFMOD 

    confidence_pct - 1-100% Yellow->Red

        power - 1 - 250 and above (MW) Yellow->Red

Examples:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh -r viirs_edr_active_fires -w geotiff -h
    
    polar2grid.sh -r viirs_edr_active_fires -w geotiff --list-products -f ../active_fire_edr/AFIMG*.nc

    polar2grid.sh -r viirs_edr_active_fires -w geotiff --list-products -f ../active_fire_edr/AFMOD*.nc

    polar2grid.sh -r viirs_edr_active_fires -w geotiff -p confidence_cat T4 img_edr/AFIMG*.nc

    polar2grid.sh -r viirs_edr_active_fires -w geotiff -g lcc_aus -p confidence_pct T13  -f AFMOD_j01_d20191120_t1513353_e1514581_b10389_c20191121192444396115_cspp_dev.nc

**NOTE:** The active fire images can be overlaid onto another GeoTIFF. 
See :ref:`util_script_fireoverlay` for instructions.

    

    

    

    


  
    
