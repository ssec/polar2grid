Utility Scripts
===============

The following are scripts that can be used to aid in the 
creation of customized |project| products. All utility
scripts are stored in the bin directory:

.. ifconfig:: is_geo2grid

    .. code-block:: bash

        $GEO2GRID_HOME/bin/<script>.sh ...

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

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
    :nodefaultconst:


Example:

.. code-block:: bash

    p2g_grid_helper.sh my_grid_name -150.1 56.3 250 -250 1000 1000
    # Will result in:
    my_grid_name, proj4, +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=56.30000 +lat_1=56.30000 +lon_0=-150.10000 +units=m +no_defs, 1000, 1000, 250.00000, -250.00000, -152.17946deg, 57.40550deg

The above example creates a proj4 text grid line named 'my_grid_name' defined
to be at 250m resolution, 1000 pixels width and height, and centered at 
-150.1 degrees longitude and 56.3 degrees latitude. The projection 
is a lambert conic conformal projection which was chosen based on the 
center longitude and latitude.

Once this text line has been output, it can be added to a text file and
referenced in the |script_literal| command line.  For instance, if I save
the output text grid line to a file named ``/home/user/my_grids.conf``, I can
create a GeoTIFF from satellite data by executing a command like this:

.. ifconfig:: is_geo2grid

    .. code-block:: bash

       geo2grid.sh -r abi_l1b -w geotiff --grid-configs /home/user/my_grids.conf -g my_grid_name -f <path_to_files>

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

       polar2grid.sh viirs_sdr gtiff --grid-configs /home/p2g/my_grids.conf -g my_grid_name -f <path_to_files>

.. _util_add_coastlines:

Add Overlays (Borders, Coastlines, Grids Lines, Rivers)
-------------------------------------------------------

.. argparse::
    :module: polar2grid.add_coastlines
    :func: get_parser
    :prog: add_coastlines.sh
    :nodefaultconst:

Examples:

.. code-block:: bash

    add_coastlines.sh --add-coastlines --add-rivers --rivers-resolution=h --add-grid GOES-16_ABI_RadF_true_color_20181112_063034_GOES-East.tif
    add_coastlines.sh --add-coastlines --add-borders --borders-resolution=h --borders-outline='red' --add-grid GOES-16_ABI_RadF_natural_color_20181112_183034_GOES-East.tif -o abi_natural_color_coastlines.png

.. _util_add_colormap:

Add Colormap
------------

.. argparse::
    :module: polar2grid.add_colormap
    :func: get_parser
    :prog: add_colormap.sh
    :nodefaultconst:


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

Note this script is no longer needed as of |project| 2.3 where colormaps
can be specified directly in rescaling configuration files. For example:

.. parsed-literal::

    [rescale:amsr2_btemp_36.5h]
    data_kind=toa_brightness_temperature
    instrument=amsr2
    product_name=btemp_36.5h
    method=palettize
    min_in=180
    max_in=280
    colormap=$POLAR2GRID_HOME/colormaps/amsr2_36h.cmap
    alpha=False

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

    gtiff2kmz.sh GOES-16_ABI_RadC_natural_color_20181219_174215_GOES-East.tif


.. _util_script_fireoverlay:

Overlay GeoTIFF Images
----------------------

The ``overlay.sh`` script can be used to overlay one image (ex. VIIRS EDR
Active Fires) on top of another image (ex. VIIRS Adaptive DNB or True Color).
This script uses GDAL's ``gdal_merge.py`` utility underneath, but converts
everything to RGBA format first for better consistency in output images.

.. code-block:: bash

    usage: overlay.sh background.tif foreground.tif out.tif

Example:
The following example shows how you would overlay the VIIRS Active
Fire AFMOD resolution Fire Confidence Percentage GeoTIFF image on top of a 
VIIRS Day/Night Band GeoTIFF image.

.. code-block:: bash

    overlay.sh noaa20_viirs_dynamic_dnb_20191120_151043_wgs84_fit.tif noaa20_viirs_confidence_pct_20191120_151043_wgs84_fit.tif afmod_overlay_confidence_cat.tif
      

.. ifconfig:: is_geo2grid

  Convert GeoTIFFs to MP4 Video
  -----------------------------

  The ``gtiff2mp4.sh`` script converts a series of GeoTIFF files in to a
  single MP4 video file. This script uses default video creation settings
  to support most video players. If an image is too large for the video
  creation they will be automatically scaled to a smaller size.

  .. code-block:: bash

      gtiff2mp4.sh out.mp4 in1.tif in2.tif ...

  This will create a MP4 video file called ``out.mp4`` with 24 images (frames)
  per second.

  Example:

  .. code-block:: bash

      gtiff2mp4.sh my_natural_color_animation.mp4  *natural_color*.tif

.. ifconfig:: is_geo2grid

  Remap GOES GeoTIFFs
  -------------------

  The projection of the GOES-East and GOES-West satellites uses special
  parameters that are not always supported by older visualization tools.
  While new versions of GDAL and PROJ.4 libraries can often fix these issues,
  this is not always an option. |project| provides the ``reproject_goes.sh``
  script to remap GOES GeoTIFFs to a nearly identical projection that is more
  compatible with older visualization tools. The script can be called by 
  executing:

  .. code-block:: bash

      reproject_goes.sh in1.tif in2.tif in3.tif

  The script will take the original name and add a ``-y`` to the end. So in
  the above example the results would be ``in1-y.tif``, ``in2-y.tif``,
  and ``in3-y.tif``. The ``y`` refers to the sweep angle axis projection
  parameter that differs between the input geotiff (``x``) and the output
  geotiff (``y``).

.. _util_convert_grids:

Convert legacy grids.conf to grids.yaml format
----------------------------------------------

.. argparse::
    :module: polar2grid.utils.convert_grids_conf_to_yaml
    :func: get_parser
    :prog: convert_grids_conf_to_yaml.sh
    :nodefaultconst:

Example:

.. code-block:: bash

    convert_grids_conf_to_yaml.sh old_file.conf > new_file.yaml

.. _util_p2g_proj:

Python Proj
-----------

.. argparse::
    :module: polar2grid.core.proj
    :func: get_parser
    :prog: p2g_proj.sh
    :nodefaultconst:

Example:

.. code-block:: bash

    p2g_proj.sh "+proj=lcc +datum=NAD83 +ellps=GRS80 +lat_1=25 +lon_0=-95" -105.23 38.5
    # Will result in:
    -878781.238459 4482504.91307
