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

    Polar2Grid Version 3.1 is now available. This is a minor
    update that includes support for more VIIRS Science Products.

    Included in this release:

    .. include:: NEWS.rst
        :start-line: 6
        :end-line: 17

    For more details on what's new in this version and past versions see the
    `Polar2Grid Release Notes <https://raw.githubusercontent.com/ssec/polar2grid/main/NEWS.rst>`_
    in the github repository.

.. ifconfig:: is_geo2grid

    Included in this release:

    .. include:: NEWS_GEO2GRID.rst
        :start-line: 5
        :end-line: 18

    For more details on what's new in this version and past versions see the
    `Geo2Grid Release Notes <https://raw.githubusercontent.com/ssec/polar2grid/main/NEWS_GEO2GRID.rst>`_
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
    * Rocky 8 or Rocky 9 64-bit Linux (or other compatible 64-bit Linux distribution)
    * 10 GB disk space (minimum)

    For a more demanding processing load, like realtime generation of all
    GOES-16 ABI channels, true color, and natural color RGB images at full
    resolution, a system should have at least:

    * Intel or AMD CPU with 64-bit instruction support (20+ cores - 2.4GHz)
    * 64 GB RAM (minimum)
    * Rocky 8 or Rocky 9 64-bit Linux (or other compatible 64-bit Linux distribution)
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
    | GOES ABI         |    2m45s            |    29s          |         16s                 |
    +------------------+---------------------+-----------------+-----------------------------+
    | AHI HSD          |    3m20s            |    N/A          |         33s                 |
    +------------------+---------------------+-----------------+-----------------------------+
    | MTG FCI*         |    2m32s            |    N/A          |         50s                 |
    +------------------+---------------------+-----------------+-----------------------------+
    | AHI HimawariCast |      24s            |    N/A          |         12s                 |
    +------------------+---------------------+-----------------+-----------------------------+
    | GEO-KOMPSAT AMI  |    2m36s            |    N/A          |         14s                 |
    +------------------+---------------------+-----------------+-----------------------------+
    | FY4 AGRI         |    5m45s            |    N/A          |         30s                 |
    +------------------+---------------------+-----------------+-----------------------------+

       \* Using preliminary test data.

.. ifconfig:: not is_geo2grid

    System requirements for the |project| software are as follows:

    * Intel or AMD CPU with 64-bit instruction support (2+ cores - 2.4GHz)
    * 16 GB RAM (minimum)
    * Rocky 8 or Rocky 9 64-bit Linux (or other compatible 64-bit Linux distribution)
    * 5 GB disk space (minimum)

    Improved Execution Times
    -------------------------

    We continue to work to improve the efficiencies of Polar2grid.  The table
    below presents a comparison of the unix `real` time required to create
    VIIRS and MODIS imager GeoTIFF files for the given segments of data in the default
    WGS84 projection. In these examples, the default 4 computer threads were used in the
    Version 3.1 executions. Execution times decrease when fewer bands and smaller data
    segments are processed. The table compares the execution times using Polar2Grid Version
    3.1 with with those of Version 2.3.

    **Table of Execution Times for Creating GeoTIFF Default Projection Images**

    +------------------+-----------------+-----------------+------------------------+-----------------------+
    |**Instrument**    |**Polar2Grid**   |**Polar2grid**   |**Polar2Grid2 V2.3 All**|**Polar2Grid V3.1 All**|
    |**Input**         |**V2.3 True and**|**V3.1 True and**|**Bands plus True**     |**Bands plus True**    |
    |                  |**False Color**  |**False Color**  |**and False Color**     |**and False Color**    |
    +==================+=================+=================+========================+=======================+
    |**VIIRS SDR**     |                 |                 |                        |                       |
    |10 - 86 second    |    4m52s        |      1m35s      |      12m54s            |       4m23s           |
    |granules          |                 |                 |                        |                       |
    +------------------+-----------------+-----------------+------------------------+-----------------------+
    |**MODIS Level 1B**|                 |                 |                        |                       |
    |3 - 5 minute      |    4m11s        |      2m34s      |      9m08s             |      2m32s            |
    |granules          |                 |                 |                        |                       |
    +------------------+-----------------+-----------------+------------------------+-----------------------+

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
