Grids
=====

|project| allows users to remap to one or more projected grids. A grid
defines the uniform geographic area that an output image covers. |project|
comes with various grids to choose from that should suit most users and their
use cases. Some grids are provided for specific writers (like Tiled AWIPS), but
can be used for other writers as well. Users can also specify their own 
custom grids. See the :doc:`custom_grids` documentation for help with this.

Provided Grids
--------------

Below are descriptions for a few of the grids provided with |project|.
For information on all of the grids provided by |project| see the
`Grids Configuration File <https://github.com/ssec/polar2grid/blob/main/polar2grid/grids/grids.conf>`_.

The grids' projections are defined using PROJ.4. Go to
the `PROJ documentation <https://proj4.org/usage/projections.html>`_
for more information on what each projection parameter means.

.. note::

    If the grid does not have a parameter specified it will be derived from the
    data during remapping.  This allows for grids that fit to the data (dynamic
    grids).

.. include:: grids_list.rst
