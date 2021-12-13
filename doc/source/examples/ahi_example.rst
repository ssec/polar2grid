Working with AHI Files
----------------------

This example walks through the creation of Himawari AHI
GeoTIFF subset image files and adding overlays.

The Basics of Geo2Grid for AHI GeoTIFF File Creation
****************************************************

Find the options available when creating AHI HSD
GeoTIFFs:

    ``geo2grid.sh -r ahi_hsd -w geotiff -h``

List the products that can be created from your AHI HSD dataset:

    ``geo2grid.sh -r ahi_hsd -w geotiff --list-products -f <path_to_files>``

To create GeoTIFF output files of all bands found in your data set,
including true and natural color full resolution sharpened 24 bit
RGBs in standard satellite projection using 8 worker threads:

    ``geo2grid.sh -r ahi_hsd -w geotiff --num-workers 8 -f <path_to_files>``

Create a subset of AHI band output Geotiff image files for Bands 1, 2, 3, 4 and 5:

    ``geo2grid.sh -r ahi_hsd -w geotiff -p B01 B02 B03 B04 B05 natural_color -f <path_to_ahi_files>``

Create AHI images over a Lambert Conic Conformal (LCC) grid centered over
Perth, Australia.

Run the grid helper script to define the grid center, areal extent, spatial
resolution and projection .

    ``p2g_grid_helper.sh perth 117.9 -32.4 500 500 1500 1500``

    ``perth, proj4, +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=-32.40000 +lat_1=-32.40000 +lon_0=117.90000 +units=m +no_defs, 1500, 1500, 500.00000, -500.00000, 114.05895deg, -28.95876deg``

Copy the output grid projection information into a grid configuration
text file. Use the grid to create an HSD AHI true color image from
data observed on 12 November 2017, at 23:30 UTC.

.. code-block:: bash

    geo2grid.sh -r ahi_hsd -w geotiff -p true_color --grid-configs=/geo/hsd/my_grid.conf -g perth --method nearest -f /data/ahi8/hsd/2330/*FLDK*.DAT

The resulting image is displayed beow.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/HIMAWARI-8_AHI_true_color_20181112_233020_perth_example.png
    :width: 100%
    :align: center

    AHI True color GeoTIFF image centered on Perth, Australia (HIMAWARI-8_AHI_true_color_20181112_233020_perth.tif).

.. raw:: latex

    \newpage

Add coastlines, borders and latitude/longitude grid lines and rivers to the image.

.. code-block:: bash

    add_coastlines.sh --add-coastlines --add-rivers --rivers-resolution=h --add-grid HIMAWARI-8_AHI_true_color_20181112_233020_perth.tif

.. figure:: ../_static/example_images/HIMAWARI-8_AHI_true_color_20181112_233020_perth.png
    :width: 100%
    :align: center

    Himawari-8 AHI true color image with overlays (HIMAWARI-8_AHI_true_color_20181112_233020_perth.png)
