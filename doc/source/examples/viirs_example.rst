Creating VIIRS SDR GeoTIFF Files
--------------------------------

This example walks through the creation of VIIRS
GeoTIFF output files and adding overlays.

Basic VIIRS SDR GeoTIFF file creation
*************************************

Find the options available when creating VIIRS SDR GeoTIFFs:

    polar2grid.sh -r viirs_sdr -w geotiff -h

List the products that can be created from your VIIRS SDR dataset:

    polar2grid.sh -r viirs_sdr -w geotiff --list-products -f <path_to_sdr_files>

.. code-block:: bash

    polar2grid.sh -r viirs_sdr -w geotiff --list-products-all -f <path_to_sdr_files>

This will provide a complete list of products that can be created
including `Satpy` and local `Custom` products.  Please note that the
`Satpy` products are available but are not officially supported.**
Need better words here. **

To create VIIRS GeoTIFF files of all default products (including true
and false color) found in your data set
and reprojected in default Platte Carrée projection using the default
4 workers:

    polar2grid.sh -r viirs_sdr -w geotiff -f <path_to_sdr_files>

Create a subset of VIIRS I- and M-Band reprojected GeoTIFFs using 8 workers:

.. code-block:: bash

    polar2grid.sh -r viirs_sdr -w geotiff -p i01 i05 m09 m14 --num-workers 8 -f <path_to_sdr_files>

Create only true color and false color GeoTIFFs with a black background (no alpha channel):

.. code-block:: bash

    polar2grid.sh -r viirs_sdr -w geotiff -p true_color false_color --fill-value 0 -f <path_to_sdr_files>

Create a true color image from a S-NPP VIIRS pass acquired on 19 September 2022, 17:53 UTC,
in Lambert Conformal Conic (LCC) projection:

.. code-block:: bash

    polar2grid.sh -r viirs_sdr -w geotiff -p true_color -g lcc_fit -f /data/sdr/*.h5

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/noaa20_viirs_true_color_20220919_175331_lcc_fit.jpg
    :width: 80%
    :align: center
    :class: with-border

    VIIRS True color image in Lambert Conformal Conic (LCC) projection (noaa20_viirs_true_color_20220919_175331_lcc_fit.tif).

.. raw:: latex

    \newpage

Add coastlines,borders and latitude/longitude grid lines to the image, and write the output to the file "myfile.png" ** Make sure this works with latest P2G **:

.. code-block:: bash

    add_coastlines.sh --add-coastlines --add-borders --borders-resolution=h --borders-outline='red' --add-grid  noaa20_viirs_true_color_20220919_175331_lcc_fit.tif -o myfile.png

.. figure:: ../_static/example_images/noaa20_viirs_true_color_20220919_175331_lcc_fit_overlay.png
    :width: 80%
    :align: center

    VIIRS True color image with overlays (myfile.png).

******Need to confirm this works******. Convert the true color GeoTIFF file into a Google Earth compatible
Keyhole Markup language Zipped (KMZ) file.

.. code-block:: bash

   gtiff2kmz.sh noaa20_viirs_true_color_20220919_175331_lcc_fit.tif

which creates the `noaa20_viirs_true_color_20220919_175331_lcc_fit.kmz`
file. When displayed in Google Earth this image appears as:

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/noaa20_viirs_true_color_20220919_175331_lcc_fit_in_google_earth.jpg
    :width: 100%
    :align: center

    VIIRS True color KMZ image displayed in the Google Earth Geobrowser.

.. raw:: latex

    \newpage
