Corrected Reflectance Reader
============================

.. automodule:: polar2grid.crefl.crefl2swath

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.crefl.crefl2swath
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh crefl <writer>
    :passparser:

Example 1 - Create True Color GeoTIFFs and KML/KMZ
--------------------------------------------------

The Polar2Grid software can create reprojected true
color and false color GeoTIFF output from
input VIIRS corrected reflectance (CREFL) HDF4
input files and VIIRS Geolocation files
(Terrain Corrected (GITCO* and GMTCO* or
non-Terrain Corrected (GMODO* and GIMGO*)) as well as
MODIS Level 1B (L1B) files, in either IMAPP or NASA
Archive naming conventions.

Polar2Grid software creates and combines single
band CREFL VIIRS Red (M-Band 5), Green (M- Band 4)
and Blue (M-Band 3) wavelength data or CREFL MODIS
Red (MODIS Band 1), Green (MODIS Band 4) and Blue
(MODIS Band 3) wavelength data to create true
color images. If the VIIRS I-Band 1 data is also present in a
CREFL file, then it will be used to spatially
sharpen the image to about 350m resolution.  For
MODIS, Polar2Grid uses the 1km CREFL file to
create a true color image, but if the 250m L1B
CREFL file is available then it will be used to
spatially sharpen the image to about 250m.
For the highest quality and resolution MODIS
images, all three 1km, 500m and 250m input Level
1B files should be used.

The CREFL software performs a simple atmospheric
Rayleigh scattering correction but with no
adjustment for aerosol scattering (smoke and
aerosols are still visible). 

If no CREFL files are presented to the Polar2Grid
CREFL reader, the files will automatically be created
as part of the execution.

In this example, we start with the creation of a 
true color VIIRS GeoTIFF files. If you are interested in 
a KMZ formatted file, a GeoTIFF must be created first:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh crefl gtiff -f /path/to/my_sdrs/

This will create a series of corrected reflectance GeoTIFF files 
that are used to the produce the final 24 bit true color 
GeoTIFF with the ``.tif`` file extension. To create a KMZ file
(a compressed KML) to show in Google Earth or other program 
use the ``gtiff2kmz.sh`` script provided in the software bundle:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/gtiff2kmz.sh input_true_color.tif output_true_color.kmz

Where the ``input_true_color.tif`` file is one of the files 
created from the ``crefl2gtiff.sh``
command and ``output_true_color.kmz`` is the name of the KMZ file to create.

For more information see the documentation for the
the :doc:`GeoTIFF Writer <../writers/gtiff>` and :ref:`util_gtiff2kmz`
documentation.

Example 2 - Creating False Color GeoTIFFs and KML/KMZ
-----------------------------------------------------

A false color image is any combination of 3 bands 
outside of those used to create a "true color" image.
The Polar2Grid can also readily create a
false color Red/Green/Blue 24 bit GeoTIFF using 
Red:VIIRS M-Band 11 (2.25 μm) or MODIS Band 7 (2.21 μm),
Green:VIIRS M-Band 7 (.87 μm) or MODIS Band 2 (.86 μm)
and Blue:VIIRS M-Band 5 (.67 μm) or MODIS Band 1 (.65 μm).
If the I-Band 2 data is also present in a CREFL file,
then it will be used to spatially sharpen the image.
This band combination is very effective at distinguishing
land/water boundaries as well as burn scars.

To create a Polar2Grid False Color GeoTIFF file, execute
the following command:


.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh crefl gtiff --false-color -f /path/to/my_sdrs/

And just like the true color image, use the following to create a KMZ file:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/gtiff2kmz.sh input_false_color.tif output_false_color.kmz

Further examples of executing the Correct Reflectance Reader 
follow. 

Execution Examples
-----------------------

.. code-block:: bash

    crefl2gtiff.sh -f /data/modis/level1b

    crefl2gtiff.sh --true-color --false-color -f ../l1b/a1.17006.1855.{250m,500m,1000m,geo}.hdf

    crefl2gtiff.sh --true-color --false-color -f ../sdr/SV{I01,M03,M04,M05,M07,M11}_*.h5 ../sdr/GMTCO*.h5 ../sdr/GITCO*.h5

    polar2grid.sh crelf gtiff -f /data/modis/MOD0{21KM,2HKM,2QKM,3}.*.hdf

    crefl2gtiff.sh --false-color -f ../l1b/a1.17006.1855.{250m,500m,1000m,geo}.hdf
  
    polar2grid.sh crefl gtiff -f /imapp/modis/a1.17006.1855.{250m,500m,1000m,geo}.hdf

    crefl2gtiff.sh --true-color -f /data/modis/a1.17006.1855.crefl.250m.hdf /data/modis/a1.17006.1855.crefl.500m.hdf /data/modis/a1.17006.1855.geo.hdf

    polar2grid.sh crefl gtiff --true-color --false-color -f ../crefl/t1.17004.1732.crefl.{250,500,1000}m.hdf ../l1b/MOD03.A2017004.1732.005.2017023210017.hdf

    polar2grid.sh crefl gtiff --true-color -g wgs84_fit_250 --fornav-D 10 -f MYD021KM.A2017004.1732.006.2017023210017.hdf MYD02HKM.A2017004.1732.005.2017023210017.hdf MYD02QKM.A2017004.1732.005.2017023210017.hdf MYD03.A2017004.1732.005.2017023210017.hdf

    polar2grid.sh crefl scmi --grid-coverage=0 -g lcc_conus_1km --sector-id LCC --letters --compress -f /home/data/t1*.hdf 

    polar2grid.sh crefl scmi --sector-id Pacific -g merc_pacific_1km --letters --compress -f /modis/data/MYD*.hdf

    polar2grid.sh crefl scmi --true-color --false-color --sector-id LCC -g lcc_conus_300m --letters -f /viirs/SV*.h5 /viirs/GMTCO*.h5 /viirs/GITCO*.h5
