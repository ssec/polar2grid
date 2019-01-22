Creating ABI GeoTIFF Files
--------------------------

This example walks through the creation of GOES ABI
GeoTIFF subset image files and adding overlays.

The Basics of Geo2Grid for GeoTIFF File Creation
************************************************

Find the options available when creating GOES-16 and GOES-17 
GeoTIFFs:

    ``geo2grid.sh -r abi_l1b -w geotiff -h``

List the products that can be created from your ABI dataset:

    ``geo2grid.sh -r abi_l1b -w geotiff --list-products -f <path_to_abi_files>``

To create GeoTIFF output files of all bands found in your data set, 
including true and natural color full resolution sharpened 24 bit
RGBs in standard satellite projection using 8 worker threads:

    ``geo2grid.sh -r abi_l1b -w geotiff --num-workers 8 -f <path_to_abi_files>``

Create a subset of ABI band output Geotiff image files:

    ``geo2grid.sh -r abi_l1b -w geotiff -p C01 C02 C03 C05 true_color -f <path_to_abi_files>``

Create ABI images over the given latitude/longitude region:

    ``geo2grid.sh -r abi_l1b -w geotiff --ll-bbox <lonmin latmin lonmax latmax> -f <path_to_abi_files>``

    
Create a natural color full resolution GeoTIFF from GOES-16 ABI CONUS 
observations acquired on 19 December 2018, 17:42 UTC over a bounding 
box of 95W,40N to 85W,50N.  This command assumes that all bands 
required to create the false color image are available:

.. code-block:: bash

    geo2grid.sh -r abi_l1b -w geotiff -p natural-color --ll-bbox -95.0 40.0 -85.0 50.0 -f OR_ABI-L1b-RadC*.nc

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/GOES-16_ABI_RadC_natural_color_20181219_174215_GOES-East.png
    :width: 100%
    :align: center

    ABI Natural color GeoTIFF image (GOES-16_ABI_RadC_natural_color_20181219_174215_GOES-East.tif) 

.. raw:: latex

    \newpage

Add coastlines,borders and latitude/longitude grid lines to the image, and write the output to the file "my_goes16_abi_naturalcolor.png":

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


Using Geo2Grid to Create Animations
***********************************

The advantage of Geostionary Satellites is the temporal resolution of the 
observations.  Geo2Grid offers an easy interface to creating animations from
Geo2Grid GeoTIFF files.  

Create a series of GOES-16 ABI GeoTIFF files from a time sequence of data. In
the bash shell example below, we use the ABI CONUS Band 1 files to search for all
files we have available from 19 December 2019. I then create true and natural
color images from time period that I found.

.. code-block:: bash

    ls -1 /data/abi16/*/OR_ABI-L1b-RadF-M3C01_G16_s20183531*.nc > file_list.txt

    sort_list=$(cat file_list.txt | sort)

    for file in ${sort_list} ; do

        echo ${file}
        datetime=`basename $file | cut -c27-38`
        echo "datetime :"$datetime
        geo2grid.sh -r abi_l1b -w geotiff --ll-bbox -105 23 -75 37 --num-workers 8 -p true_color natural_color -f /data/users/kathys/geo/validation/abi16/*${datetime}*.nc

     done






.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/VIIRS_true_color_in_google_earth.jpg
    :width: 100%
    :align: center

    VIIRS True color KMZ image displayed in the Google Earth
    Geobrowser.

.. raw:: latex

    \newpage
