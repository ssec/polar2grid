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

Will result in:

.. code-block:: yaml

    my_grid_name:
      projection:
        proj: lcc
        lat_1: 56.3
        lat_0: 56.3
        lon_0: -150.1
        datum: WGS84
        units: m
        no_defs: null
        type: crs
      shape:
        height: 1000
        width: 1000
      center:
        x: -150.1
        y: 56.3
        units: degrees
      resolution:
        dx: 250.0
        dy: 250.0

The above example creates a
`YAML formatted <https://en.wikipedia.org/wiki/YAML>`_ block of text for the
grid named 'my_grid_name'. It is defined to have a pixel resolution of 250m,
have 1000 rows and 1000 columns, and be centered at
-150.1 degrees longitude and 56.3 degrees latitude. The projection
is a lambert conic conformal projection which was chosen based on the
center longitude and latitude.

Once this text has been output, it can be added to a text file ending in
``.yaml`` and referenced in the |script_literal| command line.  For instance,
if I save the output text to a file named ``/home/user/my_grids.yaml``, I can
create a GeoTIFF from satellite data by executing a command like this:

.. ifconfig:: is_geo2grid

    .. code-block:: bash

       geo2grid.sh -r abi_l1b -w geotiff --grid-configs /home/user/my_grids.yaml -g my_grid_name -f <path_to_files>

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

       polar2grid.sh -r viirs_sdr -w geotiff --grid-configs /home/p2g/my_grids.yaml -g my_grid_name -f <path_to_files>

.. _util_add_coastlines:

Add Overlays (Borders, Coastlines, Grids Lines, Rivers)
-------------------------------------------------------

.. argparse::
    :module: polar2grid.add_coastlines
    :func: get_parser
    :prog: add_coastlines.sh
    :nodefaultconst:

Examples:

.. ifconfig:: is_geo2grid

    .. code-block:: bash

       add_coastlines.sh GOES-18_ABI_RadF_true_color_night_microphysics_20221115_123020_GOES-West.tif --add-coastlines --add-rivers --rivers-resolution=h --add-grid -o abi_true_color_coastlines.png
       add_coastlines.sh --add-coastlines --add-borders --borders-resolution=h --borders-outline='red' --add-grid GOES-17_ABI_RadF_natural_color_20181211_183038_GOES-West.tif -o abi_natural_color_coastlines.png

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

       add_coastlines.sh noaa20_viirs_true_color_20221011_174112_wgs84_fit.tif --add-coastlines --coastlines-outline yellow --coastlines-level 1 --coastlines-resolution=i --add-borders --borders-level 2 --borders-outline gray --add-grid --grid-text-size 16 --grid-fill white --grid-D 5 5 --grid-d 5 5 --grid-outline white

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

Note this script is no longer needed in modern versions of |project| if the
original geotiff (no color) is not needed. The colormap can be specified
directly in the enhancement YAML file for a product. For example, for the
AMSR-2 L1B product "btemp_36.5h" we could add the following to a
``etc/enhancements/amsr2.yaml`` (or ``generic.yaml``):

.. parsed-literal:: yaml

  amsr2_btemp_365h:
    name: btemp_36.5h
    sensor: amsr2
    operations:
      - name: add_colormap
        method: !!python/name:polar2grid.enhancements.palettize
        kwargs:
          palettes:
            - filename: $POLAR2GRID_HOME/colormaps/amsr2_36h.cmap
              min_value: 180
              max_value: 280

When saved using the 'geotiff' writer this will be converted to an RGB/RGBA
image. Optionally you can provide the ``--keep-palette`` flag to your
|script_literal| call which will add the colormap as a geotiff color table.

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

.. ifconfig:: is_geo2grid

    .. code-block:: bash

        gtiff2kmz.sh  GOES-18_ABI_RadF_natural_color_20221115_183020_GOES-West.tif

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

        gtiff2kmz.sh noaa20_viirs_false_color_20221011_174112_wgs84_fit.tif

.. _util_script_fireoverlay:

Overlay GeoTIFF Images
----------------------

.. ifconfig:: not is_geo2grid

  The ``overlay.sh`` script can be used to overlay one GeoTIFF image
  (ex. VIIRS EDR Active Fires) on top of another image (ex. VIIRS
  Adaptive DNB or True Color).  This script uses GDAL's ``gdal_merge.py``
  utility underneath, but converts everything to RGBA format first
  for better consistency in output images.

.. ifconfig:: is_geo2grid

  The ``overlay.sh`` script can be used to overlay one GeoTIFF image
  (ex. Gridded Geostationary Lightning Mapper (GLM)) on top of another image (ex. GOES
  infrared brightness temperature Image).  This script uses GDAL's ``gdal_merge.py``
  utility underneath, but converts everything to RGBA format first
  for better consistency in output images.

.. code-block:: bash

    usage: overlay.sh background.tif foreground.tif out.tif

.. ifconfig:: not is_geo2grid

   Example:
   The following example shows how you would overlay the VIIRS Active
   Fire AFMOD resolution Fire Confidence Percentage GeoTIFF image on top of a
   VIIRS Day/Night Band GeoTIFF image.

  .. code-block:: bash

      overlay.sh noaa20_viirs_dynamic_dnb_20191120_151043_wgs84_fit.tif noaa20_viirs_confidence_pct_20191120_151043_wgs84_fit.tif afmod_overlay_confidence_cat.tif

.. ifconfig:: is_geo2grid

   Example:
   The following example shows how you would overlay the GOES ABI AIT Level-2 Cloud
   top Tempetaure Product on top of a GOES ABI Band 14 brithtness temperature image.

  .. code-block:: bash

      overlay.sh GOES-17_ABI_RadF_C14_20221123_183031_GOES-West.tif GOES-17_ABI_TEMP_20221123_183031_GOES-West.tif abi17_fd_overlay.tif

.. ifconfig:: is_geo2grid

.. _util_convert_to_video:

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
