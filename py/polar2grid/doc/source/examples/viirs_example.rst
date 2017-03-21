Creating VIIRS SDR GeoTIFF Files
--------------------------------

This example walks through the creation of VIIRS 
GeoTIFF output files and adding overlays.

Basic VIIRS SDR GeoTIFF file creation
*************************************

Find the options available when creating VIIRS SDR GeoTIFFs:

    ``polar2grid.sh viirs gtiff -h``

List the products that can be created from your VIIRS SDR dataset:

    ``polar2grid.sh viirs gtiff --list-products -f <path_to_sdr_files>``

To create VIIRS GeoTIFF files of all bands found in your data set
and reprojected in default Platte Carrée projection:

    ``polar2grid.sh viirs gtiff -f <path_to_sdr_files>``

Create a subset of VIIRS I- and M-Band reprojected GeoTIFFs:

    ``polar2grid.sh viirs gtiff -p i01 i05 m09 m14 -f <path_to_sdr_files>``

Create a true color and false color GeoTIFF:

    ``polar2grid.sh crefl gtiff --true-color --false-color -f <path_to_sdr_files>``
    
Create a true color image from a S-NPP VIIRS pass acquired on 5 March 2016, 19:32 UTC,
in Lambert Conic Conformal (LCC) projection:

.. code-block:: bash

    polar2grid.sh crefl gtiff -g lcc_fit -f /data/sdr/*.h5

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/npp_viirs_true_color_20170305_193251_lcc_fit.jpg
    :width: 100%
    :align: center

    VIIRS True color image in Lambert Conic Conformal (LCC) projection (npp_viirs_true_color_20170305_193251_lcc_fit.tif).

.. raw:: latex

    \newpage

Add coastlines,borders and latitude/longitude grid lines to the image, and write the output to the file "myfile.png":

.. code-block:: bash

    add_coastlines.sh --add-coastlines --add-borders --borders-resolution=h --borders-outline='red' --add-grid npp_viirs_true_color_20170305_193251_lcc_fit.tif -o myfile.png

.. figure:: ../_static/example_images/npp_viirs_true_color_20170305_193251_lcc_fit_overlay.png
    :width: 100%
    :align: center

    VIIRS True color image with overlays (myfile.png).
