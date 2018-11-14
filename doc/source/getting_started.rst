|project| Basics
=================

All of the tools provided by |project| can be found in the ``bin`` directory
of the extracted tarball. The majority of the scripts in the software bundle
are wrappers around python software.

Basic Usage
-----------

.. ifconfig:: not is_geo2grid

    The most common use of |project| is to convert satellite data files in to
    gridded image files.
    The following command can be used to create GeoTIFF single band images of
    all S-NPP VIIRS imager SDR calibrated data with accompanying geolocation
    files found in ``<path to files>/<list of files>``.

    .. code-block:: bash

        $POLAR2GRID_HOME/bin/polar2grid.sh viirs_sdr gtiff -f <path to files>/<list of files>

.. ifconfig:: is_geo2grid

    The most common use of |project| is to convert satellite data files in to
    gridded image files.
    The following command can be used to create 8-bit GeoTIFF single band
    images of all 16 ABI imager L1B calibrated channels, a true color RGB,
    and natural color RGB, based on the files found in
    ``<path to files>/<list of files>``.

    .. code-block:: bash

        $GEO2GRID_HOME/bin/geo2grid.sh -r abi_l1b -w geotiff -f <path to files>/<list of files>

This script takes advantage of the modular design of |project|;
a user only needs to decide on a :doc:`Reader <readers/index>` and a
:doc:`Writer <writers/index>` and provide them to |script_literal|.

In |project| the ``<path to files>`` will be searched for the necessary
files to make as many products as possible. Similarly if processing errors
occur |project| will attempt to continue processing to make as many products
as it can.

.. ifconfig:: not is_geo2grid

    For example, executing the command above will create 8-bit GeoTIFF files of
    all M-Band, I-Band, and Day/Night Band SDR files it finds in the directory
    as long as it contains the matching geolocation files. If multiple granules
    are provided to |script_literal| they will be aggregated together.
    By default the above command resamples the data to a Google Earth compatible
    Platte Carrée projected grid at ~600m resolution, but this can be changed
    with command line arguments.

.. ifconfig:: is_geo2grid

    For example, executing the command above will create 8-bit GeoTIFF files of
    all 16 ABI imager channels, a true color RGB, and natural color RGB in the
    native resolution of the instrument channel (500m for most RGB composites).
    This can be customized with command line arguments.

Common Script Options
---------------------

Additional command line arguments for the |script_literal| script and
their defaults are described in the related
:doc:`reader <readers/index>` or :doc:`writer <writers/index>` sections.
Options that affect remapping are described in the :doc:`remapping` section.
Additionally all |project| bash scripts accept a ``-h`` argument to list
all the available command line arguments.
Although the available command line arguments may change depending on the
reader and writer specified, there are a set of common arguments that
are always available:

.. ifconfig:: not is_geo2grid

    .. rst-class:: full_width_table

        -h                    Print detailed helpful information.
        --list-products       List all possible product options to use with -p from the given input data.
        -p                    List of products to create.
        -f                    Input files and paths.
        --grid-coverage       Fraction of grid that must be covered by valid data. Default is 0.1.
        -g <grid_name>        Specify the output grid to use. Default is the Platte Carrée projection, also
                              known as the wgs84 coordinate system. See :doc:`grids` and :doc:`custom_grids`
                              for information on possible values.
        -v                    Print detailed log information.

    Examples:

    .. code-block:: bash

        polar2grid.sh modis gtiff --list-products -f <path to files>/<list of files>

        polar2grid.sh viirs gtiff -p i01 adaptive_dnb -g polar_alaska_300 --grid-coverage=.25 -v -f <path to files>

.. ifconfig:: is_geo2grid

    .. rst-class:: full_width_table

        -h                    Print detailed helpful information.
        --list-products       List all possible product options to use with -p from the given input data.
        -p                    List of products to create.
        -f                    Input files and paths.
        -g <grid_name>        Specify the output grid to use. Default is the native instrument projection.
                              See :doc:`grids` and :doc:`custom_grids` for information other possible values.
        -v                    Print detailed log information.

    Examples:

    .. code-block:: bash

        geo2grid.sh -r abi_l1b -w geotiff --list-products -f <path to files>/<list of files>

        geo2grid.sh -r abi_l1b -w geotiff -p C01 natural_color -v -f <path to files>


For information on other scripts and features provided by |project| see
the :doc:`utilscripts` or :doc:`misc_recipes` sections or
the various examples through out the :doc:`reader <readers/index>` and
:doc:`writer <writers/index>` sections.

.. _reader_writer_combos:

Reader/Writer Combinations
--------------------------

The table below is a summary of the possible combinations of readers and
writers and expectations for the inputs and outputs of |script_literal|.
To access these features provide the "reader" and "writer" names to the
|script_literal| script followed by other script options:

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

        $POLAR2GRID_HOME/bin/polar2grid.sh <reader> <writer> --list-products <options> -f /path/to/files

.. ifconfig:: is_geo2grid

    .. code-block:: bash

        $POLAR2GRID_HOME/bin/geo2grid.sh -r <reader> -w <writer> --list-products <options> -f /path/to/files

.. raw:: latex

    \newpage
    \begin{landscape}

.. tabularcolumns:: |L|L|L|l|l|l|

.. ifconfig:: not is_geo2grid

    .. include:: summary_table.rst

.. ifconfig:: is_geo2grid

    .. include:: summary_table_geo2grid.rst

.. raw:: latex

    \end{landscape}
    \newpage

Creating Your Own Custom Grids
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The |project| software bundle comes with a wrapper script for the
:ref:`Custom Grid Utility <util_p2g_grid_helper>` for easily creating |project| grids over
a user determined longitude and latitude region. To run it from the software bundle wrapper run:

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

        $POLAR2GRID_HOME/bin/p2g_grid_helper.sh ...

.. ifconfig:: is_geo2grid

    .. code-block:: bash

        $GEO2GRID_HOME/bin/p2g_grid_helper.sh ...

See the :ref:`script's documentation <util_p2g_grid_helper>` for more information
on how to use this script and the arguments it accepts.
