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

The grids module requires 2 configuration files to define the information about
each grid. Those files are known as the "grid configuration file" and the "grid
shapes configuration file". Both of these files and their any corresponding
gpd files can be found
`here <https://github.com/davidh-ssec/polar2grid/tree/master/py/polar2grid/polar2grid/grids>`_.

At the time of this writing the grids module's only way of receiving
alternative configuration files is through environment variables.

.. envvar:: POLAR2GRID_GRIDS_CONFIG

    The environment variable set to the path to the grid configuration file.
    See `grids.conf <https://github.com/davidh-ssec/polar2grid/tree/master/py/polar2grid/polar2grid/grids/grids.conf>`_
    for formatting details.

.. envvar:: POLAR2GRID_SHAPES_CONFIG

    The environment variable set to the path to the grid shapes configuration
    file. See
    `grid_shapes.conf <https://github.com/davidh-ssec/polar2grid/tree/master/py/polar2grid/polar2grid/grids/grid_shapes.conf>`_
    for formatting details.

Except for dynamic PROJ.4 grids, grids must be specified in both configuration
files. The shapes configuration file will be used by grid determination as a
bounding box for the grids being analyzed.

Understanding the grids module
------------------------------

The grids module's main point of access is the
:py:func:`polar2grid.grids.grids.get_grid_info` function. This function
returns a dictionary that provides information that can be used by the
polar2grid remapping process or polar2grid backends is needed. The 
``grid_info`` dictionaries are different depending on the kind of grid.

One important
piece of information is the ``grid_kind`` key which is set to either the
:data:`GRID_KIND_GPD` constant or :data:`GRID_KIND_PROJ4` constant value.

TODO

