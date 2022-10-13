Executing the MODIS Polar2Grid Test Case
----------------------------------------

To run the MODIS GeoTIFF test case, unpack the test data as
shown in Section 2.2 and execute the following commands:

.. code-block:: bash

    cd polar2grid_test/modis
    mkdir work
    cd work 
    polar2grid.sh -r modis -w geotiff -p true_color false_color --fill-value 0 \
      --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.yaml -g miami -f ../input/

The test case consists of a set of MODIS archived 5 minute HDF 4 Level 1B
granule files (1KM, HKM, QKM and Geolocation) for a Terra MODIS
pass observed on 19 March 2017 at 16:30 UTC. In this test,
the Polar2Grid software is using the example configuration file
(${POLAR2GRID_HOME}/grid_configs/grid_example.yaml) and the lambert
conformal conic (lcc) “miami” grid definition entry located
within it. The software goes through a number of steps to produce
the true and false color imagery, include the removal of the atmospheric
Rayleigh Scattering, creation of reflectances from the normalized
radiances, sharpening the image to full resolution and combining
the 3 bands into on 24-bit output GeoTIFF files. The end result
is one true and one false color image at
300 m resolution, 750 lines x 1000 elements centered on the US city of
Miami in the state of Florida. The processing should run in less than
2 minutes.

If the MODIS Polar2Grid processing script runs normally, it will return
a status code equal to zero. If the MODIS Polar2Grid processing script
encounters a fatal error, it will return a non-zero status code.

To verify your output files against the output files created at
UW/SSEC, execute the following commands:


.. code-block:: bash

    cd ..
    ./p2g_compare.sh output work

This script compares the values of all bands in the GeoTIFF file
for the true and false color high resolution images. The verification
text string from our test system is shown below.

.. code-block:: bash

    ./p2g_compare.sh output work


    Comparing output/terra_modis_false_color_20170319_163000_miami.tif to known valid file
    SUCCESS: 0 pixels out of 750000 pixels are different
    Comparing output/terra_modis_true_color_20170319_163000_miami.tif to known valid file
    SUCCESS: 0 pixels out of 750000 pixels are different
    All files passed
    SUCCESS

The Terra MODIS false color GeoTIFF image created from the test data
is displayed below:

.. figure:: ../_static/example_images/terra_modis_false_color_20170319_163000_miami_p2g_v3.png
    :width: 100%
    :align: center

    GeoTIFF false color image created from the 19 March 2017 Terra MODIS test data centered on Miami, Florida.
