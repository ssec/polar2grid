Introduction
============

Overview
--------

.. include:: overview.rst

Software Design
---------------

.. graphviz::

    digraph glue_flow {
        rankdir = LR;
        node [shape = rectangle, fillcolor="#C3DCE7:white", gradientangle="90.0", style="filled"];
        "Reader" -> "Remapper";
        "Remapper" -> "Writer";
        "Remapper" -> "Compositors" [style=dashed];
        "Compositors" -> "Writer" [style=dashed];
    }

|project| has a modular design operating on the idea of satellite “products”
or "datasets"; data observed by a satellite instrument. These products can be
any type of raster data, such as temperatures, reflectances, radiances, or
any other value that may be recorded by or calculated from an instrument.
There are 4 main steps or components involved when working with these
products in |project|:
reading, writing, compositing, and remapping.
|project| makes it possible to access and configure these steps with a simple
bash script called |script_literal| and other helper scripts.
More information on accessing |project|'s features and
running its scripts can be found in the :doc:`getting_started` section
or the examples following each reader section. Note that although an
example may be written for a specific reader the same operations can
be applied to all readers unless mentioned otherwise.

For more low-level information on the design and responsibility of each
component see the :doc:`design_overview` Appendix.

In |project| a majority of the functionality is provided by the open source
SatPy library created by the Pytroll group. More information on SatPy and
the capabilities it provides to python users can be found in the
`SatPy documentation <https://satpy.readthedocs.io/en/latest/>`_.

What's New?
-----------

.. ifconfig:: not is_geo2grid

    Polar2Grid Version 2.3 is now available. Changes in this
    version include:

    .. include:: NEWS.rst
        :start-line: 6
        :end-line: 14

    For more details on what's new in this version and past versions see the
    `Polar2Grid Release Notes <https://raw.githubusercontent.com/ssec/polar2grid/master/NEWS.rst>`_
    in the github repository.

.. ifconfig:: is_geo2grid

    Included in this release:

    .. include:: NEWS_GEO2GRID.rst
        :start-line: 6
        :end-line: 7

    For more details on what's new in this version and past versions see the
    `Geo2Grid Release Notes <https://raw.githubusercontent.com/ssec/polar2grid/master/NEWS_GEO2GRID.rst>`_
    in the github repository.


.. raw:: latex

    \newpage

System Requirements
-------------------

.. ifconfig:: is_geo2grid

    For minimal processing requirements (i.e. not realtime) the following
    system specifications are required:

    * Intel or AMD CPU with 64-bit instruction support (2+ cores - 2.4GHz)
    * 16 GB RAM (minimum)
    * CentOS 6 64-bit Linux (or other compatible 64-bit Linux distribution)
    * 5 GB disk space (minimum)

    For a more demanding processing load, like realtime generation of all
    GOES-16 ABI channels, true color, and natural color RGB images at full
    resolution, a system should have at least:

    * Intel or AMD CPU with 64-bit instruction support (20+ cores - 2.4GHz)
    * 64 GB RAM (minimum)
    * CentOS 6 64-bit Linux (or other compatible 64-bit Linux distribution)
    * 1 TB disk space (minimum for ~1 week of images, does not include long-term storage)

    Local storage (i.e. not network file systems) are preferred to limit any
    effect that network congestion may have. If additional satellites are
    included in the processing requirements then the above system requirements
    will need to be adjusted accordingly.

    Execution Times
    ---------------

    The following table provides execution time averages for creating all default
    GeoTIFF images at full spatial resolution for the given instrument and sector.
    Eight computer threads were used. The times are provided for the higher end
    system defined above. Execution times decrease when fewer bands and smaller
    regions are processed.

    **Table of Execution Times for Creating GeoTIFF default Images**
    (All bands plus true and natural color images)

    +------------------+---------------------+-----------------+-----------------------------+
    |**Instrument**    |**Full Disk Sector** |**CONUS Sector** |  **1000x1000 pixel subset** |
    +==================+=====================+=================+=============================+
    | GOES ABI         |    4m48s            |      42s        |         18s                 |
    +------------------+---------------------+-----------------+-----------------------------+
    | AHI HSD          |    7m01s            |    N/A          |         21s                 |
    +------------------+---------------------+-----------------+-----------------------------+
    | AHI HimawariCast |      36s            |    N/A          |         18s                 |
    +------------------+---------------------+-----------------+-----------------------------+

.. ifconfig:: not is_geo2grid

    System requirements for the |project| software are as follows:

    * Intel or AMD CPU with 64-bit instruction support (2+ cores - 2.4GHz)
    * 16 GB RAM (minimum)
    * CentOS 6 64-bit Linux (or other compatible 64-bit Linux distribution)
    * 5 GB disk space (minimum)

License and Disclaimer
----------------------

Original scripts and automation included as part of this package are
distributed under the
:download:`GNU GENERAL PUBLIC LICENSE agreement version 3 <../../LICENSE.txt>`.
Software included as part of this software package are copyrighted
and licensed by their respective organizations, and distributed consistent
with their licensing terms.

The University of Wisconsin-Madison Space Science and Engineering
Center (SSEC) makes no warranty of any kind with regard to the |cspp_abbr|
software or any accompanying documentation, including but
not limited to the implied warranties of merchantability and fitness for a
particular purpose. SSEC does not indemnify any infringement of copyright,
patent, or trademark through the use or modification of this software.

There is no expressed or implied warranty made to anyone as to the
suitability of this software for any purpose. All risk of use is assumed by
the user. Users agree not to hold SSEC, the University of Wisconsin-Madison,
or any of its employees or assigns liable for any consequences resulting from
the use of the |cspp_abbr| software.

