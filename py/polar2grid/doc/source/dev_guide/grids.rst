Grids
=====

The :py:mod:`grids <polar2grid.grids.grids>` module is where grid information
is made available to :term:`glue scripts` and developers. Currently, you can
provide PROJ.4 grids (static or dynamic) or GPD grids to the polar2grid
system, although it is
ultimately the backends decision of whether or not to support a grid. GPD
grids are used with the ms2gt utilities and specify a static grid. PROJ.4
grids are specified directly in the grid configuration files (see below).
PROJ.4 grids can be static, meaning the grid definition specifies the
projection, pixel size, origin, and grid size. PROJ.4 grids can also be
dynamic, meaning that only some grid defining parameters are specified.
An example of a dynamic grid is the :ref:`wgs84_fit` grid. This grid
does not have an origin or grid size specified, which tells the python
version of ll2cr to calculate those values from the data it is gridding.

Adding your own grid
--------------------

Polar2Grid allows users to define and add their own grids for remapping in
any glue script. The Polar2Grid package provides a default set of grids that
can be specified on the command line with most :term:`glue scripts`.
This built-in configuration file can be found in the source on github
`here <https://github.com/davidh-ssec/polar2grid/tree/master/py/polar2grid/polar2grid/grids/grids.conf>`_.
If you wish to add your own grids as a replacement for or in addition to the
provided set you'll have to make your own grid configuration file.

Any glue script that provides the :option:`--grid-configs` command line option
supports user-provided grids. Multiple files can be listed with this command
line flag (space separated). If you would like to add your grids in addition
to the package provided set of grids you must specify "grids.conf" as one of
the files on the command line.

Configuration files are processed in the order they are specified. If more
than one grid configuration file specifies the same grid the most recently
processed file's entry is
used. It is recommended that you don't reuse a package-provided grid's name
so there is no confusion about the configuration of that grid when viewing
polar2grid products.

The following steps will add a configuration file to polar2grid in addition
to the built-in grids:

1. Create a text file named anything besides "grids.conf". Open it for editing.
   For software bundle users, there is a ``grid_configs`` directory in the
   root of the software bundle where user configuration files can be stored.
2. Add a line for each grid you would like to add to polar2grid. Follow the
   :ref:`grid_configuration_format` section below. This section also has
   header comments specifying each column that can be added to your file
   for clarity.
3. Call any polar2grid glue script and add the command line option
   ``--grid-configs grids.conf <your-file.conf>``. If you would like only
   your grids and not the package provided grids don't include the
   "grids.conf" in the command line option.

If you are unsure which type of grid to make, it is recommended that you
create a PROJ.4 grid as there is more online documentation for this format
and also allows for dynamic parameters.

.. note::

    The decision of whether a grid is supported or not is ultimately up to
    :doc:`the backend <../backends/index>` used by a glue script. Some
    backends support any grid (GPD or PROJ.4) and others only a handful.
    Check the :doc:`../backends/index` section for your specific backend.

.. warning::

    Some glue scripts force a certain built-in grid by default. These type
    of glue scripts will fail if no grid is forced (:option:`-g` flag) or
    the built-in grid configuration file is not provided.

.. _grid_configuration_format:

Grid Configuration File Format
------------------------------

Example Grid Configuration File: :download:`grid_example.conf <../../../../../swbundle/grid_configs/grid_example.conf>`

Grid configuration files are comma-separated text files with 2 possible types
of entries, PROJ.4 grids and GPD grids. Comments can be added by prefixing lines
with a ``#`` character. Spaces are allowed between values to make aligning columns
easier. The following describes the 2 types of grids and each column that must
be specified (in order). A sample header comment is also provided to add to your
grid configuration file for better self-documentation. The example grid
configuration file linked to above can also be found in the software bundle in
``swbundle/grid_configs/grid_example.conf``.

As discussed in the introduction of this section, PROJ.4 grids can be
dynamic or static, but GPD grids can only be static. Of the 3 dynamic
grid attributes (grid size, pixel size, grid origin) a maximum of 2 can
be dynamic at a time for a single grid.

PROJ.4 Grids:

