Grids
=====

|project| allows users to remap to one or more projected grids. A grid
defines the uniform geographic area that an output image covers. |project|
comes with various grids to choose from that should suit most users and their
use cases. Some grids are provided for specific writers (like AWIPS SCMI), but
can be used for other writers as well. For those cases that the provided
grids aren't enough it is possible to create your own custom grids. See the
:doc:`custom_grids` documentation for help with this.

Provided Grids
--------------

Below are descriptions for a few of the grids provided with |project|.
For information on all of the grids provided by |project| see the
`Grids Configuration File <https://github.com/ssec/polar2grid/blob/master/polar2grid/grids/grids.conf>`_.

The grids' projections are defined using PROJ.4. Go to
the `PROJ documentation <https://proj4.org/usage/projections.html>`_
for more information on what each projection parameter means.

.. note::

    If the grid does not have a parameter specified it will be derived from the
    data during remapping.  This allows for grids that fit to the data (dynamic
    grids).

.. _grid_wgs84_fit:

WGS84 Dynamic Fit
^^^^^^^^^^^^^^^^^

:Grid Name: wgs84_fit
:Description: Longitude/Latitude WGS84 Grid
:PROJ.4 String: +proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs
:Grid Width: None
:Grid Height: None
:X Pixel Size: 0.0057 degrees
:Y Pixel Size: 0.0057 degrees
:X Origin: None
:Y Origin: None

WGS84 Dynamic Fit 250m
^^^^^^^^^^^^^^^^^^^^^^

:Grid Name: wgs84_fit_250
:Description: Longitude/Latitude WGS84 Grid at ~250m resolution
:PROJ.4 String: +proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs
:Grid Width: None
:Grid Height: None
:X Pixel Size: 0.00225 degrees
:Y Pixel Size: 0.00225 degrees
:X Origin: None
:Y Origin: None

Lambert Conic Conformal Dynamic Fit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Grid Name: lcc_fit
:Description: 1km East CONUS centered lcc grid (alias: lcc_na)
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

Lambert Conic Conformal - South America Centered
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Grid Name: lcc_sa
:Description: 1km South America centered lcc grid
:PROJ.4 String: +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=-25 +lat_1=-25 +lon_0=-55 +units=m +no_defs
:Grid Width: None
:Grid Height: None
:X Pixel Size: 1000 meters
:Y Pixel Size: 1000 meters
:X Origin: None
:Y Origin: None

Lambert Conic Conformal - Europe Centered
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Grid Name: lcc_eu
:Description: 1km Europe centered lcc grid
:PROJ.4 String: +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=25 +lat_1=25 +lon_0=15 +units=m +no_defs
:Grid Width: None
:Grid Height: None
:X Pixel Size: 1000 meters
:Y Pixel Size: 1000 meters
:X Origin: None
:Y Origin: None

Lambert Conic Conformal - South Africa Centered
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Grid Name: lcc_south_africa
:Description: 1km South Africa centered lcc grid
:PROJ.4 String: +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=-25 +lat_1=-25 +lon_0=25 +units=m +no_defs
:Grid Width: None
:Grid Height: None
:X Pixel Size: 1000 meters
:Y Pixel Size: 1000 meters
:X Origin: None
:Y Origin: None

Lambert Conic Conformal - Australia Centered
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Grid Name: lcc_aus
:Description: 1km Australia centered lcc grid
:PROJ.4 String: +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=-25 +lat_1=-25 +lon_0=135 +units=m +no_defs
:Grid Width: None
:Grid Height: None
:X Pixel Size: 1000 meters
:Y Pixel Size: 1000 meters
:X Origin: None
:Y Origin: None

Lambert Conic Conformal - Asia Centered
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Grid Name: lcc_asia
:Description: 1km Asia centered lcc grid
:PROJ.4 String: +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=25 +lat_1=25 +lon_0=105 +units=m +no_defs
:Grid Width: None
:Grid Height: None
:X Pixel Size: 1000 meters
:Y Pixel Size: 1000 meters
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

Polar-Stereographic Alaska
^^^^^^^^^^^^^^^^^^^^^^^^^^

:Grid Name: polar_alaska
:Description: 400m Northern Grid over Alaska
:PROJ.4 String: +proj=stere +datum=WGS84 +ellps=WGS84 +lat_0=90 +lat_ts=60.0 +lon_0=-150
:Grid Width: None
:Grid Height: None
:X Pixel Size: 400 meters
:Y Pixel Size: 400 meters
:X Origin: None
:Y Origin: None

Polar-Stereographic Canada
^^^^^^^^^^^^^^^^^^^^^^^^^^

:Grid Name: polar_canada
:Description: 1km Northern Grid over Canada
:PROJ.4 String: +proj=stere +datum=WGS84 +ellps=WGS84 +lat_0=90 +lat_ts=45.0 +lon_0=-150
:Grid Width: None
:Grid Height: None
:X Pixel Size: 1000 meters
:Y Pixel Size: 1000 meters
:X Origin: None
:Y Origin: None

Polar-Stereographic Russia
^^^^^^^^^^^^^^^^^^^^^^^^^^

:Grid Name: polar_russia
:Description: 400m Northern Grid over Russia
:PROJ.4 String: +proj=stere +datum=WGS84 +ellps=WGS84 +lat_0=90 +lat_ts=45.0 +lon_0=50
:Grid Width: None
:Grid Height: None
:X Pixel Size: 400 meters
:Y Pixel Size: 400 meters
:X Origin: None
:Y Origin: None

Equirectangular Fit
^^^^^^^^^^^^^^^^^^^

:Grid Name: eqc_fit
:Description: 250m Grid centered over -100 longitude
:PROJ.4 String: +proj=eqc +datum=WGS84 +ellps=WGS84 +lat_ts=0 +lon_0=-100 +units=m +no_defs
:Grid Width: None
:Grid Height: None
:X Pixel Size: 250 meters
:Y Pixel Size: 250 meters
:X Origin: None
:Y Origin: None

GOES-East 1km
^^^^^^^^^^^^^

:Grid Name: goes_east_1km
:Description: 1 kilometer resolution GOES-16 Full Disk

GOES-East 4km
^^^^^^^^^^^^^

:Grid Name: goes_east_4km
:Description: 4 kilometer resolution GOES-16 Full Disk

GOES-East 8km
^^^^^^^^^^^^^

:Grid Name: goes_east_8km
:Description: 8 kilometer resolution GOES-16 Full Disk

GOES-East 10km
^^^^^^^^^^^^^^

:Grid Name: goes_east_10km
:Description: 10 kilometer resolution GOES-16 Full Disk

GOES-West 1km
^^^^^^^^^^^^^

:Grid Name: goes_west_1km
:Description: 1 kilometer resolution GOES-17 Full Disk

GOES-West 4km
^^^^^^^^^^^^^

:Grid Name: goes_west_4km
:Description: 4 kilometer resolution GOES-17 Full Disk

GOES-West 8km
^^^^^^^^^^^^^

:Grid Name: goes_west_8km
:Description: 8 kilometer resolution GOES-17 Full Disk

GOES-West 10km
^^^^^^^^^^^^^^

:Grid Name: goes_west_10km
:Description: 10 kilometer resolution GOES-17 Full Disk
