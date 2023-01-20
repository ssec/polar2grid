.. raw:: latex

    \newpage

Creating MODIS AWIPS Compatible Files
-------------------------------------

This example walks through the creation of MODIS
NetCDF files for display in AWIPS.

Basic MODIS Level 1B AWIPS compatible file creation
***************************************************

Find the options available when creating MODIS AWIPS files:

    ``polar2grid.sh -r modis -w awips_tiled -h``

List the products that can be created from your MODIS L1B dataset.  For
the new Sectorized Cloud and Moisture Imagery (SCMI) AWIPS writer, include
the sector name (see Section 6.1.3) either Lambert Conformal Conic (LCC),
Pacific, Mercator, or Polar:

    ``polar2grid.sh -r modis -w awips_tiled --sector-id LCC --list-products -f <path_to_files>``

Follow the command below to create MODIS AWIPS NetCDF files of all
Level 1B products found in your data set for your sector.  When
using the ``awips_tiled`` scmi server, it is advised that a specific grid be chosen, and
that the ``--letters`` and ``--compress`` options are used.
In our LCC example, we will use the 1km grid:

    ``polar2grid.sh -r modis -w scmi --sector-id LCC --letters --compress -g lcc_conus_1km -f <path_to_files>``

Create a subset of MODIS reprojected AWIPS products for a specfic AWIPS grid:

.. code-block:: bash

    polar2grid.sh -r modis -w awips_tiled -p bt27 vis02 --sector-id LCC --letters --compress -g lcc_conus_1km -f <path_to__files>


.. figure:: ../_static/example_images/modis_vis02_example.png
    :width: 100%
    :align: center

    AWIPS display of Aqua MODIS Band 2 (.86 micron) reflectances from 20:52 UTC, 16 October 2022.


Create true color and false color Aqua MODIS AWIPS NetCDF files from the 1000m, 500m, 250m and geolocation pass files acquired on 16 October 2022 at 20:52 UTC, reprojected onto the LCC 300m lettered grid.

.. code-block:: bash

    polar2grid.sh -r modis -w awips_tiled --awips-true-color --awips-false-color --sector-id LCC --letters --compress -g lcc_conus_300 -f l1b/a1.22289.2052.1000m.hdf  l1b/a1.22289.2052.250m.hdf  l1b/a1.22289.2052.500m.hdf  l1b/a1.22289.2052.geo.hdf

.. figure:: ../_static/example_images/modis_true_color_example.png
    :width: 100%
    :align: center

    AWIPS display of Polar2Grid MODIS corrected reflectances combined to create a 24 bit true color image.  Data was collected from a Aqua MODIS pass at 20:52 UTC, 16 October 2022.
