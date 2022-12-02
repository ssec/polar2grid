Working with ABI Files
----------------------

This example walks through the creation of GOES ABI
GeoTIFF subset image files and adding overlays.

The Basics of Geo2Grid for ABI GeoTIFF File Creation
****************************************************

Find the options available when creating GOES-16, -17 and -18
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


Create a natural color full resolution GeoTIFF from GOES-18 ABI
observations acquired on 15 November 2022, 18:30 UTC over a latitude/
longitude bounding box of 128W,30N to -118W,40N .  This command
assumes that all bands required to create the false color image are available:

.. code-block:: bash

    geo2grid.sh -r abi_l1b -w geotiff -p natural_color --ll-bbox -128 30 -118 40 -f OR_ABI-L1b-RadF-M6C*_G18_s20223191830*.nc

The resulting image is displayed below.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/GOES-18_ABI_RadF_natural_color_20221115_183020_GOES-West_cutout.png
    :width: 100%
    :align: center

    ABI Natural color subset GeoTIFF image (GOES-18_ABI_RadF_natural_color_20221115_183020_GOES-West.tif)

.. raw:: latex

    \newpage

Add coastlines, borders and latitude/longitude grid lines to the image, and write the output to the file "my_goes18_abi_naturalcolor.png":

.. code-block:: bash

    add_coastlines.sh --add-coastlines --add-borders --borders-resolution=h --borders-outline='red' --add-grid GOES-18_ABI_RadF_natural_color_20221115_183020_GOES-West.tif -o my_goes18_abi_naturalcolor.png

.. figure:: ../_static/example_images/my_goes18_abi_naturalcolor.png
    :width: 100%
    :align: center

    GOES-18 natural color image with overlays (my_goes18_abi_naturalcolor.png).

Convert the natural color GeoTIFF file into a Google Earth compatible
Keyhole Markup language Zipped (KMZ) file.

.. code-block:: bash

   gtiff2kmz.sh GOES-18_ABI_RadF_natural_color_20221115_183020_GOES-West.tif

which creates the `GOES-18_ABI_RadF_natural_color_20221115_183020_GOES-West.kmz`
file which can then be displayed easily in the Google Earth GeoBrowser.
