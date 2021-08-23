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

TODO

Configuring enhancements
------------------------

TODO

Add documentation
-----------------

Create a new restructuredtext document at
``doc/source/readers/<p2g_reader_name>.rst``. Add the name of this document
to the table of contents in ``doc/source/readers/index.rst``.

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