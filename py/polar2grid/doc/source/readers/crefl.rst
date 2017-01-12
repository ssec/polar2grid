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

