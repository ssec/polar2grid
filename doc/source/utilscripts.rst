Utility Scripts
===============

The following are scripts that can be used to aid in the 
the creation of customized |project| products. All utility
scripts are stored in the bin directory:

.. ifconfig:: is_geo2grid

    $GEO2GRID_HOME/bin/<script>.sh ...

.. ifconfig:: not is_geo2grid

    $POLAR2GRID_HOME/bin/<script>.sh ...

For simplicity, the sections below will specify the script directly, but
note the scripts exist in the bin directory above.

.. _util_p2g_grid_helper:

Defining Your Own Grids (Grid Configuration Helper)
---------------------------------------------------

.. argparse::
    :module: polar2grid.grids.config_helper
    :func: get_parser
    :prog: p2g_grid_helper.sh


Example:

.. code-block:: bash

    p2g_grid_helper.sh my_grid_name -150.1 56.3 250 -250 1000 1000
    # Will result in:
    my_grid_name, +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=56.300 +lat_1=56.300 +lon_0=-150.100 +units=m +no_defs, 1000, 1000, 250.000, -250.000, -125000.000, 125000.000

The above example creates a text grid line named 'my_grid_name' at a 
250m resolution, 1000 pixels wide and height, and centered at 
-150.1 degrees longitude and 56.3 degrees latitude. The projection 
is a lambert conic conformal projection which was chosen based on the 
center longitude and latitude.

Once this text line has been output, it can be added to a text file and
referenced in any Polar2Grid command line.  For instance, if I save
the output text grid line to a file named ``/home/user/my_grids.txt``, I can
create a GeoTIFF from satellite data by executing a command like this:

.. ifconfig:: is_geo2grid

    .. code-block:: bash

       geo2grid.sh -r abi_l1b -w geotiff --grid-configs /home/user/my_grids.txt -g my_grid_name -f <path_to_files>

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

       polar2grid.sh viirs_sdr gtiff --grid-configs /home/p2g/my_grids.txt -g my_grid_name -f <path_to_files>

.. _util_add_coastlines:

Add Overlays (Borders, Coastlines, Grids Lines)
-----------------------------------------------

.. argparse::
    :module: polar2grid.add_coastlines
    :func: get_parser
    :prog: add_coastlines.sh

Example:

.. code-block:: bash

    add_coastlines.sh --add-coastlines --add-borders gcom-w1_amsr2_btemp_89.0ah_20160719_190300_lcc_fit.tif
    add_coastlines.sh --add-coastlines --add-borders --borders-resolution=h --borders-outline='red' --add-grid npp_viirs_true_color_20170305_193251_lcc_fit.tif -o myfile.png

.. _util_add_colormap:

Add Colormap
------------

.. argparse::
    :module: polar2grid.add_colormap
    :func: get_parser
    :prog: add_colormap.sh


Colormap files are comma-separated 'integer,R,G,B,A' text files.

A basic greyscale example for an 8-bit GeoTIFF would be:

.. parsed-literal::

    0,0,0,0,255
    1,1,1,1,255
    ...
    254,254,254,254,255
    255,255,255,255,255

Where the `...` represents the lines in between, meaning every input
GeoTIFF value has a corresponding RGBA value specified. The first value
is the input GeoTIFF value, followed by R (red), G (green), B (blue),
and A (alpha).

This script will also linearly interpolate between two values.
So the above colormap file could also be written in just two lines:

.. parsed-literal::

    0,0,0,0,255
    255,255,255,255,255

Often times you may want to have the 0 value as a transparent 'fill' value
and continue the colormap after that. This can be done by doing the
following:

.. parsed-literal::

    # 0 is a fill value
    0,0,0,0,0
    # 1 starts at bright red
    1,255,0,0,255
    # and we end with black at the end
    255,0,0,0,255

.. note::

    Not all image viewers will obey the transparent (alpha) settings

Blank lines are allowed as well as spaces between line elements.

.. _util_gtiff2kmz:

GeoTIFF to KMZ Conversion
-------------------------

The ``gtiff2kmz.sh`` script converts a single GeoTIFF file into a Google Earth
compatible Keyhole Markup language Zipped (KMZ) file. It is a wrapper around the 
GDAL tool ``gdal2tiles.py``.  The script can be executed with:

.. code-block:: bash

    gtiff2kmz.sh input.tif [output.kmz]

Where ``output.kmz`` is an optional parameter specifying the name of the
output KMZ file. If it isn't specified it defaults to the input
filename with the extension changed to ``.kmz``.

Example:

.. code-block:: bash

    gtiff2kmz.sh npp_viirs_true_color_20161210_193100_wgs84_fit.tif


Convert GeoTIFFs to MP4 Video
-----------------------------

The ``gtiff2mp4.sh`` script converts a series of GeoTIFF files in to a
single MP4 video file. This script uses default video creation settings
to support the most video players. If an image is too large for the video
creation they will be automatically scaled to a smaller size.

.. code-block:: bash

    gtiff2mp4.sh out.mp4 in1.tif in2.tif ...

.. _util_p2g_proj:

Python Proj
-----------

.. argparse::
    :module: polar2grid.core.proj
    :func: get_parser
    :prog: p2g_proj.sh

Example:

.. code-block:: bash

    p2g_proj.sh "+proj=lcc +datum=NAD83 +ellps=GRS80 +lat_1=25 +lon_0=-95" -105.23 38.5
    # Will result in:
    -878781.238459 4482504.91307
