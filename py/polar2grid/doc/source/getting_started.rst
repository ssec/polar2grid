Getting Started
===============

Getting started with Polar2Grid can be simple once you've decided what you actually want to do.
Polar2Grid comes with a lot of options and there is a lot that can be customized with little work.
Each section below describes the basic operations that a user should take to achieve their processing
goals. The information is split in to 3 sections:

 - :ref:`getting_started_bundle`
 - :ref:`getting_started_cli`
 - :ref:`getting_started_library`

.. _getting_started_bundle:

For CSPP Software Bundle Users
------------------------------

Users of the CSPP Software Bundle can find all of the tools they may want
to use in the ``bin`` directory of the extracted tarball. As mentioned in
the :doc:`installation instructions <installation>`, the following line can
be added to your ``.bash_profile`` to simplify calling Polar2Grid scripts.
This line allows you to remove the ``$POLAR2GRID_HOME/bin/`` portion of the
commands mentioned elsewhere in the documentation.

::

    export PATH=$POLAR2GRID_HOME/bin:$PATH

The majority of the scripts in the software bundle are wrappers around python command line tools.
Due to the modular design of Polar2Grid a user only needs to decide on a
:doc:`Frontend <frontends/index>` and a :doc:`Backend <backends/index>` to find the script to run.
For example, to convert VIIRS SDR files to Geotiffs a user should run the following::

    $POLAR2GRID_HOME/bin/viirs2gtiff.sh -f /path/to/my_sdrs/

This method of finding and calling scripts applies to all basic Polar2Grid features. Each Frontend
comes with a logical set of default products to be created. If it can't find all the necessary data
then it will continue on with what could be created.

To see a full
list of the available command line arguments provide the ``-h`` argument to a script. See the
:doc:`frontends documentation <frontends/index>` for available frontends and
:doc:`backends documentation <backends/index>` for available backends. Some of the more advanced features
provided by Polar2Grid are decribed in the below sections. It is recommended that users searching
for a feature not explained on this page look at the rest of the Polar2Grid documentation. For users
looking to make their own custom RGB products, see the :doc:`Compositor's documentation <compositors/index>`.

Creating True Color as Geotiffs and KML/KMZ
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a true color image you must first have the SDRs for the proper instrument. Traditional
true color images are created using the :doc:`CREFL (Corrected Reflectance) Frontend <frontends/crefl>`.
See the frontend documentation for which instruments are supported at this
time (VIIRS and MODIS at the moment). Even if you want a KMZ, a geotiff must be created first::

    $POLAR2GRID_HOME/bin/crefl2gtiff.sh -f /path/to/my_sdrs/

This will create a series of geotiff files with the ``.tif`` file extension. To create a KMZ file
(a compressed KML) to show in Google Earth or other program use the ``gtiff2kmz.sh`` script provided
in the software bundle::

    $POLAR2GRID_HOME/bin/gtiff2kmz.sh input_true_color.tif output_true_color.kmz

Where the ``input_true_color.tif`` file is one of the files created from the ``crefl2gtiff.sh``
command and ``output_true_color.kmz`` is the name of the KMZ file to create.

For more information see the documentation for the
:doc:`CREFL Frontend <frontends/crefl>`, the :doc:`Geotiff Backend <backends/gtiff>`, and the
:doc:`True Color Compositor <compositors/true_color>`.

Creating False Color as Geotiffs and KML/KMZ
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A false color image is any combination of 3 bands that isn't a true color image, but by default
Polar2Grid uses a default set of bands. See the :doc:`False Color Compositor <compositors/false_color>`
for more information on those defaults. To make a false color image geotiff run::

    $POLAR2GRID_HOME/bin/crefl2gtiff.sh false_color --false-color -f /path/to/my_sdrs/

Now while these command arguments may seem redundant there is a good reason for them. The
``--false-color`` portion of the command tells the frontend that you want the products used
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

.. _getting_started_cli:

For Command Line Tool Users
---------------------------

TODO

.. _getting_started_library:

For Python Library Users
------------------------

TODO