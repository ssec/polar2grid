Getting Started
===============

All of the tools provided by Polar2Grid can be found in the ``bin`` directory
of the extracted tarball. The majority of the scripts in the software bundle
are wrappers around python software.

The most common use of Polar2Grid is to convert satellite data files in to
gridded image files. This is accomplished through the ``polar2grid.sh``
script. Due to the modular design of Polar2Grid a user only needs
to decide on a :doc:`Reader <readers/index>` and a
:doc:`Writer <writers/index>` and provide them to ``polar2grid.sh``::

    $POLAR2GRID_HOME/bin/polar2grid.sh viirs_sdr gtiff -f <path to files>/<list of files>

Where ``<list of files>`` includes input calibrated data and geolocation
files. Each Reader comes with a logical set of default products to be created,
but this can be configured. If you provide only ``<path to files>`` the
path will be searched for the necessary files to make as many products as
possible. Similarly if processing errors occur Polar2Grid will attempt to
continue processing to make as many products as it can.

For example, executing the following::

    $POLAR2GRID_HOME/bin/polar2grid.sh viirs_sdr gtiff -f /home/data/viirs/sdr

Will create 8-bit GeoTIFF files of all M-Band, I-Band, and Day/Night Band
SDR files it finds in the ``/home/data/viirs/sdr`` directory as long as it
contains the matching geolocation files. If multiple granules are provided
to ``polar2grid.sh`` they will be aggregated together.

Additional command line arguments for the ``polar2grid.sh`` script and
their defaults are described in the related
:doc:`reader <readers/index>` or :doc:`writer <writers/index>` sections.
Options that affect remapping are described in the :doc:`remapping` section.
Additionally all Polar2Grid bash scripts accept a ``-h`` argument to list
all the available command line arguments. Usually readers will share the same
command line options except when it comes to configuring specific products
or "shortcut flags" to request a group of products at once.

For information on other scripts and features provided by Polar2Grid see
the :doc:`utilscripts` or :doc:`misc_recipes` sections or
the various examples through out the :doc:`reader <readers/index>` and
:doc:`writer <writers/index>` sections.

.. note::

    In previous versions of Polar2Grid scripts were named
    ``<reader>2<writer>.sh`` instead of
    ``polar2grid.sh <reader> <writer>``. These legacy scripts will still
    work but the new form of calling is preferred.

Creating True Color as Geotiffs and KML/KMZ
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a true color image you must first have the SDRs for the proper instrument. Traditional
true color images are created using the :doc:`CREFL (Corrected Reflectance) Reader <readers/crefl>`.
See the reader documentation for which instruments are supported at this
time (VIIRS and MODIS at the moment). Even if you want a KMZ, a geotiff must be created first::

    $POLAR2GRID_HOME/bin/crefl2gtiff.sh -f /path/to/my_sdrs/

This will create a series of geotiff files with the ``.tif`` file extension. To create a KMZ file
(a compressed KML) to show in Google Earth or other program use the ``gtiff2kmz.sh`` script provided
in the software bundle::

    $POLAR2GRID_HOME/bin/gtiff2kmz.sh input_true_color.tif output_true_color.kmz

Where the ``input_true_color.tif`` file is one of the files created from the ``crefl2gtiff.sh``
command and ``output_true_color.kmz`` is the name of the KMZ file to create.

For more information see the documentation for the
:doc:`CREFL Reader <readers/crefl>`, the :doc:`Geotiff Writer <writers/gtiff>`, and the
:doc:`True Color Compositor <compositors>`.

Creating False Color as Geotiffs and KML/KMZ
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A false color image is any combination of 3 bands that isn't a true color image, but by default
Polar2Grid uses a default set of bands. See the :doc:`False Color Compositor <compositors>`
for more information on those defaults. To make a false color image geotiff run::

    $POLAR2GRID_HOME/bin/crefl2gtiff.sh false_color --false-color -f /path/to/my_sdrs/

Now while these command arguments may seem redundant there is a good reason for them. The
``--false-color`` portion of the command tells the reader that you want the products used
in a false color image. The ``false_color`` portion says that you actually want to *make*
a false color image product. Without the ``false_color`` part, no RGB image would be created.

Just like for the true color image, use the following to create a KMZ file::

    $POLAR2GRID_HOME/bin/gtiff2kmz.sh input_false_color.tif output_false_color.kmz

Custom Grid Utility
^^^^^^^^^^^^^^^^^^^

The Polar2Grid software bundle comes with a wrapper script for the
:ref:`Custom Grid Utility <util_p2g_grid_helper>` for easily creating Polar2Grid grids over
a certain longitude and latitude. To run it from the software bundle wrapper run::

    $POLAR2GRID_HOME/bin/p2g_grid_helper.sh ...

See the :ref:`script's documentation <util_p2g_grid_helper>` for more information
on how to use this script and the arguments it accepts.
