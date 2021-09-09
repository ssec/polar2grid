Third-Party Recipes
===================

Third-party tools like those provided by
the Geospatial Data Abstraction Library (GDAL) can be 
found in the ``libexec/python_runtime/bin`` directory alongside the Python
executable used by |project|.

.. ifconfig:: not is_geo2grid

    Combining GeoTIFF Images
    ------------------------

    When working with polar orbiter satellite data, it is often
    useful to stitch images of neighboring passes together.
    The GDAL merge tool can do this easily using |project|
    GeoTIFF output files.

    Suppose we have two VIIRS GeoTIFF files created from
    two sequential Suomi NPP overpasses.  The GeoTIFF
    files we use in this example are
    false color images from data acquired at 20:43 and
    22:22 UTC on 23 March 2017 created in a
    WGS84 projection.  The individual images are
    displayed side by side below.

    .. raw:: latex

        \newpage
        \begin{landscape}

    .. figure:: _static/example_images/VIIRS_False_Color_Side_by_Side_Example_P2G.png
        :width: 100%
        :align: center

        Suomi-NPP VIIRS False Color Images from two separate passes
        (Red:VIIRS M-Band 11 (2.25 μm), Green:VIIRS M-Band 7 (.87 μm)
        and Blue:VIIRS M-Band 5 (.67μm)) observed on 23 March 2017.

    .. raw:: latex

        \end{landscape}
        \newpage

    To combine these images into a single output GeoTIFF image
    I can use the `gdal_merge.py` command that is packaged as
    part of |project|:

    .. code-block:: bash

        gdal_merge.py -n 0 -o my_false_color.tif npp_viirs_false_color_20170323_204320_wgs84_fit.tif npp_viirs_false_color_20170323_222255_wgs84_fit.tif

    The `-n 0` is used to set the background data value so
    it will not be included in the merge.  This is required
    because without it, the black regions that border
    the second WGS84 GeoTIFF will be overlaid on top of the first
    image.

    The resulting image is displayed below.

    .. figure:: _static/example_images/my_false_color.jpg
        :width: 100%
        :align: center

        Merged S-NPP VIIRS False Color Images created from a pair
        of images acquired and processed from two different orbits.

    More than one image can be combined. There are more options
    available to `gdal_merge.py`.  Execute

    .. code-block:: bash

        gdal_merge.py -h

    for a complete list of options.
