AMSR2 L1B - Example 1
---------------------

This example walks through some common tasks when working with
GCOM-W1 AMSR2 L1B data.

Basic GeoTIFF file creation
***************************

.. code-block:: bash

    polar2grid.sh amsr2_l1b gtiff -f  GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5

produces these files in WGS84 (Plate Carrée) projection:

.. parsed-literal::

    gcom-w1_amsr2_btemp_36\.5h_20160719_190300_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_36\.5v_20160719_190300_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0ah_20160719_190300_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0av_20160719_190300_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bh_20160719_190300_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bv_20160719_190300_wgs84_fit\.tif

.. figure:: ../_static/example_images/gcom-w1_amsr2_btemp_36.5h_20160719_190300_wgs84_fit.jpg
    :width: 50%
    :align: center

    GCOMW-1 AMSR2 L1B 36.5H Brightness Temperature

Naval Research Lab (NRL) Image Reproduction
*******************************************

.. code-block:: bash

    polar2grid.sh amsr2_l1b gtiff --rescale-configs $POLAR2GRID_HOME/rescale_configs/amsr2_png.ini -g lcc_fit -f ../data/ GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5

produces these Lambert Conformal Conic (LCC) geotiff files:

.. parsed-literal::

    gcom-w1_amsr2_btemp_36\.5h_20160719_190300_lcc_fit\.tif
    gcom-w1_amsr2_btemp_36\.5v_20160719_190300_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0ah_20160719_190300_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0av_20160719_190300_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bh_20160719_190300_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bv_20160719_190300_lcc_fit\.tif

.. figure:: ../_static/example_images/gcom-w1_amsr2_btemp_89.0ah_20160719_190300_lcc_fit.jpg
    :name: gcom-w1_amsr2_btemp_89.0ah_20160719_190300_lcc_fit.jpg
    :width: 50%
    :align: center

    GCOMW-1 AMSR2 L1B 89.0A/H Brightness Temperature
