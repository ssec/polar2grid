.. polar2grid documentation master file, created by
   sphinx-quickstart on Thu Apr 19 23:17:38 2012.

Polar2Grid
==========

Polar2Grid is a set of tools for extracting swath data from earth-observing satellite instruments,
remapping it to uniform grids, and writing that gridded data to a new file format.
Polar2Grid was created by scientists and software developers at the
`SSEC <http://www.ssec.wisc.edu>`_. It is distributed as part of the
`CSPP project <http://cimss.ssec.wisc.edu/cspp/>`_ for
processing of data received via direct broadcast antennas. Although Polar2Grid was created to serve the direct
broadcast community, it can be used on most archived data files.

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

.. note::

    A collaboration between the Polar2Grid and PyTroll team will change a majority of the low-level code in
    future versions of Polar2Grid.
    However, the bash scripts will still be available to provide the same functionality with which users are familiar.

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
    compositors
    rescaling
    utilscripts
    NEWS
    grids
    glossary

Developer's Guide
-----------------

.. toctree::
    :maxdepth: 1
    :numbered:

    Introduction <dev_guide/index>
    dev_guide/dev_env
    dev_guide/grids
    dev_guide/swbundle
    dev_guide/json_input


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


