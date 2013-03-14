MODIS Frontend
==============

The MODIS Frontend operates on Level 1B files from the Moderate Resolution
Imaging Spectroradiometer (MODIS) instruments on the Aqua and Terra
satellites. Only data files and not geonavigation files should be passed to
the frontend. Input files must have the following format to be accepted by
the frontend::

    a1.YYJJJ.HHMM.<product kind>.hdf
    t1.YYJJJ.HHMM.<product kind>.hdf

Only certain files and product kinds are supported at the moment::

    1000m
    250m
    mod06ct
    mod07

.. warning::

    250m and 1000m files should not be provided in the same call to a
    :term:`glue script`. From the point-of-view of backends there is no
    difference between the 250m and 1000m reflectance bands. Backend product
    files will probably be overwritten.
