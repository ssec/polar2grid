Grids
=====

Polar2grid is capable of handling PROJ.4 strings to describe the grids being mapped to.
For more details on each grid see the package provided
`Grids Configuration File <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/grids/grids.conf>`_.
If you would like to add your own grid see the :doc:`dev_guide/grids` section
of the Developer's Guide.

The following grids are used with the PROJ.4 library (using pyproj bindings)
through the "ll2cr" step of remapping.  See
`PROJ.4 GenParams <http://trac.osgeo.org/proj/wiki/GenParms>`_
for more information on what each parameter means.

.. note::

    If the grid does not have a parameter specified it will be derived from the
    data during remapping.  This allows for grids that fit to the data (dynamic
    grids).

.. _wgs84_fit:

WGS84 Dynamic Fit
^^^^^^^^^^^^^^^^^
:Grid Name: wgs84_fit
:Description: Longitude/Latitude WGS84 Grid
:PROJ.4 String: +proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs
:Grid Width: None
:Grid Height: None
:X Pixel Size: 0.0001 radians
:Y Pixel Size: 0.0001 radians
:X Origin: None
:Y Origin: None

Lambert Conic Conformal Dynamic Fit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:Grid Name: lcc_fit
:Description: 1km East CONUS centered lcc grid
:PROJ.4 String: +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=25 +lon_0=-95
:Grid Width: None
:Grid Height: None
:X Pixel Size: 1000 meters
:Y Pixel Size: 1000 meters
:X Origin: None
:Y Origin: None

High Resolution Lambert Conic Conformal Dynamic Fit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:Grid Name: lcc_fit_hr
:Description: 400m East CONUS centered lcc grid
:PROJ.4 String: +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=25 +lon_0=-95
:Grid Width: None
:Grid Height: None
:X Pixel Size: 400 meters
:Y Pixel Size: 400 meters
:X Origin: None
:Y Origin: None

Polar-Stereographic North Pacific
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:Grid Name: polar_north_pacific
:Description: 400m Northern Pacific Grid
:PROJ.4 String: +proj=stere +datum=WGS84 +ellps=WGS84 +lat_0=90 +lat_ts=45.0 +lon_0=-170
:Grid Width: None
:Grid Height: None
:X Pixel Size: 400 meters
:Y Pixel Size: 400 meters
:X Origin: None
:Y Origin: None

Polar-Stereographic South Pacific
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:Grid Name: polar_south_pacific
:Description: 400m Southern Pacific Grid
:PROJ.4 String: +proj=stere +datum=WGS84 +ellps=WGS84 +lat_0=-90 +lat_ts=-45.0 +lon_0=-170
:Grid Width: None
:Grid Height: None
:X Pixel Size: 400 meters
:Y Pixel Size: 400 meters
:X Origin: None
:Y Origin: None



