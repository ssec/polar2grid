Polar2Grid Basics
=================

All of the tools provided by Polar2Grid can be found in the ``bin`` directory
of the extracted tarball. The majority of the scripts in the software bundle
are wrappers around python software.

Basic Usage
-----------

The most common use of Polar2Grid is to convert satellite data files in to
gridded image files. This is accomplished through the ``polar2grid.sh``
script. Due to the modular design of Polar2Grid a user only needs
to decide on a :doc:`Reader <readers/index>` and a
:doc:`Writer <writers/index>` and provide them to ``polar2grid.sh``:

.. code:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh viirs_sdr gtiff -f <path to files>/<list of files>

where ``<list of files>`` includes input calibrated data and geolocation
files. If you provide only ``<path to files>`` the
path will be searched for the necessary files to make as many products as
possible. Similarly if processing errors occur Polar2Grid will attempt to
continue processing to make as many products as it can.

For example, executing the following:

.. code:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh viirs_sdr gtiff -f /home/data/viirs/sdr

will create an 8-bit GeoTIFF files of all M-Band, I-Band, and Day/Night Band
SDR files it finds in the ``/home/data/viirs/sdr`` directory as long as it
contains the matching geolocation files. If multiple granules are provided
to ``polar2grid.sh`` they will be aggregated together.
By default the above command resamples the data to a Google Earth compatible
Platte Carrée projected grid at ~600m resolution, but this can be changed
with command line arguments.

Common Script Options
---------------------

Additional command line arguments for the ``polar2grid.sh`` script and
their defaults are described in the related
:doc:`reader <readers/index>` or :doc:`writer <writers/index>` sections.
Options that affect remapping are described in the :doc:`remapping` section.
Additionally all Polar2Grid bash scripts accept a ``-h`` argument to list
all the available command line arguments.
Although the available command line arguments may change depending on the
reader and writer specified, there are a set of common arguments that
are always available:

.. csv-table:: Common Command Line Options

    "-h", "Print detailed helpful information."
    "--list-products", "List all possible product options to use with -p from the given input data."
    "-p", "List of products to create."
    "-f", "Input files and paths."
    "--grid-coverage", "Fraction of grid that must be covered by valid data. Default is 0.1."
    "-g <grid_name>", "Specify the output grid to use. Default is the Platte Carrée projection, also
 known as the wgs84 coordinate system. See :doc:`grids` and :doc:`custom_grids` for information on
 possible values."
    "--debug", "Don’t remove intermediate files upon completion."
    "-v", "Print detailed log information."

For information on other scripts and features provided by Polar2Grid see
the :doc:`utilscripts` or :doc:`misc_recipes` sections or
the various examples through out the :doc:`reader <readers/index>` and
:doc:`writer <writers/index>` sections.

Reader/Writer Combinations
--------------------------

The table below is a summary of the possible combinations of readers and
writers and expectations for the inputs and outputs of ``polar2grid.sh``.
To access these features provide the "reader" and "writer" names to the
``polar2grid.sh`` script followed by other script options:

.. code:: bash

    $POLAR2GRID_HOME/bin/polar2grid.sh <reader> <writer> <options> -f /path/to/files

In previous versions of Polar2Grid scripts were all named
``<reader>2<writer>.sh`` instead of
``polar2grid.sh <reader> <writer>``. These legacy scripts are still available
and still work but the new form of calling is preferred. For example:

.. code:: bash

    $POLAR2GRID_HOME/bin/avhrr2awips.sh <options> -f /path/to/files

.. include:: summary_table.rst

Custom Grid Utility
^^^^^^^^^^^^^^^^^^^

The Polar2Grid software bundle comes with a wrapper script for the
:ref:`Custom Grid Utility <util_p2g_grid_helper>` for easily creating Polar2Grid grids over
a certain longitude and latitude. To run it from the software bundle wrapper run::

    $POLAR2GRID_HOME/bin/p2g_grid_helper.sh ...

See the :ref:`script's documentation <util_p2g_grid_helper>` for more information
on how to use this script and the arguments it accepts.
