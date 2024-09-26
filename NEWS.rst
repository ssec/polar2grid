Release Notes
=============

Version 3.2.0 (unreleased)

* Change default visible band output to apply '/ cos(SZA)'. Use '--normalized-radiances' for old behavior.

Version 3.1.0 (2024-08-13)
--------------------------

* Support for additional VIIRS EDRs, including

  * Aerosol Optical Depth (AOD)
  * Cloud Top Height and Cloud Top Temperature
  * Surface Reflectances, including True Color
  * Vegetation Indices (NDVI, EVI)

* Support added for FY-3E MERSI-LL instrument
* Re-organization of software directories
* Optimizations
* Bug fixes

Version 3.0.0 (2023-02-21)
--------------------------

* New Implementation "polar2grid.sh -r <reader> -w <writer>"
* Reader name changes and replacements
* Writer name changes
* NOAA20 output file names standardized to "noaa20" prefix
* Alpha Band now included as default. Use ``--fill-value 0`` to not include
* Specify number of CPU's to use ``--num-workers <num>``
* ``--list-products`` and ``--list-product-all`` now available.
* Scaling ".ini" files no longer supported. Replaced with ".yaml"
* Longer list of updates included in the documentation

Version 2.3.0 (2020-01-13)
--------------------------

* Add FY-3C VIRR reader
* Add MERSI-2 reader
* Add VIIRS EDR Flood reader
* Add VIIRS EDR Active Fire reader
* Add "overlay.sh" script for overlaying active fire products
* Add '--borders-width' flag to "add_coastlines.sh"
* Fix AVHRR reader not masking bad 0 values
* Fix MIRS reader not using valid range properly

Version 2.2.1 (2018-04-27)
--------------------------

* Fix CREFL reader not reading negative reflectances
* Fix ratio sharpening calculating bad ratios for dark or invalid regions
* Fix VIIRS and MODIS false color by using the green band for sharpening
* Fix AMSR2 L1B scaling for PNG creation (`amsr2_png.ini`)
* Fix NinJo writer not using backend config command line option

Version 2.2 (2017-12-14)
------------------------

* Phase out legacy `<reader>2<writer>.sh` scripts and replace with `polar2grid.sh <reader> <writer>` implementation.
  Although the legacy scripts are still supported in Version 2.2, they are no longer documented.
* Add new AWIPS NetCDF writer "scmi".
* Add new grid definitions for 300m, 750m and 1km AWIPS SCMI tiled sectors LCC, Polar, Mercator, and Pacific.
* Add ACSPO SST reader.
* Add CLAVR-x Cloud Product reader.
* Fix scaling sometimes using the wrong configuration on certain platforms.
* Fix MODIS navigation calculations over the prime meridian.
* Add 'hncc_dnb' VIIRS product.
* Add JPSS-1/NOAA-20 support.

Version 2.1 (2016-11-25)
------------------------

* Start using Pytroll SatPy library for various features
* Phasing out of legacy <reader><writer>.bash scripts and replacing with polar2grid.sh <reader> <writer> implementation.
* Add ability to output float geotiffs
* Add ability to store geotiff tiles instead of strips
* Fix fornav bug for non-float inputs (unused in most cases)
* Add `add_colormap.sh` script for adding color tables to geotiffs
* Add `add_coastlines.sh` script for adding borders, coastlines, rivers, etc to geotiffs
* Add basic NUCAPS reader (via SatPy)
* Add VIIRS L1B reader (via SatPy)
* Add AMSR2 L1B reader (via SatPy)
* Add MIRS reader
* Change default `fornav-d` flag in most glue scripts to `1`
* Adjust true/false color scaling to be more continuous (similar result)
* Add AWIPS Puerto Rico Grid (210)
* Add `polar_alaska` dynamic grid
* New version of ShellB3 for C/python dependencies
* Fix geotiff geotransform to fix "off by half-pixel" bug.

Roadmap to Version 3.0
----------------------

* Collaboration with the Pytroll project and the creation of the new SatPy
  library will result in large internal changes to Polar2Grid.

    * SatPy is a replacement for the internals of Polar2Grid and a replacement
      for the Pytroll mpop package.
    * Migrate Polar2Grid frontends to SatPy readers.
    * Use SatPy for resampling and output writers, not just some readers.
    * Rename frontends to readers, backends to writers, products to datasets.
    * The remaining roadmap bullets are subject to change based on the Pytroll/Polar2Grid merger.

