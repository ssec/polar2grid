Custom Grids
============

|project| provides a set of grids to suit most use cases, but sometimes
these grids are not enough. This is why |project| allows users
to create their own custom grids.

Grids can be static, meaning the grid definition specifies the
projection, pixel size, origin, and grid size. Grids can also be
dynamic, meaning that only some grid defining parameters are specified.
An example of a dynamic grid is the :ref:`grid_wgs84_fit` grid. This grid
does not have an origin or grid size specified, which tells the remapping
components of |project| to calculate these values from the data.

Adding your own grid
--------------------

If you wish to add your own grids as a replacement for or in addition to the
provided set you'll have to make your own grid configuration file.
The instructions below describe how to create your own configuration file
and how it can be provided to |script_literal|:

1. Create a text file named something ending in ".yaml" (ex. "my_grids.yaml").
   Open it for editing. The package includes a ``grid_configs`` directory
   where user configuration files can be stored.
2. Add an entry to this file for each grid you would like to add
   |project|. Follow the :ref:`grid_configuration_format` section below.
   The grid file is in the
   `YAML text format <https://en.wikipedia.org/wiki/YAML>`_.
3. Call the |script_literal| script and add the command line option
   ``--grid-configs grids.conf <your-file.yaml>``. The builtin grids
   in |project| are included when "grids.conf" is provided. If you would like
   only your grids and not the |project| provided grids don't include the
   "grids.conf" in the command line option.

|project| also includes a simple script that can generate the
required YAML text when provided with general information about the grid
you wish to create. See the :ref:`util_p2g_grid_helper` section.

.. note::

    Configuration files are loaded in the order specified. If a grid name
    is used more than once, the last one loaded is used.

.. _grid_configuration_format:

Grid Configuration File Format
------------------------------

.. note::

    The legacy ".conf" format is still supported for backwards compatibility,
    but should not be used for new grid definition files.

Example Grid Configuration File: :download:`grid_example.yaml <../../swbundle/grid_configs/grid_example.yaml>`

Grid configuration files follow the format used by the Satpy and Pyresample
Python libraries in their
:doc:`areas.yaml files <pyresample:howtos/geometry_utils>` and are in the
`YAML text format <https://en.wikipedia.org/wiki/YAML>`_.
Comments can be added by prefixing lines with a ``#`` character. There is an
example file provided in the |project| bundle at:

.. ifconfig:: not is_geo2grid

    ``$POLAR2GRID_HOME/grid_configs/grid_example.yaml``

.. ifconfig:: is_geo2grid

    ``$GEO2GRID_HOME/grid_configs/grid_example.yaml``

Grids can be dynamic or static. Dynamic grids have some amount of information
unspecified that will be filled in later at runtime using the provided input
geolocation data. The most common case for a dynamic grid is specifying only
"resolution", but not "shape" or any extent information. If enough information
is provided in the definition then a static grid is created which will always
be in the same location at the same resolution, but will process faster as
the other grid parameters don't need to be computed.

If you are unfamiliar with projections, try the :ref:`util_p2g_grid_helper` script.
One example of a grid is shown below.

.. code-block:: yaml

    my_211e:
      description: 'My LCC grid'
      projection:
        proj: lcc
        lat_1: 25
        lat_0: 25
        lon_0: -95
        R: 6371200
        units: m
        no_defs: null
        type: crs
      shape:
        height: 5120
        width: 5120
      resolution:
        dy: 1015.9
        dx: 1015.9
      upper_left_extent:
        x: -122.9485839789149
        y: 59.86281930852158
        units: degrees

This static grid is named ``my_211e`` and has the following parameters:

 #. **description**:
    Optional human-readable description of the grid. This is not currently
    used by |project|.
 #. **projection**:
    PROJ.4 parameters of the projection of the grid. Can also
    be specified as a string. Or as an EPSG code integer.
    In addition to the example grids file linked above, for more information
    on possible parameters see the
    `PROJ documentation <https://proj4.org/usage/projections.html>`_.
 #. **shape**:
    Number of pixels in each dimension.
 #. **resolution**:
    Resolution of each pixel in projection units (usually meters). This can
    also be specified in degrees by adding a ``units: degrees`` in this
    section.
 #. **upper_left_extent**:
    Location of the upper-left corner of the upper-left pixel of the grid. By
    default this is in projection units (usually meters), but is specified
    in degrees here with the extra ``units:`` parameter.
    Note this differs from the legacy ``.conf`` format which used the
    center of the upper-left pixel.

See the example grids file linked above for more examples and other available
parameters like **center** or **area_extent**.
