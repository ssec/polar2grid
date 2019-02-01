Executing the ABI Geo2Grid Test Case
------------------------------------

To confirm a successful Geo2Grid installation, follow these 
instructions to create a set of GOES-16 ABI GeoTIFF files from
a single time period.

Unpack the test data as shown in Section 2.2 and 
execute the following commands:

.. code-block:: bash

    cd geo2grid_test/abi
    mkdir work
    cd work
    geo2grid.sh -r abi_l1b -w geotiff --num-workers 8 --progress  -f ../input

The test case consists of a 7 band subset of Full Disk Level 1B 
GOES-16 ABI calibrated NetCDF files from 17:45 UTC on 19 December 2018.  
The dataset includes GOES-16 ABI Bands 1, 2, 3, 5, 7, 9, and 14.  

In this test, the Geo2Grid software will create by default as many
single band full resolution Full Disk GeoTIFF files as possible, as 
well as true and natural color images. The true and natural color 
images are by default atmospherically corrected and spatially 
sharpened to 500 m resolution in native satellite 
projection.  As it is executing, a progress bar will update, and 
8 CPU threads will be used if available. On modern computers, the 
execution should take around 10-15 minutes.  

The output files are large, including the true and natural color
images that are greater than 1 GB (21696 lines x 21696 elements).

The software uses ABI Band 1 (.47 micron), Band 2 (.64 micron) and
Band 3 (.86 micron) reflectances to create a "Green" Band, which is
in turn combined with Bands 1 and 2 to create the true color imagery.
The natural color image is created by combining ABI Band 2 (.64 micron),
Band 3 (.86 micron) and Band 5 (1.6 micron) reflectances.  Both
true and natural color images are sharpened to 500 m spatial
resolution by using the textual information provided by Band 2 (.64 
micron).  

If the ABI Geo2Grid processing script runs normally, it will return
a status code equal to zero. If the ABI Geo2Grid processing script
encounters a fatal error, it will return a non-zero status code.

To verify your output files against the output files created at 
UW/SSEC, execute the following commands:

.. code-block:: bash

    cd ..
    ./g2g_compare_geotiff.sh output work

This script compares the values of all the GeoTIFF files for all 
ABI Bands found. The output from our test system is shown below. 

.. code-block:: bash

    ./g2g_compare_geotiff.sh output work
    Comparing work/GOES-16_ABI_RadF_C01_20181219_174533_GOES-East.tif to known valid file
    SUCCESS: 0 pixels out of 117679104 pixels are different
    Comparing work/GOES-16_ABI_RadF_C02_20181219_174533_GOES-East.tif to known valid file
    SUCCESS: 0 pixels out of 470716416 pixels are different
    Comparing work/GOES-16_ABI_RadF_C03_20181219_174533_GOES-East.tif to known valid file
    SUCCESS: 0 pixels out of 117679104 pixels are different
    Comparing work/GOES-16_ABI_RadF_C05_20181219_174533_GOES-East.tif to known valid file
    SUCCESS: 0 pixels out of 117679104 pixels are different
    Comparing work/GOES-16_ABI_RadF_C07_20181219_174533_GOES-East.tif to known valid file
    SUCCESS: 0 pixels out of 29419776 pixels are different
    Comparing work/GOES-16_ABI_RadF_C09_20181219_174533_GOES-East.tif to known valid file
    SUCCESS: 0 pixels out of 29419776 pixels are different
    Comparing work/GOES-16_ABI_RadF_C14_20181219_174533_GOES-East.tif to known valid file
    SUCCESS: 0 pixels out of 29419776 pixels are different
    Comparing work/GOES-16_ABI_RadF_natural_color_20181219_174533_GOES-East.tif to known valid file
    SUCCESS: 0 pixels out of 470716416 pixels are different
    Comparing work/GOES-16_ABI_RadF_true_color_20181219_174533_GOES-East.tif to known valid file
    SUCCESS: 0 pixels out of 470716416 pixels are different
    All files passed
    SUCCESS

A montage of the 9 output GeoTIFF files (7 single band and 2 RGB images) 
is displayed below.

.. figure:: ../_static/example_images/abi_20181219_1745_montage.jpg
    :width: 100%
    :align: center

    GOES-16 ABI montage of images created from the Geo2Grid verification
    data observed on 19 December 2018 at 17:45 UTC. The images are 
    from top to bottom, right to left, bands 1, 2, 3, 5, 7, 9, 14, 
    natural color and true color.






