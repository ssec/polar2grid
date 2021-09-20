Executing the MODIS Polar2Grid Test Case
----------------------------------------

To run the MODIS GeoTIFF test case, unpack the test data as
shown in Section 2.2 and execute the following commands:

.. code-block:: bash

    cd polar2grid_test/modis
    mkdir work
    cd work
    polar2grid.sh crefl gtiff --true-color --false-color --fornav-d 1 --grid-configs \
      ${POLAR2GRID_HOME}/grid_configs/grid_example.yaml -g miami -f ../input

The test case consists of a set of MODIS archived 5 minute HDF 4 Level 1B
granule files (1KM, HKM, QKM and Geolocation) for a Terra MODIS
pass observed on 19 March 2017 at 16:30 UTC. In this test, 
the Polar2Grid software is using the example configuration file 
(${POLAR2GRID_HOME}/grid_configs/grid_example.yaml) and the lambert
conformal conic (lcc) “miami” grid definition entry located 
within it. It will first create Corrected REFLectance (CREFL) HDF4 files
and then use those to create one true and one false color image at 
300 m resolution, 500 lines x 700 elements centered on the US city of 
Miami in the state of Florida. The processing should run in less than 
2 minutes and create 9 CREFL output MODIS GeoTIFF files, including 
both true and false color output images, and the individual Corrected 
Reflectance images that went into producing the final products. 

If the MODIS Polar2Grid processing script runs normally, it will return 
a status code equal to zero. If the MODIS Polar2Grid processing script 
encounters a fatal error, it will return a non-zero status code.

To verify your output files against the output files created at 
UW/SSEC, execute the following commands:


.. code-block:: bash

    cd ..
    ./p2g_compare_geotiff.sh output work

This script compares the values of all the GeoTIFF files for all 
MODIS Bands found. The output from our test system is shown below. 

.. code-block:: bash

    ./p2g_compare_geotiff.sh output work
    Comparing work/terra_modis_false_color_20170319_163000_miami.tif to known valid file
    SUCCESS: 0 pixels out of 750000 pixels are different
    Comparing work/terra_modis_modis_crefl01_250m_20170319_163000_miami.tif to known valid file
    SUCCESS: 0 pixels out of 750000 pixels are different
    Comparing work/terra_modis_modis_crefl01_500m_20170319_163000_miami.tif to known valid file
    SUCCESS: 0 pixels out of 750000 pixels are different
    Comparing work/terra_modis_modis_crefl02_500m_20170319_163000_miami.tif to known valid file
    SUCCESS: 0 pixels out of 750000 pixels are different
    Comparing work/terra_modis_modis_crefl03_500m_20170319_163000_miami.tif to known valid file
    SUCCESS: 0 pixels out of 750000 pixels are different
    Comparing work/terra_modis_modis_crefl04_500m_20170319_163000_miami.tif to known valid file
    SUCCESS: 0 pixels out of 750000 pixels are different
    Comparing work/terra_modis_modis_crefl07_500m_20170319_163000_miami.tif to known valid file
    SUCCESS: 0 pixels out of 750000 pixels are different
    Comparing work/terra_modis_true_color_20170319_163000_miami.tif to known valid file
    SUCCESS: 0 pixels out of 750000 pixels are different
    All files passed
    SUCCESS

The Terra MODIS false color GeoTIFF image created from the test data 
is displayed below:

.. figure:: ../_static/example_images/terra_modis_false_color_20170319_163000_miami.jpg
    :width: 100%
    :align: center

    GeoTIFF false color image created from the 19 March 2017 Terra MODIS test data centered on Miami, Florida.
