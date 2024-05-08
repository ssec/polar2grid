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
    As an example, the following command can be used to create GeoTIFF single
    band images of all S-NPP VIIRS imager SDR calibrated data with accompanying
    geolocation files found in ``<path to files>/<list of files>``.

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
    with command line arguments. The GeoTIFF contains 2 bands, including an
    Alpha band.

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

    For example, executing the following command will create
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

        -r                    Instrument input files to read from.
        -w                    Output format to write to.
        -h                    Print helpful information.
        --list-products       List all possible product options to use with -p from the given input data and exit.
        --list-products-all   List available polar2grid products options and custom/Satpy products and exit.
        -p                    List of products you want to create.
        -f                    Input files and paths.
        --grid-coverage       Fraction of grid that must be covered by valid data. Default is 0.1.
        -g <grid_name>        Specify the output grid to use. Default is the Platte Carrée projection, also
                              known as the wgs84 coordinate system. See :doc:`grids` and :doc:`custom_grids`
                              for information on possible values.
        --num-workers num_workers   Specify number of worker threads to use (Default: 4).
        --progress            Show processing progress bar (Not recommended for logged output).
        -v                    Print detailed log information.

    Examples:

    .. code-block:: bash

        polar2grid.sh -r viirs_sdr -w geotiff -p i01 dynamic_dnb -g polar_alaska_300 --grid-coverage=.25 -v -f <path to files>

        polar2grid.sh -r modis_l1b -w geotiff --list-products -f <path to files>/<list of files>

.. ifconfig:: is_geo2grid

    .. rst-class:: full_width_table

        -r 	 	      Instrument input files to read from.
        -w  		      Output format to write to (Currently only option is geotiff).
        -h                    Print helpful information.
        --list-products       List all possible geo2grid product options to use with -p from the given input data and exit.
        --list-products-all   List available geo2grid products options and custom/Satpy products and exit.
        -p                    List of products you want to create.
        -f                    Input files and paths.
        --grid-coverage       Fraction of grid that must be covered by valid data. Default is 0.1.
        -g <grid_name>        Specify the output grid to use. Default is the native instrument projection.
                              See :doc:`grids` and :doc:`custom_grids` for information on other possible values.
        --cache-dir <dir>     Directory to store resampling intermediate results between executions.
                              Not used with 'native' resampling method.
        --num-workers num_workers   Specify number of worker threads to use (Default: 4).
        --progress            Show processing progress bar (Not recommended for logged output).

        --ll-bbox <lonmin latmin lonmax latmax>    Subset input data to the bounding coordinates specified.
        -v                    Print detailed log information.

    Examples:

    .. code-block:: bash

        geo2grid.sh -r abi_l1b -w geotiff --list-products -f <path to files>/<list of files>

        geo2grid.sh -r abi_l1b -w geotiff -p C01 natural_color -v -f <path to files>

        geo2grid.sh -r abi_l1b -w geotiff --ll-bbox -95.0 40.0 -85.0 50.0 -f /abi/OR_ABI-L1b-RadF-*.nc

        geo2grid.sh -r ahi_hsd -w geotiff -p B03 B04 B05 B14 -f /ahi/*FLDK*.DAT

        geo2grid.sh -r ahi_hrit -w geotiff -f /ahi/IMG_DK01*

        geo2grid.sh -r ami_l1b -w geotiff -p IR112 VI006 --num-workers 12 -f /ami/gk2a_ami_l31b*.nc

        geo2grid.sh -r fci_l1c_nc -w geotiff -p ir_38 true_color -f /fci/MTG-FCI-L1C/*_N_JLS_C_0072*

        geo2grid.sh -r agri_fy4a_l1 -w geotiff -p C07 natural_color --progress -f /fy4a/FY4A-_AGRI--*.HDF

        geo2grid.sh -r agri_fy4b_l1 -w geotiff -p C01 C02 C03 -f FY4B-_AGRI--_N_DISK_1330E_L1*_V0001.HDF

        geo2grid.sh -r abi_l2_nc -w geotiff -f /cloud_products/CG_ABI-L2-ACH?C-M6_G16*.nc

        geo2grid.sh -r glm_l2 -w geotiff -p flash_extent_density -f CG_GLM-L2-GLMF-M3_G18*.nc

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

        $POLAR2GRID_HOME/bin/polar2grid.sh -r <reader> -w <writer> --list-products <options> -f /path/to/files

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
        these two RGBs includes the following steps, which are performed by
        default with each execution:

        * Check for required spectral bands used in RGB creation among input files.
        * Upsample and sharpen composite bands to the highest spatial resolution.
        * Creation of pseudo "green" band if necessary (for instance ABI).
        * Reflectance adjustment (dividing by cosine of the solar zenith angle).
        * Removal of atmospheric Rayleigh scattering (atmospheric correction).
        * Nonlinear scaling before writing data to disk.

        Geo2Grid also supports the creation of other RGBs (this varies depending on
        the instrument), however these files are not produced by default.  The
        recipes for creating these RGBs come from recipes that have been
	decided upon by different satellite governing Agencies. For more
	information on RGB recipes, please see `this site
        <https://rammb2.cira.colostate.edu/training/visit/quick_reference/#tab17>`_.
        Please `Contact Us <http://cimss.ssec.wisc.edu/contact-form/index.php?name=CSPP%20Geo%20Questions>`__
        if you have any specific questions regarding RGB creation.


Creating Your Own Custom Grids
------------------------------

The |project| software bundle comes with a script for
:ref:`Custom Grid Utility <util_p2g_grid_helper>` that allows users to easily create |project|
custom grid definitions over a user determined longitude and latitude region. Once these
definitions have been created, they can be provided to |project|. To run the utility script
from the software bundle wrapper run:

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

        $POLAR2GRID_HOME/bin/p2g_grid_helper.sh ...

.. ifconfig:: is_geo2grid

    .. code-block:: bash

        $GEO2GRID_HOME/bin/p2g_grid_helper.sh ...

See the :ref:`script's documentation <util_p2g_grid_helper>` for more information
on how to use this script and the arguments it accepts.
