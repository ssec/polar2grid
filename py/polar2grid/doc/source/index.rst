.. polar2grid documentation master file, created by
   sphinx-quickstart on Thu Apr 19 23:17:38 2012.

Polar2Grid
==========

Polar2Grid is a set of tools for extracting swath data from earth-observing satellite instruments,
remapping it to uniform grids, and writing that gridded data to a new file format.
Polar2Grid was created by scientists and software developers at the Space Science and Engineering Center (SSEC) at
the University of Wisconsin - Madison. It is distributed as part of the
`Community Satellite Processing Package (CSPP) <http://cimss.ssec.wisc.edu/cspp/>`_ for
processing of data received via direct broadcast (DB) antennas. Although Polar2Grid was created for DB, it can be used
on most archived (non-DB) data files.

The features provided by Polar2Grid are accessible via bash scripts, command line tools, and a set of python packages.
These methods give scientists and programmers options for using Polar2Grid in a way most comfortable to them.

Original scripts and automation included as part of this package are
distributed under the
:download:`GNU GENERAL PUBLIC LICENSE agreement version 3 <../../../../COPYING>`.
Binary
executable files included as part of this software package are copyrighted
and licensed by their respective organizations, and distributed consistent
with their licensing terms.

.. Documentation <http://www.ssec.wisc.edu/software/polar2grid/>

`GitHub Repository <https://github.com/davidh-ssec/polar2grid>`_

`Contact Us <http://cimss.ssec.wisc.edu/contact-form/index.php?name=CSPP%20Questions>`_

Contents
--------

.. toctree::
    :maxdepth: 1
    :numbered:

    installation
    design_overview
    getting_started
    frontends/index
    remapping
    backends/index
    compositors/index
    rescaling
    utilscripts
    NEWS
    glossary

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
   
    api/polar2grid
    api/polar2grid.viirs
    api/polar2grid.modis
    api/polar2grid.crefl
    api/polar2grid.core


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