# grid_name,proj4,proj4_str,width,height,pixel_size_x,pixel_size_y,origin_x,origin_y

 #. **grid_name**:
     A unique grid name describing the behavior of the grid. Grid name's should not contain spaces.
 #. **proj4**:
     A constant value, "proj4" without the quotes. This tells the software
     reading the configuration file that this grid is a PROJ.4 grid.
 #. **proj4_str**:
     A PROJ.4 projection definition string. Some examples can be found in the
     :doc:`../grids` list, but for more information on possible parameters see
     `PROJ.4 GenParams <http://trac.osgeo.org/proj/wiki/GenParms>`_. Note that
     compatiblity with certain PROJ.4 string components may be dependent on the
     version of the PROJ.4(pyproj) library that polar2grid uses, so testing
     should be done to verify that your string works properly.
 #. **width**:
     Width of the grid in number of pixels. This value may be 'None' if it
     should be dynamically determined. Width and height must both be specified
     or both not specified.
 #. **height**:
     Height of the grid in number of pixels. This value may be 'None' if it
     should be dynamically determined. Width and height must both be specified
     or both not specified.
 #. **pixel_size_x**:
     Size of one pixel in the X direction in grid units. Most grids are in
     metered units, except for ``+proj=latlong`` which expects radians.
     This value may be 'None' if it should be dynamically determined.
     X and Y pixel size must both be specified or both not specified.
 #. **pixel_size_y**:
     Size of one pixel in the Y direction in grid units (**MUST** be negative).
     Most grids are in
     metered units, except for ``+proj=latlong`` which expects radians.
     This value may be 'None' if it should be dynamically determined.
     X and Y pixel size must both be specified or both not specified.
 #. **origin_x**:
     The grid's top left corner's X coordinate in grid units. Most grids are in
     metered units, except for ``+proj=latlong`` which expects radians.
     This value may be 'None' if it should be dynamically determined.
     X and Y origin coordinates must both be specified or both not specified.
     For help with converting lon/lat values into X/Y values see the
     documentation for the utility script :ref:`util_p2g_proj`.
 #. **origin_y**:
     The grid's top left corner's Y coordinate in grid units. Most grids are in
     metered units, except for ``+proj=latlong`` which expects radians.
     This value may be 'None' if it should be dynamically determined.
     X and Y origin coordinates must both be specified or both not specified.
     For help with converting lon/lat values into X/Y values see the
     documentation for the utility script :ref:`util_p2g_proj`.

An example of running the :ref:`util_p2g_proj` utility::

    $POLAR2GRID_HOME/bin/p2g_proj.sh "+proj=lcc +datum=NAD83 +ellps=GRS80 +lat_1=25 +lon_0=-95" -105.23 38.5
    # Will result in:
    -878781.238459 4482504.91307

GPD Grids:

# grid_name,gpd,gpd_filename,ul_lon,ul_lat,ur_lon,ur_lat,lr_lon,lr_lat,ll_lon,ll_lat

 #. **grid_name**:
     A unique grid name describing the behavior of the grid. Grid name's should not contain spaces.
 #. **gpd**:
     A constant value, "gpd", without the quotes. This tells the software
     reading the configuration file that this grid is a PROJ.4 grid.
 #. **gpd_filename**:
     Absolute path to a GPD file. See the
     `ms2gt documentation <http://geospatialmethods.org/documents/ppgc/ppgc.html>`_
     for syntax
     and format of GPD files.
 #. **ul_lon**:
     Longitude of the upper left corner of the grid.
 #. **ul_lat**:
     Latitude of the upper left corner of the grid.
 #. **ur_lon**:
     Longitude of the upper right corner of the grid.
 #. **ur_lat**:
     Latitude of the upper right corner of the grid.
 #. **lr_lon**:
     Longitude of the lower right corner of the grid.
 #. **lr_lat**:
     Latitude of the lower right corner of the grid.
 #. **ll_lon**:
     Longitude of the lower left corner of the grid.
 #. **ll_lat**:
     Latitude of the lower left corner of the grid.

Grid corners are used during :term:`grid determination` to define a polygon
describing the grid. PROJ.4 grids' corners are calculated when needed, but
GPD grids must have their corners specified in the configuration file.

Understanding the grids module
------------------------------

The grids module's main points of access are the
:py:class:`polar2grid.grids.grids.Cartographer` class and the
:py:func:`polar2grid.grids.grids.create_grid_jobs` function. The
``Cartographer`` class stores all information of the grids it knows and
makes it available to the developer. The ``create_grid_jobs`` function
returns a dictionary of dictionaries that can be passed to the remapping
components of polar2grid for processing. The ``grid_info`` dictionaries
returned by the ``get_*_info`` methods of the ``Cartographer`` are different
depending on the kind of grid being described.

One important
piece of information is that the ``grid_kind`` key which is set to either the
:data:`GRID_KIND_GPD` constant or :data:`GRID_KIND_PROJ4` constant value.

Grid Jobs
---------

The :py:func:`polar2grid.grids.grids.create_grid_jobs` function is used by
:term:`glue scripts` to create a python dictionary structure that can be
passed to the remapping components. This function asks the backend (via
the `can_handle_inputs` function) what grids it is configured or is able
to support. If the user did not specify any grids on the command line then
grid determination is done to decide what grids would be useful to project
the data to.

The dictionary structure returned by
:py:func:`polar2grid.grids.grids.create_grid_jobs` has the following
information::

    grid_jobs = {
            grid_name_1 : {
                    ( band_kind, band_id ) : {
                                ... copy of band information from the frontend ...
                                grid_info : Grid information dictionary returned by
                                            the Cartographer
                                }
                    }
            }

Grid Determination
------------------

Grid determination is the process of checking if it would be useful to remap
the data being processed into any of the grids supported by the backend being
used. This is done by comparing the area of the observation data that overlaps
the area of the grid. If the data covers more than 10% of the grid then that
grid is considered useful and will be added to the ``grid_jobs`` structure
described above.

The coverage percentage threshold (10% by default) can be changed by an
environment variable:

.. envvar:: POLAR2GRID_GRID_COVERAGE

    The value used to determine whether a grid is useful or not. Should be
    the minimum ratio of data area to grid area. So the default is ``"0.1"``
    for 10%.


