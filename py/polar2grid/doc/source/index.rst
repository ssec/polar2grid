.. polar2grid documentation master file, created by
   sphinx-quickstart on Thu Apr 19 23:17:38 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

polar2grid
======================================

polar2grid provides scripts, utilities, and library functions for reading
polar-orbitting satellite data, remapping or gridding that data, and writing
it to a file format to be used by other software. All
polar2grid "glue" scripts execute a series of function calls known as
"The Chain".  These functions being called act as a toolbox for software
developers to make their own scripts.  See :doc:`Advanced Topics <advanced>`
for more details if the basic documentation doesn't answer your questions.
If you are a developer wishing to add your own frontend or backend please
see the :doc:`Developer's Guide <dev_guide>` for details on how to do so.

Contents
--------

.. toctree::
    :maxdepth: 2
    :numbered:

    installation
    chain
    scripts
    frontends
    backends
    rescaling
    utilscripts
    dev_guide
    advanced
    release_notes

Grids
-----

.. toctree::
    :maxdepth: 2

    grids

API
---

.. toctree::
    :maxdepth: 3
   
    modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


