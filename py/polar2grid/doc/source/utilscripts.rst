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

.. _util_add_coastlines:

Add Coastlines
--------------

.. argparse::
    :module: polar2grid.add_coastlines
    :func: get_parser
    :prog: add_coastlines.sh

.. _util_add_colormap:

Add Colormap
------------

.. argparse::
    :module: polar2grid.add_colormap
    :func: get_parser
    :prog: add_colormap.sh


Colormap files are comma-separated 'integer,R,G,B,A' text files.

A basic greyscale example for an 8-bit geotiff would be::

    0,0,0,0,255
    1,1,1,1,255
    ...
    254,254,254,254,255
    255,255,255,255,255

Where the `...` represents the lines in between, meaning every input
geotiff value has a corresponding RGBA value specified. The first value
is the input geotiff value, followed by R (red), G (green), B (blue),
and A (alpha).

This script will also linearly interpolate between two values.
So the above colormap file could also be written in just two lines::

    0,0,0,0,255
    255,255,255,255,255

Often times you may want to have the 0 value as a transparent 'fill' value
and continue the colormap after that. This can be done by doing the
following::

    # 0 is a fill value
    0,0,0,0,0
    # 1 starts at bright red
    1,255,0,0,255
    # and we end with black at the end
    255,0,0,0,255

.. note::

    Not all image viewers will obey the transparent (alpha) settings

Blank lines are allowed as well as spaces between line elements.

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

