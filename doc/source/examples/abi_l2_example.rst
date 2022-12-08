Working with ABI Level 2 Cloud Product Files
--------------------------------------------

This example walks through the creation of GOES ABI
Level 2 GeoTIFF product image files and adding overlays.

The Basics of Geo2Grid ABI L2 GeoTIFF File Creation
***************************************************

Find the options available when creating GOES-16, -17 and -18
ABI Level 2 GeoTIFFs:

    ``geo2grid.sh -r abi_l2_nc -w geotiff -h``

List the products that can be created from your ABI dataset:

    ``geo2grid.sh -r abi_l2_nc -w geotiff --list-products -f <path_to_files>``

Geo2Grid now supports two different ABI Cloud Products, cloud top
height (HT) and cloud top temperature (TEMP).  The height files use product
names ``ACHA`` while the temp files using ``ACHT``.  For instance

    ``CG_ABI-L2-ACHAC-M6_G17_s20223271831172_e20223271833556_c20223271834370.nc``

    ``CG_ABI-L2-ACHTC-M6_G17_s20223271831172_e20223271833556_c20223271834370.nc``

You can provide Geo2Grid with both files for the same date/time and it will
provide you the option to create both products with one execution.

To create GeoTIFF output files of both products found in this data set,

    ``geo2grid.sh -r abi_l2_nc -w geotiff --num-workers 8 -f <path_to_files>``

By default the products are color enhanced using the colormap:

    ``$GEO2GRID_HOME/colormaps/abi_l2_modified_cloud_top.cmap``.

Create just a Cloud Top Height Geotiff image:

    ``geo2grid.sh -r abi_l2_nc -w geotiff -p HT -f <path_to_abi_files>``

Create a Cloud Top Temperature image from the GOES-17 CONUS domain
product created from 23 November 2022, 18:31 UTC ABI observations.

.. code-block:: bash

    geo2grid.sh -r abi_l2_nc -w geotiff -p TEMP -f CG_ABI-L2-ACHTC-M6_G17_s20223271831172_e20223271833556_c20223271834370.nc

The resulting image is displayed below.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/GOES-17_ABI_TEMP_20221123_183117_GOES-West_original.png
    :width: 100%
    :align: center

    CSPP GEO ABI AIT GOES-17 Cloud Top Temperature GeoTIFF image (GOES-17_ABI_TEMP_20221123_183117_GOES-West.tif)

.. raw:: latex

    \newpage

Add a color table, coastlines, borders and latitude/longitude grid lines to the image, and write the output
to the file ``my_goes17_abi_ctt.png`` using the ``add_coastlines.sh`` script. The script provides many options,
including the ability to add a colorbar title using the font of your choice (provide the path
to the font location on your local machine):

.. code-block:: bash

    add_coastlines.sh GOES-17_ABI_TEMP_20221123_183117_GOES-West.tif --add-colorbar --colorbar-text-color="black"   --colorbar-title="GOES-17 ABI Cloud Top Temperature (°K)  23 November 2022  18:30 UTC"   --add-coastlines --coastlines-outline "black" --coastlines-level 1 --coastlines-resolution=i --add-borders --borders-level 2 --borders-outline gray --coastlines-width 2  --colorbar-tick-marks 10 --colorbar-font /usr/share/fonts/gnu-free/FreeSerifBold.ttf -o my_goes17_abi_ctt.png

.. figure:: ../_static/example_images/my_goes17_abi_ctt.png
    :width: 100%
    :align: center

    CSPP GEO ABI AIT GOES-17 Cloud Top Temperature GeoTIFF image with overlays (my_goes17_abi_ctt.png).

Users can aslo overlay Level 2 images onto other GeoTIFFS. In the example execution below, we
overaly the Cloud Top Temperature GeoTIFF image on top of the GOES-17 true color image from
the same time and name the output GeoTIFF "goes17_overlay_true_color_cloud_temperature.tif".

.. code-block:: bash

   overlay.sh GOES-17_ABI_RadC_true_color_20221123_183117_GOES-West.tif GOES-17_ABI_TEMP_20221123_183117_GOES-West.tif goes17_overlay_true_color_cloud_temperature.tif

The new combined GeoTIFF is displayed below.

.. figure:: ../_static/example_images/goes17_overlay_true_color_cloud_temperature.png
    :width: 100%
    :align: center

    CSPP GOES-17 ABI cloud top temperatures overlaid on the coincident true color image from 23 November 2022, 18:31 UTC (goes17_overlay_true_color_cloud_temperature.tif).
