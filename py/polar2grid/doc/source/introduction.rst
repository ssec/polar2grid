Introduction
============

Overview
--------

.. include:: overview.rst

Software Design
---------------

Polar2Grid has a modular design operating on the idea of satellite “products”
or "datasets"; data observed by a satellite instrument. These products can be
any type of raster data, such as temperatures, reflectances, radiances, or
any other value that may be recorded by or calculated from an instrument.
There are 4 main steps or components involved when working with these
products in Polar2Grid:
reading, writing, compositing, and remapping.
Polar2Grid makes it possible to access and configure these steps via simple
bash scripts. The script that "glues" these steps together is
``polar2grid.sh`` and creates gridded versions of the user swath products
provided to it. More information on accessing Polar2Grid's features and
running its scripts can be found in the :doc:`getting_started` section
or the examples following each reader section. Note that although an
example may be written for a specific reader the same operations can
be applied to all readers unless mentioned otherwise.

For more low-level information on the design and responsibility of each
component see the :doc:`design_overview` Appendix.

.. graphviz::

    digraph glue_flow {
        rankdir = LR;
        node [shape = rectangle, fillcolor="#C3DCE7:white", gradientangle="90.0", style="filled"];
        "Reader" -> "Remapper";
        "Remapper" -> "Writer";
        "Remapper" -> "Compositors" [style=dashed];
        "Compositors" -> "Writer" [style=dashed];
    }

.. note::

    Compositors and how they are configured will be changing in future
    versions of Polar2Grid. Due to this they are no longer documented in this
    document.

What's New?
-----------

Polar2Grid Version 2.1 is now available. Changes in this
version include:

.. include:: NEWS.rst
    :start-line: 7
    :end-line: 22

For more details on what's new in this version and past versions see the
`Release Notes <https://raw.githubusercontent.com/davidh-ssec/polar2grid/master/NEWS.rst>`_
in the github repository.

System Requirements
-------------------

System requirements for the Polar2grid software are as follows:
 * Intel or AMD CPU with 64-bit instruction support
 * 8 GB RAM (minimum)
 * CentOS 6 64-bit Linux (or other compatible 64-bit Linux distribution)
 * 3 GB disk space (minimum)
 * GLIBC version 2.7 or higher (execute “/lib64/libc.so.6” to find the version number)

Linux terminal commands included in these instructions assume the bash shell is used.

License and Disclaimer
----------------------

Original scripts and automation included as part of this package are
distributed under the
:download:`GNU GENERAL PUBLIC LICENSE agreement version 3 <../../../../COPYING>`.
Software included as part of this software package are copyrighted
and licensed by their respective organizations, and distributed consistent
with their licensing terms.

The University of Wisconsin-Madison Space Science and Engineering
Center (SSEC) makes no warranty of any kind with regard to the CSPP and/or
IMAPP Polar2Grid software or any accompanying documentation, including but
not limited to the implied warranties of merchantability and fitness for a
particular purpose. SSEC does not indemnify any infringement of copyright,
patent, or trademark through the use or modification of this software.

There is no expressed or implied warranty made to anyone as to the
suitability of this software for any purpose. All risk of use is assumed by
the user. Users agree not to hold SSEC, the University of Wisconsin-Madison,
or any of its employees or assigns liable for any consequences resulting from
the use of the CSPP and/or IMAPP Polar2Grid software.

