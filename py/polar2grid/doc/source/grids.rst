Grids
=====

Polar2grid is capable of handling gpd files or PROJ.4 strings to describe
the grids being mapped to.
See the :doc:`Backend Documentation <backends/index>` to see what grids are
supported for your specific grid.  For more details on each grid see
the package provided 
`Grids Configuration File <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/grids/grids.conf>`_.
If you would like to add your own grid see the :doc:`dev_guide/grids` section
of the Developer's Guide.

.. _gpd_grids:

GPD Grids
---------

The following grids are used with the mapx library through the C version of
ll2cr during polar2grid's remapping step.

AWIPS Grid 211e
^^^^^^^^^^^^^^^
:Grid Name: 211e
:Description: CONUS East Grid
:GPD File:    `grid211e.gpd <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/grids/grid211e.gpd>`_

AWIPS Grid 211w
^^^^^^^^^^^^^^^
:Grid Name: 211w
:Description: CONUS West Grid
:GPD File:    `grid211w.gpd <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/grids/grid211w.gpd>`_

AWIPS Grid 203
^^^^^^^^^^^^^^
:Grid Name: 203
:Description: Alaska Grid
:GPD File:    `grid203.gpd <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/grids/grid203.gpd>`_

AWIPS Grid 204
^^^^^^^^^^^^^^
:Grid Name: 204
:Description: Hawaii Grid
:GPD File:    `grid204.gpd <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/grids/grid204.gpd>`_

.. _proj4_grids:

PROJ.4 Grids
------------

The following grids are used with the PROJ.4 library (using pyproj bindings)
through the python version of ll2cr during polar2grid's remapping step.  See
`PROJ.4 GenParams <http://trac.osgeo.org/proj/wiki/GenParms>`_
for more information on what each parameter means.

.. note::

    If the grid does not have a parameter specified it will be derived from the
    data during remapping.  This allows for grids that fit to the data.

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



