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

.. note::

    If you are using the basic software bundle method of installation, you MUST use
    the companion script to properly run polar2grid processing.

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

.. versionchanged:: 1.0.0
    The -d flag replaced the positional argument for the data directory.

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
:ref:`binary files <backend_binary>``.  It can be run using the following
command::

    $POLAR2GRID_HOME/bin/viirs2binary.sh -d /path/to/data

or for a specific set of files and to force the PROJ.4
:doc:`grid <grids>`::

    $POLAR2GRID_HOME/bin/viirs2binary.sh -g wgs84_fit -f /path/to/files*.h5

for more options run::

    $POLAR2GRID_HOME/bin/viirs2binary.sh --help

..versionadded:: 1.0.0

