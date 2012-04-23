Scripts
=======

polar2grid uses specialized scripts to handle the high level processing of
polar-orbiting satellite data to product generation.  Each script has
a "companion" script that is located in the polar2grid software bundle's
``/bin`` directory.  These "companion" scripts are used to setup the
environment needed by the python scripts, enter defaults into the python
scripts, and ease the installation/use process of the user.  The "companion"
scripts are callable (once proper installation steps have been taken) by the
name of the script.

.. note::

    If you are using the basic software bundle method of installation, you MUST use
    the companion script to properly run polar2grid processing.

viirs2awips
-----------

:Python Script: ``polar2grid.viirs2awips``
:Comp. Script: ``viirs2awips.sh``

This script is used to process VIIRS imager data into AWIPS compatible NetCDF
files.  It can be run using the following command:

    ``viirs2awips.sh /path/to/data/``

or to force the grid that will be mapped too:

    ``viirs2awips.sh -g 203 /path/to/data/``

viirs2awips follows the basic chain sequence of:

    1. Swath Extraction
    2. Prescaling
    3. Grid Determination (if not forced)
    4. Remapping
    5. AWIPS NetCDF Backend

The prescaling step only scales the DNB data to a 0-1 range using histogram
equalization.  It performs different equalization depending on if the data
is determined to be at daytime, nighttime, or in between.

The grid determination for viirs2awips uses a bounding box algorithm with
AWIPS grids' boxes determined from outer most latitudes and longitudes.

See the :ref:`awips_netcdf_backend` for more
information on what scaling it does to prepare the data for the
AWIPS-compatible NetCDF file.

