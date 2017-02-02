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

Example 1 - Create True Color Geotiffs and KML/KMZ
--------------------------------------------------

To create a true color image you must first have the SDRs for the proper
instrument. At this time VIIRS and MODIS are supported by this reader. Even
if you want a KMZ, a geotiff must be created first:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh crefl gtiff -f /path/to/my_sdrs/

This will create a series of geotiff files with the ``.tif`` file extension. To create a KMZ file
(a compressed KML) to show in Google Earth or other program use the ``gtiff2kmz.sh`` script provided
in the software bundle:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/gtiff2kmz.sh input_true_color.tif output_true_color.kmz

Where the ``input_true_color.tif`` file is one of the files created from the ``crefl2gtiff.sh``
command and ``output_true_color.kmz`` is the name of the KMZ file to create.

For more information see the documentation for the
the :doc:`Geotiff Writer <../writers/gtiff>` and :ref:`util_gtiff2kmz`
documentation.

Example 2 - Creating False Color Geotiffs and KML/KMZ
-----------------------------------------------------

A false color image is any combination of 3 bands that isn't a true color image, but by default
Polar2Grid uses a default set of bands. The procedure is almost the same to
how the true color image was made:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh crefl gtiff --false-color -f /path/to/my_sdrs/

And just like for the true color image, use the following to create a KMZ file:

.. code-block:: bash

    $POLAR2GRID_HOME/bin/gtiff2kmz.sh input_false_color.tif output_false_color.kmz


More Execution Examples:

.. code-block:: bash

    crefl2gtiff.sh -f /data/modis/level1b

    crefl2gtiff.sh --true-color --false-color -f ../l1b/a1.17006.1855.{250m,500m,1000m,geo}.hdf

    crefl2gtiff.sh -f /data/modis/MOD0{21KM,2HKM,2QKM,3}.*.hdf

    crefl2gtiff.sh --false-color -f ../l1b/a1.17006.1855.{250m,500m,1000m,geo}.hdf
  
    polar2grid.sh crefl gtiff -f /imapp/modis/a1.17006.1855.{250m,500m,1000m,geo}.hdf

    crefl2gtiff.sh --true-color -f /data/modis/a1.17006.1855.crefl.250m.hdf /data/modis/a1.17006.1855.crefl.500m.hdf /data/modis/a1.17006.1855.geo.hdf

    polar2grid.sh crefl gtiff --true-color --false-color -f ../crefl/t1.17004.1732.crefl.{250,500,1000}m.hdf ../l1b/MOD03.A2017004.1732.005.2017023210017.hdf

        

       

