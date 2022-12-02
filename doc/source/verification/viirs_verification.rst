Executing the VIIRS Polar2Grid Test Case
----------------------------------------

To run the VIIRS GeoTIFF test case, unpack the test data as
shown in Section 2.2 and execute the following commands:

.. code-block:: bash

    cd polar2grid_test/viirs
    mkdir work
    cd work
    polar2grid.sh -r viirs_sdr -w geotiff -p true_color false_color --grid-configs \
      ${POLAR2GRID_HOME}/grid_configs/grid_example.yaml -g miami --weight-distance-max 1 -f ../input

The test case consists of 6 input direct broadcast HDF 5 SDR granules
for a selection of VIIRS bands from a pass acquired on 19 March 2017
at 18:32 UTC. In this test, the Polar2Grid software
is using the example configuration file
(${POLAR2GRID_HOME}/grid_configs/grid_example.yaml) and the lambert
conformal conic (lcc) miami grid definition entry located
within it. We will create one true and one false color image at
300 m resolution, 750 lines x 1000 elements centered on the US city of
Miami in the state of Florida.

The creation of the true and false color images includes the Atmospheric
Rayleigh Scattering Correction, and sharpening of the
image to the spatial resolution of the VIIRS I-Bands.
We are using a ``--weight-distance-max`` option of ``1`` to inform the elliptical
weight averaging (EWA) technique how to weight the effect of the input
pixel to an output pixel based upon its location in the scan line and
other calculated coefficients. Although this may result in the
"sharpest" output resolution image, the user should be aware that
with reprojecting VIIRS terrain corrected imagery this may lead to
black missing data sections in regions of varying terrains, especially
at higher view angles.  That is why the default ``--weight-distance-max``
value is ``2``.

The processing should run in less than 2 minutes and create 2 atmospherically
corrected and sharpened output VIIRS GeoTIFF true and false
color images.

If the VIIRS Polar2Grid processing script runs normally, it will return
a status code equal to zero. If the VIIRS Polar2Grid processing script
encounters a fatal error, it will return a non-zero status code.

To verify your output files against the output files created at
UW/SSEC, execute the following commands:

.. code-block:: bash

    cd ..
    p2g_compare.sh output work

This script compares the values of all bands in the GeoTIFF file
for the true and false color high resolution images. The verification
text string from our test system is shown below.

.. code-block:: bash

    p2g_compare.sh output work

    Comparing work/npp_viirs_false_color_20170319_183246_miami.tif to known valid file
    INFO:__main__:Comparing 'work/npp_viirs_false_color_20170319_183246_miami.tif' to known valid file 'output/npp_viirs_false_color_20170319_183246_miami.tif'.
    INFO:__main__:0 pixels out of 3000000 pixels are different
    INFO:__main__:Comparing 'work/npp_viirs_true_color_20170319_183246_miami.tif' to known valid file 'output/npp_viirs_true_color_20170319_183246_miami.tif'.
    INFO:__main__:0 pixels out of 3000000 pixels are different
    All files passed
    SUCCESS

The VIIRS true color GeoTIFF image created from the test data
is displayed below:

.. figure:: ../_static/example_images/npp_viirs_true_color_20170319_183246_miami.jpg
    :width: 100%
    :align: center

    GeoTIFF true color image created from the 19 March 2017 VIIRS test data centered on Miami, Florida.
