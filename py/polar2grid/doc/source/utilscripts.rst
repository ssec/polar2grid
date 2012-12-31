Utility Scripts
===============

.. include:: global.rst

The following are scripts that can be used to help analyze and/or verify
polar2grid operations.

Plot AWIPS NC Data
------------------

:Bundle Script: plot_ncdata.sh
:Python Script: polar2grid.plot_ncdata

This script will read a series of NetCDF3 files created using the AWIPS
backend and plot the data on a b/w color scale.  It searches for any NetCDF
files with the prefix ``SSEC_AWIPS_``.  It has the following usage syntax::

    $POLAR2GRID_HOME/bin/plot_ncdata.sh [options] [ base directory | '.' ]

    Options:
      -h, --help      show this help message and exit
      --vmin=VMIN     Specify minimum brightness value. Defaults to minimum value
                      of data.
      --vmax=VMAX     Specify maximum brightness value. Defaults to maximum value
                      of data.
      --pat=BASE_PAT  Specify the glob pattern of NetCDF files to look for.
                      Defaults to 'SSEC_AWIPS_*'

Where ``base directory`` is an optional parameter, specifying the location
of all the NetCDF files to plot, defaulting to the current directory.

