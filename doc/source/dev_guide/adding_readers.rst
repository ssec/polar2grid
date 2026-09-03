Adding Readers
==============

The below sections will describe what has to be done to add a new reader
to Polar2Grid and Geo2Grid. The quick overview is:

1. Add the reader to Satpy if it doesn't already exist.
2. Add a "wrapper" module in the "polar2grid" python package.
3. Add any reader-specific resampling and enhancement configurations if
   needed.
4. Add documentation to the sphinx documentation.

Satpy readers
-------------

Polar2Grid and Geo2Grid use readers defined in the Satpy python library. The
only time a reader should not be included in Satpy is if it would be a burden
to maintain for the Satpy team and/or it will not be used by the majority of
Satpy users.

To add a reader to Satpy, follow the instructions in the
`Satpy documentation <https://satpy.readthedocs.io/en/latest/dev_guide/custom_reader.html>`_.
This process will require a GitHub account, making a pull request, writing
Python code that uses Xarray and dask, and writing unit tests using the
pytest package.

Add wrapper reader module
-------------------------

By default, Polar2Grid and Geo2Grid are able to use any reader that is in
Satpy. However, in most cases we want to define a set of default products to
load and possibly rename the products. We may also want to provide additional
command line flags to simplify requesting specific sets of products.

1. Create a ``polar2grid/readers/<satpy_reader_name>.py``.
2. Add the license header to the top of the module. See other readers for
   examples.
3. Add a module docstring that includes a table of the products that P2G/G2G
   supports. See other reader modules for examples.
4. Import ``from ._base import ReaderProxyBase`` and create a subclass of it
   called ``class ReaderProxy(ReaderProxyBase)``. This class must be named
   ``ReaderProxy`` so it can be discovered from the main scripts.
5. In this ``ReaderProxy`` class define any customizations needed by this
   reader. See :class:`polar2grid.readers._base.ReaderProxyBase` for more
   information.
6. Define a function to add custom command line arguments:

   .. code-block:: python

       from argparse import ArgumentParser, _ArgumentGroup
       from typing import Optional

       def add_reader_argument_groups(
           parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
       ) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:

           if group is None:
               group = parser.add_argument_group(title="<reader name> Reader")
           # Add argparse arguments here by doing group.add_argument(...)
           return group, None

   See other readers for examples of complex command line arguments. The second
   ``None`` that is returned is for rare cases when keyword arguments need to
   be passed to the ``Scene.load`` method of Satpy (besides the list of
   products). This is not currently used.

Configure resampling
--------------------

Polar2Grid and Geo2Grid decide how each product is resampled with their own
decision tree, loaded from ``polar2grid/etc/resampling.yaml``. Only this
configuration file is specific to these projects; the resampling algorithms
themselves and the keyword arguments they accept come from Satpy and are
described in :doc:`satpy:resample`. See :doc:`../remapping` for the
user-level description of the algorithms these projects offer.

Most new readers do not need an entry in this file. Without one, swath-based
products are resampled with the ``nearest`` neighbor algorithm and gridded
(area-based) products use the defaults for whatever target grid is being
used. Add an entry only when those defaults produce a poor image for this
reader's data:

.. code-block:: yaml

    resampling:
      my_reader_all_products:
        reader: my_reader
        area_type: swath
        resampler: ewa
        kwargs:
          weight_delta_max: 40.0
          weight_distance_max: 2.0
      my_reader_cloud_mask:
        reader: my_reader
        name: cloud_mask
        area_type: swath
        resampler: nearest

Each section has a unique name of your choosing, one or more metadata keys to
match on, and the options to use when it matches. Sections are matched the
same way as the enhancement sections described in :doc:`satpy:enhancements`,
with the most specific match winning, but the keys available here are
``name``, ``reader``, ``platform_name``, ``sensor``, ``area_type``,
``standard_name``, and ``units``. The ``area_type`` key is either ``swath``
or ``area`` and is determined from the data at runtime. Note that ``name`` is
the Satpy product name, not any Polar2Grid alias defined in the wrapper
module.

The options that can be set for a match are:

``resampler``
    The resampling algorithm to use (ex. ``nearest``, ``ewa``, ``native``).
``kwargs``
    Keyword arguments passed on to the resampling algorithm.
``default_target``
    The grid to resample to when the user does not specify one with ``-g``.
    When not set this is ``wgs84_fit`` for Polar2Grid and the finest
    resolution area of the input data (``MAX``) for Geo2Grid.

Anything the user provides on the command line (``--method`` and the
resampling options that go with it, or ``-g``) takes priority over these
values.

Configuring enhancements
------------------------

