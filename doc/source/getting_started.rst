|project| Basics
=================

All of the tools provided by |project| can be found in the ``bin`` directory
of the extracted tarball. The majority of the scripts in the software bundle
are bash wrappers around python software.

Basic Usage
-----------

.. ifconfig:: not is_geo2grid

    The most common use of |project| is to convert satellite data files in to
    gridded image files.
    The following command can be used to create GeoTIFF single band images of
    all S-NPP VIIRS imager SDR calibrated data with accompanying geolocation
    files found in ``<path to files>/<list of files>``.

    .. code-block:: bash

        $POLAR2GRID_HOME/bin/polar2grid.sh -r viirs_sdr -w geotiff -f <path to files>/<list of files>

    This script takes advantage of the modular design of |project|;
    a user only needs to decide on a :doc:`Reader <readers/index>` and a
    :doc:`Writer <writers/index>` and provide them to |script_literal|.
    In |project| the ``<path to files>`` will be searched for the necessary
    files to make as many products as possible. Similarly if processing errors
    occur |project| will attempt to continue processing to make as many products
    as it can.

    For example, executing the command above will create 8-bit GeoTIFF files of
    all M-Band, I-Band, and Day/Night Band SDR files it finds in the directory
    as long as it contains the matching geolocation files. If multiple granules
    are provided to |script_literal| they will be aggregated together.
    By default the above command resamples the data to a Google Earth compatible
    Platte Carrée projected grid at ~600m resolution, but this can be changed
    with command line arguments.

.. ifconfig:: is_geo2grid

    The purpose of |project| is to convert satellite data files into
    high quality gridded image files. The main run script is ``geo2grid.sh``
    and requires users to choose an input reader (-r what instrument 
    data would you like to use) and an output writer (-w what output format
    would you like to create). The only other required input is the 
    list of files or a directory pointing to the location of the input 
    files (-f). Each instrument data reader by default will create
    single band output image GeoTIFF files for whatever bands are provided,
    along with true and natural color images. Only one time step
    can be processed with each script execution.
    
    For example, executing the following command above will create 
    8-bit GeoTIFF files of all 16 ABI imager channels, a true 
    color RGB, and natural color RGB in the native resolution of the 
    instrument channel (500m for RGB composites).  This can be 
    customized with command line arguments.

    .. code-block:: bash

        $GEO2GRID_HOME/bin/geo2grid.sh -r abi_l1b -w geotiff -f <path to files>

    This script takes advantage of the modular design of |project|;
    a user only needs to decide on a :doc:`Reader <readers/index>` and a
    :doc:`Writer <writers/index>` and provide them to |script_literal|.

    If processing errors occur |project| will attempt to continue 
    processing to make as many products as it can.

Common Script Options
---------------------

Additional command line arguments for the |script_literal| script and
their defaults are described in the related
:doc:`Reader <readers/index>` or :doc:`Writer <writers/index>` sections.
Options that affect remapping are described in the :doc:`remapping` section.
Additionally all |project| bash scripts accept a ``-h`` argument to list
all the available command line arguments.
Although the available command line arguments may change depending on the
reader and writer specified, there are a set of common arguments that
are always available:

