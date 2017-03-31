Custom Grids
============

Polar2Grid provides a set of grids to suit most use cases, but sometimes
these grids are not enough. This is why Polar2Grid allows users
to create their own custom grids.

Grids can be static, meaning the grid definition specifies the
projection, pixel size, origin, and grid size. Grids can also be
dynamic, meaning that only some grid defining parameters are specified.
An example of a dynamic grid is the :ref:`wgs84_fit` grid. This grid
does not have an origin or grid size specified, which tells the remapping
components of Polar2Grid to calculate these values from the data.

Adding your own grid
--------------------

If you wish to add your own grids as a replacement for or in addition to the
provided set you'll have to make your own grid configuration file.
The instructions below describe how to create your own configuration file
and how it can be provided to ``polar2grid.sh``:

1. Create a text file named anything besides "grids.conf". Open it for editing.
   The package includes a ``$POLAR2GRID_HOME/grid_configs`` directory
   where user configuration files can be stored.
2. Add a line to this text file for each grid you would like to add to
   Polar2Grid. Follow the
   :ref:`grid_configuration_format` section below. This section also has
   header comments specifying each column that can be added to your file
   for clarity.
3. Call any Polar2Grid glue script and add the command line option
   ``--grid-configs grids.conf <your-file.conf>``. If you would like only
   your grids and not the Polar2Grid provided grids don't include the
   "grids.conf" in the command line option.

Polar2Grid also includes a simple script that can generate the
required text string when provided with general information about the grid
you wish to create. See the :ref:`util_p2g_grid_helper` section.

.. note::

    The decision of whether a grid is supported or not is ultimately up to
    :doc:`the writer <../writers/index>` used with ``polar2grid.sh``.
    Check the :doc:`../writers/index` section for your specific writer.

.. note::

    Configuration files are loaded in the order specified. If a grid name
    is used more than once, the last one loaded is used.

.. _grid_configuration_format:

Grid Configuration File Format
------------------------------

Example Grid Configuration File: :download:`grid_example.conf <../../../../swbundle/grid_configs/grid_example.conf>`

Grid configuration files are comma-separated text files.
Comments can be added by prefixing lines
with a ``#`` character. Spaces are allowed between values to make aligning columns
easier. The following describes each column that must
be specified (in order). A sample header comment is also provided to add to your
grid configuration file for better self-documentation. The example grid
configuration file linked to above can also be found in the software bundle in
``$POLAR2GRID_HOME/grid_configs/grid_example.conf``.

As mentioned earlier, grids can be
dynamic or static. Dynamic grids may have either grid size parameters
or grid origin parameters or both unspecified. All other parameters must
be specified.

If you are unfamiliar with projections, try the :ref:`util_p2g_grid_helper` script.

# grid_name,proj4,proj4_str,width,height,pixel_size_x,pixel_size_y,origin_x,origin_y

 #. **grid_name**:
     A unique grid name describing the behavior of the grid. Grid names should not contain spaces.
 #. **proj4**:
     A constant value, "proj4" without the quotes. This tells the software
     reading the configuration file that this grid is a PROJ.4 grid.
 #. **proj4_str**:
     A PROJ.4 projection definition string. Some examples can be found in the
     :doc:`grids` list, but for more information on possible parameters see
     `PROJ.4 GenParams <http://trac.osgeo.org/proj/wiki/GenParms>`_. Note that
     compatiblity with certain PROJ.4 string components may be dependent on the
     version of the PROJ.4(pyproj) library that Polar2Grid uses, so testing
     should be done to verify that your string works as expected.
 #. **width**:
     Width of the grid in number of pixels. This value may be 'None' if it
     should be dynamically determined. Width and height must both be specified
     or both not specified.
 #. **height**:
     Height of the grid in number of pixels. This value may be 'None' if it
     should be dynamically determined. Width and height must both be specified
     or both not specified.
 #. **cell_width**:
     Size of one pixel in the X direction in grid units. Most grids are in
     metered units, except for ``+proj=latlong`` which expects degrees.
 #. **cell_height**:
     Size of one pixel in the Y direction in grid units (**MUST** be negative).
     Most grids are in metered units, except for ``+proj=latlong`` which expects degrees.
 #. **origin_x**:
     The grid's top left corner's X coordinate in grid units. Most grids are in
     metered units, except for ``+proj=latlong`` which expects degrees.
     This can be specified in degrees by using the "deg" suffix.
     This value may be 'None' if it should be dynamically determined.
     X and Y origin coordinates must both be specified or both not specified.
     For help with converting lon/lat values into X/Y values see the
     documentation for the utility script :ref:`util_p2g_proj`.
 #. **origin_y**:
     The grid's top left corner's Y coordinate in grid units. Most grids are in
     metered units, except for ``+proj=latlong`` which expects degrees.
     This can be specified in degrees by using the "deg" suffix.
     This value may be 'None' if it should be dynamically determined.
     X and Y origin coordinates must both be specified or both not specified.
     For help with converting lon/lat values into X/Y values see the
     documentation for the utility script :ref:`util_p2g_proj`.
