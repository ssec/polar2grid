Grids
=====

The :py:mod:`grids <polar2grid.grids.grids>` module is where grid information
is made available to :term:`glue scripts` and developers. Currently, you can
provide grids with PROJ.4 projections to the polar2grid system.
Grids can be static, meaning the grid definition specifies the
projection, pixel size, origin, and grid size. Grids can also be
dynamic, meaning that only some grid defining parameters are specified.
An example of a dynamic grid is the :ref:`wgs84_fit` grid. This grid
does not have an origin or grid size specified, which tells the remapping
components of Polar2Grid to calculate these values from the data.

Adding your own grid
--------------------

Polar2Grid allows users to define and add their own grids for remapping in
any glue script. The Polar2Grid package provides a default set of grids that
can be specified on the command line with most :term:`glue scripts`.
This built-in configuration file can be found in the source on github
`here <https://github.com/davidh-ssec/polar2grid/tree/master/py/polar2grid/polar2grid/grids/grids.conf>`_.
If you wish to add your own grids as a replacement for or in addition to the
provided set you'll have to make your own grid configuration file.

Glue scripts provide the :option:`--grid-configs` command line option
to specify user-created grid configurations. Multiple files can be listed with this command
line flag (space separated). If you would like to add your grids in addition
to the package provided set of grids you must specify "grids.conf" as one of
these configuration files.

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

.. note::

    The decision of whether a grid is supported or not is ultimately up to
    :doc:`the backend <../backends/index>` used by a glue script.
    Check the :doc:`../backends/index` section for your specific backend.

.. note::

    Configuration files are loaded in the order specified. If a grid name
    is used more than once, the last one loaded is used.

.. _grid_configuration_format:

Grid Configuration File Format
------------------------------

Example Grid Configuration File: :download:`grid_example.conf <../../../../../swbundle/grid_configs/grid_example.conf>`

Grid configuration files are comma-separated text files.
Comments can be added by prefixing lines
with a ``#`` character. Spaces are allowed between values to make aligning columns
easier. The following describes each column that must
be specified (in order). A sample header comment is also provided to add to your
grid configuration file for better self-documentation. The example grid
configuration file linked to above can also be found in the software bundle in
``swbundle/grid_configs/grid_example.conf``.

As mentioned at the top of this page, grids can be
dynamic or static. Dynamic grids may have either grid size parameters
or grid origin parameters or both unspecified. All other parameters must
be specified.

If you are unfamiliar with projections, try the :ref:`util_p2g_grid_helper` script.

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
