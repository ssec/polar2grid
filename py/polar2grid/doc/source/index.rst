.. polar2grid documentation master file, created by
   sphinx-quickstart on Thu Apr 19 23:17:38 2012.

Polar2Grid
==========

Polar2Grid is a set of command line tools for extracting swath data from
earth-observing satellite instruments, remapping it to uniform grids,
and writing that gridded data to a new file format.
Polar2Grid was created by scientists and software developers at the
`SSEC <http://www.ssec.wisc.edu>`_. It is distributed as part of the
`CSPP <http://cimss.ssec.wisc.edu/cspp/>`_ and
`IMAPP <http://cimss.ssec.wisc.edu/imapp>`_ projects for
processing of data received via direct broadcast antennas. Although
Polar2Grid was created to serve the direct
broadcast community, it can be used on most archived data files.

The features provided by Polar2Grid are accessible via bash scripts and binary
command line tools. This is meant to give scientists an easy way to use and
access features that typically involve complicated programming interfaces.

Linux terminal commands included in these instructions assume the bash shell
is used.

Polar2Grid Version 2.1 is now available. For a description of what's new see
the :doc:`NEWS` section.

.. only:: not html

    `Documentation Website <http://www.ssec.wisc.edu/software/polar2grid/>`_

`GitHub Repository <https://github.com/davidh-ssec/polar2grid>`_

`Contact Us <http://cimss.ssec.wisc.edu/contact-form/index.php?name=CSPP%20Questions>`_

.. note::

    A collaboration between the Polar2Grid and PyTroll team will change a
    majority of the low-level code in future versions of Polar2Grid.
    However, the bash scripts will still be available to provide the same
    functionality with which users are familiar.

.. toctree::
    :maxdepth: 1
    :numbered:

    disclaimer
    system_requirements
    installation
    design_overview
    examples/index
    getting_started
    frontends/index
    remapping
    backends/index
    compositors
    rescaling
    utilscripts
    NEWS
    grids
    custom_grids
    glossary

.. only:: html

    Developer's Guide
    -----------------

    .. toctree::
        :maxdepth: 1
        :numbered:

        Introduction <dev_guide/index>
        dev_guide/dev_env
        dev_guide/swbundle
        dev_guide/json_input

    Indices and tables
    ------------------

    * :ref:`genindex`
    * :ref:`modindex`
    * :ref:`search`