.. ifconfig:: not is_geo2grid

    .. rst-class:: full_width_table

        -h                    Print helpful information.
        --list-products       List all possible product options to use with -p from the given input data.
        -p                    List of products you want to create.
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

        -r 	 	      Instrument input files to read from (choose from abi_l1b, ahi_hsd, and ahi_hrit).
        -w  		      Output format to write to (Currently only option is geotiff).
        -h                    Print helpful information.
        --list-products       List all possible product options to use with -p from the given input data.

        -p                    List of products you want to create.
        -f                    Input files and paths.
        -g <grid_name>        Specify the output grid to use. Default is the native instrument projection.
                              See :doc:`grids` and :doc:`custom_grids` for information on other possible values.
        --cache-dir <dir>     Directory to store resampling intermediate results between executions.
                              Not used with 'native' resampling method.
        --num-workers         Specify number of parallel processing worker threads to use (default: 4)
        --progress            Display a timed progress bar to show processing progress

        --ll-bbox <lonmin latmin lonmax latmax>    Subset input data to the bounding coordinates specified.

        -v                    Print detailed log information.

    Examples:

    .. code-block:: bash

        geo2grid.sh -r abi_l1b -w geotiff --list-products -f <path to files>/<list of files>

        geo2grid.sh -r abi_l1b -w geotiff -p C01 natural_color -v -f <path to files>

        geo2grid.sh -r abi_l1b -w geotiff --ll-bbox -95.0 40.0 -85.0 50.0 -f /abi/OR_ABI-L1b-RadF-*.nc

        geo2grid.sh -r ahi_hsd -w geotiff -p B03 B04 B05 B14 -f /ahi/*FLDK*.DAT

        geo2grid.sh -r ahi_hrit -w geotiff -f /ahi/IMG_DK01*


For information on other scripts and features provided by |project| see
the :doc:`utilscripts` section or the various examples throughout 
the document.

.. _reader_writer_combos:

Reader/Writer Combinations
--------------------------

The tables below provide a summary of the possible combinations of readers and
writers and expectations for the inputs and outputs of |script_literal|.
To access these features provide the "reader" and "writer" names to the
|script_literal| script followed by other script options:

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

        $POLAR2GRID_HOME/bin/polar2grid.sh <reader> <writer> --list-products <options> -f /path/to/files

.. ifconfig:: is_geo2grid

    .. code-block:: bash

        $GEO2GRID_HOME/bin/geo2grid.sh -r <reader> -w <writer> --list-products <options> -f /path/to/files

.. raw:: latex

    \newpage
    \begin{landscape}

.. ifconfig:: not is_geo2grid

    .. include:: summary_table.rst

.. ifconfig:: is_geo2grid

    .. include:: summary_table_geo2grid_readers.rst
    .. include:: summary_table_geo2grid_writers.rst

.. raw:: latex

    \end{landscape}
    \newpage

.. ifconfig:: is_geo2grid

    .. _getting_started_rgb:

    Creating Red Green Blue (RGB) Composite Imagery
    -----------------------------------------------

        The list of supported products includes true and natural color 24-bit
        RGB imagery. The software uses the number of specified CPU threads to
        create high quality reprojections in the lowest latency possible
        thanks to the dask python library. Dask splits data arrays in to
        multiple "chunks" and processes them in parallel. The creation of
        these RGBs includes the following steps, which are performed by
        default with each execution:

        * Check for required spectral bands used in RGB creation among input files.
        * Upsample and sharpen composite bands to the highest spatial resolution (500m).
        * Creation of pseudo "green" band for the ABI instruments.
        * Reflectance adjustment (dividing by cosine of the solar zenith angle).
        * Removal of atmospheric Rayleigh scattering (atmospheric correction).
        * Nonlinear scaling before writing data to disk

        Geo2Grid also supports the creation of other RGBs (this varies depending on
        the instrument), however these files are not produced by default.  The
        recipes for creating these RGBs come from historical EUMETSAT recipes that
        have been adjusted to work with the data being used in |project|.


Creating Your Own Custom Grids
------------------------------

The |project| software bundle comes with a wrapper script for the
:ref:`Custom Grid Utility <util_p2g_grid_helper>` for easily creating |project| grid definitions over
a user determined longitude and latitude region. Once these definitions have
been created, they can be provided to polar2grid.sh. To run the utility script  
from the software bundle wrapper run:

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

        $POLAR2GRID_HOME/bin/p2g_grid_helper.sh ...

.. ifconfig:: is_geo2grid

    .. code-block:: bash

        $GEO2GRID_HOME/bin/p2g_grid_helper.sh ...

See the :ref:`script's documentation <util_p2g_grid_helper>` for more information
on how to use this script and the arguments it accepts.
