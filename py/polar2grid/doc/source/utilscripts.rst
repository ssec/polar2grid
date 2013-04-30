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

Example::

    $POLAR2GRID_HOME/bin/p2g_proj.sh "+proj=lcc +datum=NAD83 +ellps=GRS80 +lat_1=25 +lon_0=-95" -105.23 38.5
    # Will result in:
    -878781.238459 4482504.91307

.. _util_p2g_grid_helper:

Grid Config. Helper
-------------------

:Bundle Script: p2g_grid_helper.sh
:Python Script: :py:mod:`polar2grid.grids.config_helper`

This script is meant to help those unfamiliar with PROJ.4 and projections
in general. By providing a few grid parameters this script will provide a
grid configuration line that can be added to a user's custom grid
configuration. Based on a center longitude and latitude, the script will
choose an appropriate projection.

Usage::

    $POLAR2GRID_HOME/bin/p2g_grid_helper.sh [-h] [-p PROJ_STR]
                            grid_name center_longitude center_latitude
                            pixel_size_x pixel_size_y grid_width grid_height

    Print out valid grid configuration line given grid parameters. A default
    projection will be used based on the location of the grid. A different
    projection can be specified if desired. The default projection is referenced
    at the center lon/lat provided by the user.

    positional arguments:
      grid_name         Unique grid name
      center_longitude  Decimal longitude value for center of grid (-180 to 180)
      center_latitude   Decimal latitude value for center of grid (-90 to 90)
      pixel_size_x      Size of each pixel in the X direction in grid units,
                        usually meters.
      pixel_size_y      Size of each pixel in the Y direction in grid units,
                        meters by default.
      grid_width        Grid width in number of pixels
      grid_height       Grid height in number of pixels

    optional arguments:
      -h, --help        show this help message and exit
      -p PROJ_STR       PROJ.4 projection string to override the default

Example::

    $POLAR2GRID_HOME/bin/p2g_grid_helper.sh my_grid_name -150.1 56.3 250 -250 1000 1000
    # Will result in:
    my_grid_name, +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=56.300 +lat_1=56.300 +lon_0=-150.100 +units=m +no_defs, 1000, 1000, 250.000, -250.000, -125000.000, 125000.000

The above example creates a grid named 'my_grid_name' at a 250m resolution,
1000 pixels wide and heigh, and centered at -150.1 degrees longitude
and 56.3 degrees latitude. The projection is a lambert conic conformal
projection chosen based on the center longitude and latitude.

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