Enhancements scale, and optionally colorize, a product right before it is
written to an image. This is entirely a Satpy feature: the YAML format, the
``operations`` list, the enhancement functions available, and the rules for
how a section is matched to a particular product are all described in
:doc:`satpy:enhancements`. Only the project-specific parts are covered here.
:doc:`../enhancements` is the user-level description.

Polar2Grid and Geo2Grid add their own configuration directory
(``polar2grid/etc/``) to Satpy's config path, so a new enhancement is added
by editing ``polar2grid/etc/enhancements/generic.yaml`` or the
``<sensor>.yaml`` file for this reader's instrument, creating that sensor
file if it does not exist yet. A new reader needs an entry only if one of its
products would otherwise be scaled poorly or should be colorized:

.. code-block:: yaml

    enhancements:
      my_rain_rate:
        name: rain_rate
        sensor: my_sensor
        operations:
          - name: colorize
            method: !!python/name:polar2grid.enhancements.shared.colorize
            kwargs:
              palettes:
                - filename: colormaps/my_rain_rate.cmap
                  min_value: 0.0
                  max_value: 50.0

Two things differ from a plain Satpy configuration:

* The ``name`` being matched is the Satpy product name, not the Polar2Grid
  alias defined in the wrapper module. The ``sensor`` and ``platform_name``,
  on the other hand, are the Polar2Grid spellings; they are replaced with the
  aliases in ``polar2grid/utils/legacy_compat.py`` and ``polar2grid/glue.py``
  before the data is written.
* In addition to the Satpy enhancement functions there are Polar2Grid
  specific ones in the ``polar2grid/enhancements/`` package. Use
  ``polar2grid.enhancements.shared.colorize`` and
  ``polar2grid.enhancements.shared.palettize`` instead of the Satpy versions
  when the color table is one of the files in ``polar2grid/etc/colormaps/``;
  these versions also expand ``$POLAR2GRID_HOME`` and ``$GEO2GRID_HOME`` in a
  palette ``filename``.

See :doc:`../custom_config` for how users can supply their own configuration
directory to override any of this, and ``swbundle/example_enhancements/`` for
a complete example of one.

Add documentation
-----------------

Create a new restructuredtext document at
``doc/source/readers/<p2g_reader_name>.rst``. Add the name of this document
to the table of contents in ``doc/source/readers/index.rst``. That file uses
the ``toctree-filt`` directive, so prefix the entry with ``:polar2grid:`` or
``:geo2grid:`` if the reader is only used by one of the two projects. An
entry with no prefix is included in both.

If the reader is specific to one project, the new document must also be added
to the *other* project's ``exclude_patterns`` list in ``doc/source/conf.py``
(``polar2grid_excludes`` or ``geo2grid_excludes``). Both projects'
documentation is built in continuous integration with warnings treated as
errors, so a document that is in neither a table of contents nor the exclude
list fails the build with "document isn't included in any toctree".

Fill in the reader file with the following information:

.. code-block:: ReST

    <reader name> Reader
    ====================

    .. automodule:: polar2grid.readers.<reader_module>
        :noindex:

    Command Line Arguments
    ----------------------

    .. argparse::
        :module: polar2grid.readers.<reader_module>
        :func: add_reader_argument_groups
        :prog: polar2grid.sh -r <reader_name> -w <writer>
        :passparser:

    Examples:

    .. code-block:: bash

        polar2grid.sh -r <reader_name> -w geotiff -f <path to files>/<list of files>

Make sure to replace all instances of ``<reader_name>`` with the name of your
reader. The name of the script will also need to be changed if this reader is
specifically for Geo2Grid instead of Polar2Grid
(``polar2grid.sh`` -> ``geo2grid.sh``).

More examples can be added to show specific use cases or features of the reader
and the available command line arguments.

Other References
----------------

The reader is also mentioned in other places in addition to the above
documentation. The main thing is to add it to the list of readers for the
``-r`` flag. This is the ``_supported_readers`` function in the
``polar2grid/_glue_argparser.py`` module, which has one hardcoded list of
reader names for Polar2Grid and one for Geo2Grid. The reader still works if
it is left out, but users will not see it in ``--help``.

Depending on the reader, these may also need updating:

* ``READER_ALIASES`` in ``polar2grid/_glue_argparser.py`` if the reader
  should also be usable by a shorter or legacy name.
* ``DEFAULT_OUTPUT_FILENAMES`` in the ``polar2grid/writers/*.py`` modules if
  this reader's output filenames should differ from the defaults.
* ``doc/source/summary_table.rst`` (Polar2Grid) or
  ``doc/source/summary_table_geo2grid_readers.rst`` (Geo2Grid). These tables
  are maintained by hand.
* ``NEWS.rst`` or ``NEWS_GEO2GRID.rst`` so users hear about the new reader.
