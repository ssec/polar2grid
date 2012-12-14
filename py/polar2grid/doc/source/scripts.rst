Glue Scripts
============

polar2grid uses specialized scripts to handle the high level processing of
polar-orbiting satellite data to product generation.  These scripts are
programmed in python and called glue scripts.  Each glue script has
a "companion" script that is located in the polar2grid software bundle's
``/bin`` directory.  These "companion" scripts are used to setup the
environment needed by the python scripts, enter defaults into the python
scripts, and ease the installation/use process for the user.  The "companion"
scripts are callable (once proper installation steps have been taken) by the
name of the script.

.. important::

    Glue scripts do not delete files created by previous glue script
    calls and may fail if those files exist during processing. The two common
    methods for dealing with this are the ``-R`` command line option
    described below or creating a working directory for each new call to a
    glue script and removing it after copying or using the product files.

.. note::

    If you are using the basic software bundle method of installation, you MUST use
    the companion script to properly run polar2grid processing.

Generic Glue Script Options
---------------------------

The following command line options are available for all glue scripts
regardless of the frontend or backend.

.. cmdoption:: -h
               --help

    Print usage and command line option information.

.. cmdoption:: -v
               --verbose

    Print detailed log messages. Increases in level from
    ERROR -> WARNING -> INFO -> DEBUG. The default for companion scripts
    is INFO and for the python script the default is ERROR. To increase the
    level of detail add more ``-v`` to the command line.

.. cmdoption:: -d <data-directory>

    Specify the directory to search for data files. Glue scripts will use
    every data file in that directory that they know how to handle. For
    example, a glue script using the VIIRS frontend will use all SVM, SVI,
    and SVDNB files located in the directory specified. This is the
    alternative to the ``-f`` option.

    .. versionchanged:: 1.0.0
        The -d flag replaced the positional argument for the data directory.

.. cmdoption:: -f <data-file> [<data-file> ...]

    Specify a space separated list of data files to process. This option is
    useful for specifying only certain bands or time ranges of data to
    process. Using shell path expansion to accomplish this type of filtering
    with VIIRS data files can look something like this::
    
        -f /path/to/data/SVM{01,02,12,15}*t18[1,2,3]*.h5
    
    This path would pass only the VIIRS M bands 01, 02, 12, 15 between the
    time range 18:10:00Z - 18:39:59Z.  The ``-f`` flag is the alternative to
    the ``-d`` option.

.. cmdoption:: -R

    This is a special flag that will remove conflicting files from the current
    working directory.  Conflicting files are files that were created by a
    previous call to a glue script and may cause the glue script being called
    to fail.  Specifying this flag on the command line will **NOT** continue
    on processing after conflicting files have been removed.

viirs2awips
-----------


:Python Script: ``polar2grid.viirs2awips``
:Comp. Script: ``viirs2awips.sh``

This script is used to process
:ref:`VIIRS imager data <frontend_viirs>`
into
:ref:`AWIPS compatible NetCDF <backend_awips_netcdf>`
files.  It can be run using the following command::

    $POLAR2GRID_HOME/bin/viirs2awips.sh -d /path/to/data/

or to force the gpd
:doc:`grid <grids>` that will be mapped to::

    $POLAR2GRID_HOME/bin/viirs2awips.sh -g 203 -d /path/to/data/

for more options run::

    $POLAR2GRID_HOME/bin/viirs2awips.sh --help

`viirs2awips` does not have any special restrictions on the bands that can
be provided.  However, `viirs2awips` creates the
:ref:`SSEC Fog pseudoband <pseudo_viirs_ifog>` if the I05 and I04 bands are
provided.  This glue script will also scale the DNB data using the method
described :ref:`here <prescale_viirs_dnb>`.

See the :ref:`backend_awips_netcdf` for more
information on what scaling it does to prepare the data for the
AWIPS-compatible NetCDF file.

.. cmdoption:: -g <grid_name> [<grid_name> ...]

    Specify the gpd grids to be gridded to. Specifying this option will skip
    the grid determination step. More than one grid can be specified at a
    time.

viirs2gtiff
-----------

:Python Script: ``polar2grid.viirs2gtiff``
:Comp. Script: ``viirs2gtiff.sh``

This is used to process
:ref:`VIIRS imager data <frontend_viirs>`
into
:ref:`Geotiff images <backend_geotiff>`.
It can be run using the following command::

    $POLAR2GRID_HOME/bin/viirs2gtiff.sh -d /path/to/data

or for a specific set of files and to force the PROJ.4
:doc:`grid <grids>`::

    $POLAR2GRID_HOME/bin/viirs2gtiff.sh -g lcc_fit -f /path/to/files*.h5

for more options run::

    $POLAR2GRID_HOME/bin/viirs2gtiff.sh --help

.. versionadded:: 1.0.0

viirs2binary
------------

:Python Script: ``polar2grid.viirs2binary``
:Comp. Script: ``viirs2binary.sh``

This is used to process
:ref:`VIIRS imager data <frontend_viirs>`
into
:ref:`binary files <backend_binary>`.  It can be run using the following
command::

    $POLAR2GRID_HOME/bin/viirs2binary.sh -d /path/to/data

or for a specific set of files and to force the PROJ.4
:doc:`grid <grids>`::

    $POLAR2GRID_HOME/bin/viirs2binary.sh -g wgs84_fit -f /path/to/files*.h5

for more options run::

    $POLAR2GRID_HOME/bin/viirs2binary.sh --help

..versionadded:: 1.0.0

