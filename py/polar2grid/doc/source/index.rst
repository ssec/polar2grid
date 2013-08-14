.. polar2grid documentation master file, created by
   sphinx-quickstart on Thu Apr 19 23:17:38 2012.

polar2grid
======================================

Polar2grid is a software package providing scripts, utilities, and a series
of functions and classes for reading
polar-orbiting satellite data, remapping or gridding that data, and writing
it to a file format to be used by other software. Polar2grid is mainly used
through one or more :term:`glue scripts <glue script>` that execute a common
sequence of
function calls known as ":term:`The Chain`". These functions being called act
as a toolbox for software developers to make their own scripts if the provided
:term:`glue scripts <glue script>` don't fit their needs.

Code repository: https://github.com/davidh-ssec/polar2grid

If you are a developer wishing to add your own frontend or backend please
see the :doc:`Developer's Guide <dev_guide/index>` for details on how to do so.

Original scripts and automation included as part of this package are
distributed under the
:download:`GNU GENERAL PUBLIC LICENSE agreement version 3 <../../../../COPYING>`.
Binary
executable files included as part of this software package are copyrighted
and licensed by their respective organizations, and distributed consistent
with their licensing terms.

Contents
--------

.. toctree::
    :maxdepth: 2
    :numbered:

    installation
    How polar2grid works <chain>
    glue_scripts/index
    frontends/index
    backends/index
    rescaling
    utilscripts
    release_notes
    constants
    glossary
    tests/index

Grids
-----

.. toctree::
    :maxdepth: 3

    grids

Developer's Guide
-----------------

.. toctree::
    :maxdepth: 2
    :numbered:

    Introduction <dev_guide/index>
    dev_guide/dev_env
    dev_guide/glue_scripts
    dev_guide/frontends
    dev_guide/grids
    dev_guide/remapping
    dev_guide/backends
    dev_guide/rescaling
    dev_guide/swbundle

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


