Utility Scripts
===============

The following are scripts that can be used to help analyze and/or verify
polar2grid operations.

.. _util_p2g_grid_helper:

Grid Config. Helper
-------------------

.. argparse::
    :module: polar2grid.grids.config_helper
    :func: get_parser
    :prog: p2g_grid_helper.sh


Example::

    $POLAR2GRID_HOME/bin/p2g_grid_helper.sh my_grid_name -150.1 56.3 250 -250 1000 1000
    # Will result in:
    my_grid_name, +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=56.300 +lat_1=56.300 +lon_0=-150.100 +units=m +no_defs, 1000, 1000, 250.000, -250.000, -125000.000, 125000.000

The above example creates a grid named 'my_grid_name' at a 250m resolution,
1000 pixels wide and heigh, and centered at -150.1 degrees longitude
and 56.3 degrees latitude. The projection is a lambert conic conformal
projection chosen based on the center longitude and latitude.

Add Coastlines
--------------

.. argparse::
    :module: polar2grid.add_coastlines
    :func: get_parser
    :prog: add_coastlines.sh

Add Colormap
------------

.. argparse::
    :module: polar2grid.add_colormap
    :func: get_parser
    :prog: add_colormap.sh

.. _util_p2g_proj:

Python Proj
-----------

.. argparse::
    :module: polar2grid.core.proj
    :func: get_parser
    :prog: p2g_proj.sh

Example::

    $POLAR2GRID_HOME/bin/p2g_proj.sh "+proj=lcc +datum=NAD83 +ellps=GRS80 +lat_1=25 +lon_0=-95" -105.23 38.5
    # Will result in:
    -878781.238459 4482504.91307

Plot AWIPS NC Data
------------------

.. argparse::
    :module: polar2grid.plot_ncdata
    :func: get_parser
    :prog: plot_ncdata.sh

