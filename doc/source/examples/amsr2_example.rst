.. raw:: latex

    \newpage

Creating AMSR2 Reprojections
----------------------------

This example walks through some common tasks when working with
GCOM-W1 AMSR2 Level 1B data.

Creating AMSR2 GeoTIFF files
****************************

Find the options available for creating AMSR2 Level 1B GeoTIFFs:

   ``polar2grid.sh amsr2_l1b gtiff -h``

List the products that can be created from your AMSR2 HDF5 dataset:

    ``polar2grid.sh amsr2_l1b gtiff --list-products -f <path_to_l1b_file>``

To create AMSR2 GeoTIFF files of all bands found in your data set 
and reprojected in default Platte Carrée projection:

     ``polar2grid.sh amsr2_l1b gtiff -f <path_to_l1b_file>``

Create default set of GeoTIFF images for the AMSR2 Level 1B file acquired
on 19 July 2016, at 19:03 UTC:

.. code-block:: bash

    polar2grid.sh amsr2_l1b gtiff -f GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5

produces these files in WGS84 (Platte Carrée) projection:

.. parsed-literal::

    gcom-w1_amsr2_btemp_36\.5h_20160719_190300_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_36\.5v_20160719_190300_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0ah_20160719_190300_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0av_20160719_190300_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bh_20160719_190300_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bv_20160719_190300_wgs84_fit\.tif

The GeoTIFF image for AMSR2 36.5H GHz band is displayed below.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/gcom-w1_amsr2_btemp_36.5h_20160719_190300_wgs84_fit.jpg
    :width: 40%
    :align: center

    GCOMW-1 AMSR2 L1B 36.5H GHz brightness temperatures using default scaling.  Data set was observed at 19:03 UTC on 19 July 2016.

Naval Research Lab (NRL) Image Reproductions
********************************************

Polar2Grid inclues the capability to reproduce the AMSR2 color enhanced
images staged on the the Naval Research Lab (NRL) tropical cyclone
page:  http://www.nrlmry.navy.mil/TC.html

First, create a reprojected GeoTIFF in Lambert Conic Conformal (LCC) projection
and rescale the data using the test data set from 19 July 2016:

.. code-block:: bash

    polar2grid.sh amsr2_l1b gtiff --rescale-configs $POLAR2GRID_HOME/rescale_configs/amsr2_png.ini -g lcc_fit -f ../data/GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5

Executing this command produces these AMSR2 LCC GeoTIFF files:

.. parsed-literal::

    gcom-w1_amsr2_btemp_36\.5h_20160719_190300_lcc_fit\.tif
    gcom-w1_amsr2_btemp_36\.5v_20160719_190300_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0ah_20160719_190300_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0av_20160719_190300_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bh_20160719_190300_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bv_20160719_190300_lcc_fit\.tif

the rescaled image for AMSR2 89.0A/H GHz band is displayed below.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/gcom-w1_amsr2_btemp_89.0ah_20160719_190300_lcc_fit.jpg
    :name: gcom-w1_amsr2_btemp_89.0ah_20160719_190300_lcc_fit.jpg
    :width: 40%
    :align: center

    GCOMW-1 AMSR2 L1B 89.0A/H GHz brightness temperatures reprojected in Lambert Conic Conformal Projection and rescaled.  Data set was observed at 19:03 UTC on 19 July 2016.

To add a Naval Research Lab (NRL) color table to the image, use the following
command:

.. code-block:: bash

    add_colormap.sh ${POLAR2GRID_HOME}/colormaps/amsr2_89h.cmap gcom-w1_amsr2_btemp_89.0ah_20160719_190300_lcc_fit.tif

This command adds the enhancement to the original GeoTIFF.  The final product
is displayed below:

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/gcom-w1_amsr2_btemp_89.0ah_20160719_190300_lcc_fit_color.jpg
    :name: gcom-w1_amsr2_btemp_89.0ah_20160719_190300_lcc_fit_color.jpg
    :width: 60%
    :align: center

    GCOMW-1 AMSR2 L1B 89.0A/H GHz brightness temperatures reprojected in Lambert Conic Conformal Projection and rescaled and enhanced using the Naval Research Lab color enahcnement.  Data set was observed at 19:03 UTC on 19 July 2016.
