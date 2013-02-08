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

The grids module requires 1 configuration file to define the information about
each grid. This file can be found in the source
`here <https://github.com/davidh-ssec/polar2grid/tree/master/py/polar2grid/polar2grid/grids/grids.conf>`_.

At the time of this writing the grids module's only way of receiving
alternative configuration files is through environment variables. The API
allows for grids to be added, but it is up to :term:`glue scripts` to provide
that functionality to the user.

.. envvar:: POLAR2GRID_GRIDS_CONFIG

    The environment variable set to the path to the grid configuration file.
    See `grids.conf <https://github.com/davidh-ssec/polar2grid/tree/master/py/polar2grid/polar2grid/grids/grids.conf>`_
    for formatting details. The value of this should be an absolute path 
    (starting with a '/').

Grid corners are used during :term:`grid determination` to define a polygon
describing the grid. PROJ.4 grids' corners are calculated when needed, but
GPD grids must have their corners specified in the configuration file.

Understanding the grids module
------------------------------

The grids module's main points of access is the
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


