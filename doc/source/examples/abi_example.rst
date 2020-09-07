Working with ABI Files
----------------------

This example walks through the creation of GOES ABI
GeoTIFF subset image files and adding overlays.

The Basics of Geo2Grid for ABI GeoTIFF File Creation
****************************************************

Find the options available when creating GOES-16 and GOES-17 
GeoTIFFs:

    ``geo2grid.sh -r abi_l1b -w geotiff -h``

List the products that can be created from your ABI dataset:

    ``geo2grid.sh -r abi_l1b -w geotiff --list-products -f <path_to_files>``

To create GeoTIFF output files of all bands found in your data set, 
including true and natural color full resolution sharpened 24 bit
RGBs in standard satellite projection using 8 worker threads:

    ``geo2grid.sh -r abi_l1b -w geotiff --num-workers 8 -f <path_to_files>``

Create a subset of ABI band output Geotiff image files for Channels 1, 2, 3 and 5:

    ``geo2grid.sh -r abi_l1b -w geotiff -p C01 C02 C03 C05 true_color -f <path_to_abi_files>``

Create ABI images over the given latitude/longitude region:

    ``geo2grid.sh -r abi_l1b -w geotiff --ll-bbox <lonmin latmin lonmax latmax> -f <path_to_abi_files>``

    
Create a natural color full resolution GeoTIFF from GOES-16 ABI CONUS 
observations acquired on 19 December 2018, 17:42 UTC over a bounding 
box of 95W,40N to 85W,50N.  This command assumes that all bands 
required to create the false color image are available:

.. code-block:: bash

    geo2grid.sh -r abi_l1b -w geotiff -p natural_color --ll-bbox -95.0 40.0 -85.0 50.0 -f OR_ABI-L1b-RadC*.nc

The resulting image is displayed below.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/GOES-16_ABI_RadC_natural_color_20181219_174215_GOES-East.png
    :width: 100%
    :align: center

    ABI Natural color GeoTIFF image (GOES-16_ABI_RadC_natural_color_20181219_174215_GOES-East.tif) 

.. raw:: latex

    \newpage

Add coastlines, borders and latitude/longitude grid lines to the image, and write the output to the file "my_goes16_abi_naturalcolor.png":

.. code-block:: bash

    add_coastlines.sh --add-coastlines --add-borders --borders-resolution=h --borders-outline='red' --add-grid GOES-16_ABI_RadC_natural_color_20181219_174215_GOES-East.tif -o my_goes16_abi_naturalcolor.png

.. figure:: ../_static/example_images/my_goes16_abi_naturalcolor.png
    :width: 100%
    :align: center

    GOES-16 natural color image with overlays (my_goes16_abi_naturalcolor.png).

Convert the natural color GeoTIFF file into a Google Earth compatible 
Keyhole Markup language Zipped (KMZ) file.

.. code-block:: bash

   gtiff2kmz.sh GOES-16_ABI_RadC_natural_color_20181219_174215_GOES-East.tif

which creates the `GOES-16_ABI_RadC_natural_color_20181219_174215_GOES-East.kmz`
file which can then be displayed easily in the Google Earth GeoBrowser.
