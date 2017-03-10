Creating MODIS AWIPS Compatible Files
-------------------------------------

This example walks through the creation of MODIS
NetCDF files for display in AWIPS.

Basic MODIS Level 1B GeoTIFF file creation
******************************************

Find the options available when creating MODIS AWIPS files:

    polar2grid.sh modis awips -h

List the products that can be created from your MODIS L1B dataset:

    polar2grid.sh modis awips --list-products -f <path_to_sdr_files>

To create MODIS AWIPS NetCDF files of all products found in your data set
for all AWIPS grids overlaid by your data:

    polar2grid.sh modis awips -f <path_to_sdr_files>

Create a subset of MODIS reprojected AWIPS products for a specfic AWIPS grid:

    polar2grid.sh modis awips -p bt27 vis02 -g 211e -f <path_to_sdr_files>

.. figure:: ../_static/example_images/SSEC_AWIPS_aqua_modis_vis02_211e_20170308_181800.nc.png
    :width: 100%
    :align: center

    AWIPS display of Aqua MODIS Band 2 (.86 micron) reflectances from 18:18 UTC, 8 March 2017.
    

Create true color and false color Aqua MODIS AWIPS NetCDF files from the 1000m, 500m, 250m and geolocation pass files acquired on 8 March 2017 at 18:18 UTC, reprojected onto the AWIPS 211e grid:

.. code-block:: bash

    polar2grid.sh crefl awips --true-color --false-color --fornav-D 10 -g 211e -f ../l1b/a1.17006.1855.1000m.hdf ../l1b/a1.17006.1855.500m.hdf  ../l1b/a1.17006.1855.250m.hdf ../l1b/a1.17006.1855.geo.hdf 

.. figure:: ../_static/example_images/npp_viirs_true_color_20170305_193251_lcc_fit_overlay.png
    :width: 100%
    :align: center

    Place holder for MODIS true color image in AWIPS-II.
