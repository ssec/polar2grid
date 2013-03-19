Utility Scripts
===============

The following are scripts that can be used to help analyze and/or verify
polar2grid operations.

.. _util_p2g_proj:

Python Proj
-----------

:Bundle Script: p2g_proj.sh
:Python Script: :py:mod:`polar2grid.p2g_proj`

This script is a very simple wrapper around the pyproj library. It is
similiar to the `proj` binary provided by the PROJ.4 C library, except
this script handles `latlong` projections being converted to radians.

Usage::

    $POLAR2GRID_HOME/bin/p2g_proj.sh [-h] [-i] proj4_str lon_point lat_point

    Convert lon/lat points to X/Y values

    positional arguments:
      proj4_str      PROJ.4 projection string (in quotes)
      lon_point      Longitude of the point to be converted (single value only)
      lat_point      Latitude of the point to be converted (single value only)

    optional arguments:
      -h, --help     show this help message and exit
      -i, --inverse  Convert X/Y values to lon/lat

Plot AWIPS NC Data
------------------

:Bundle Script: plot_ncdata.sh
:Python Script: :py:mod:`polar2grid.plot_ncdata`

This script will read a series of NetCDF3 files created using the AWIPS
backend and plot the data on a b/w color scale.  It searches for any NetCDF
files with the prefix ``SSEC_AWIPS_``.

Usage::

    $POLAR2GRID_HOME/bin/plot_ncdata.sh [options] [ base directory | '.' ]

    Options:
      -h, --help      show this help message and exit
      --vmin=VMIN     Specify minimum brightness value. Defaults to minimum value
                      of data.
      --vmax=VMAX     Specify maximum brightness value. Defaults to maximum value
                      of data.
      --pat=BASE_PAT  Specify the glob pattern of NetCDF files to look for.
                      Defaults to 'SSEC_AWIPS_*'
      --dpi=DPI       Specify the dpi for the resulting figure, higher dpi will
                      result in larger figures and longer run times

Where ``base directory`` is an optional parameter, specifying the location
of all the NetCDF files to plot, defaulting to the current directory.

Plot Binary Data
----------------

:Bundle Script: N/A
:Python Script: :py:mod:`polar2grid.plot_binary`

This script will read one or more binary files fitting the flat binary file
naming convention and plot the data with a bone color scale. It can search
for files with any prefix via the ``-p`` flag, but will default to
``result_*.real4.*.*`` if no binary files are specified.

Usage::

    python -m plot_binary.py [-h] [-f FILL_VALUE] [-p PATTERN]
                             [binary_files [binary_files ...]]

    positional arguments:
      binary_files   list of flat binary files to be plotted in the current
                     directory

    optional arguments:
        -h, --help     show this help message and exit
        -f FILL_VALUE  Specify the fill_value of the input file(s)
        -p PATTERN     filename pattern to search the current directory for