* Create new grid file format for more flexibility

* Allow resampling parameters to be configured based on dataset identifiers (satellite, instrument, etc)

* Further fornav updates

  * Move all module logic to C++ and remove cython dependency for this module (simple one function cython wrapper should be easy to remove)
  * Try rewriting in either opencl or use openmp for multiprocess work, but we're getting to the point that fornav is not the slowest part of fornav (intermediate disk use)

* Consider linking directly to PROJ.4 C library for ll2cr (removing pyproj dependency for ll2cr) to make it faster

* Update rescaling with cython wrapper (test performance before committing to this)

  * Needs change of clipping and masking logic so that its a decorator and can be easily excluded from cython code (which would use internal logic for those steps)

* Add proper handling for product data being kept in memory (should speed up quite a few things)

  * For better handling of in-memory data, should either let the user choose or determine it based on available memory
  * Frontend's could choose logical default (VIIRS should probably write to disk, DR-RTV should stay in memory)
  * Glue script can use memory analysis to come up with default but can be forced by command line argument

* Python 3 Compatibility

Version 2.0.1 (2015-10-19)
--------------------------

* Fixed small bug in ll2cr where NaNs in navigation would cause a dynamic grid to never "fit"

Version 2.0.0 (2015-10-13)
--------------------------

* Rewrite of entire internal structure and behavior of polar2grid (Frontends, Backends, Remapping)
* Most frontends (VIIRS, MODIS, etc) are filename independent and try to determine type of file by internal structure
* Frontends now do operations based on what "products" are requested and return a "scene" object
* The `polar2grid.core.meta` module is added to provide structure to intermediate steps (Frontend -> Remap -> Backend) with the classes it offers
* Backends now operate on a gridded scene as a whole (with option for operating on one product at a time for some backends)
* A compositor role was added to provide a more flexible method of creating true/false color and other composited images
* ll2cr rewritten in python and cython (C-like python) to be faster and more accurate
* Grid determination has been essentially removed since "data fits in grid" decisions don't make sense unless you are in projection/grid space (ll2cr serves this purpose now)
* fornav has been rewritten to be accessed directly from python. The ms2gt version of fornav is no longer used.
* The ms2gt version of fornav was also modified to be faster and is still destributed with the software bundle (for this release only).
* GPD grids and support for them has been removed. PROJ.4 is more flexible, more widely used, and can actually support the AWIPS grids better.
* Python setup.py files updated to better meet common practice of other python projects (READMEs, classifiers, etc)
* Major changes to rescaling so that it can be specified independent of output data type and "increment_by_one"
* Removed AWIPS I support due to National Weather Service using AWIPS II from now on
* Added basic ACSPO and MIRS frontends
* Added HDF5 backend

Version 1.2.0 (2014-08-16)
--------------------------

* Fixed VIIRS CREFL C code and added custom version to repository (viirs_crefl)
* Added ability to use 'deg' units on grid origin definitions
* Latlong grids use degrees instead of radians (affects grid configurations and intermediate values in code)
* Added `wgs84_fit_250` grid
* AWIPS grids "fixed" to actually align properly in AWIPS. The grid specification says ellipsoid earth, but my results say spherical.

Version 1.1.7 (2013-07-07)
--------------------------

* Non-TC geolocation used as backup option for VIIRS Frontend
* Fixed major bug when creating true colors (Issue #81). If the high resolution data resolved to a different dynamic grid than the low resolution data then a true color could not be made.

Version 1.1.6 (2013-05-31)
--------------------------

* Fixed frontends handling of symbolic links for files

Version 1.1.5 (2013-05-28)
--------------------------

* Various CREFL fixes
* Added MODIS geotiffs
* Added MODIS 250m bands

Version 1.1.0 (2013-02-13)
--------------------------

* Added MODIS Frontend (limited number of bands)
* Added CREFL Frontend (including true color glue script)
* Changed default geotiff data type to unsigned 8-bit integer
* Added option to provide user created grid configuration files
* NinJo backend added for DWD added

Version 1.0.0 (2013-01-25)
--------------------------

* Object oriented Frontend, Backend, and Rescaling
* Python version of ll2cr (still uses ms2gt fornav)
* Geotiff Backend
* Start of developer's guide in documentation
