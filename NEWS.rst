Release Notes
=============

Current Version: 2.0.1 (2015-10-19)

Version 2.0 (2015-10-13)
------------------------

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
* Version 2.0.1 (2015-10-19)

  * Fixed small bug in ll2cr where NaNs in navigation would cause a dynamic grid to never "fit"

Roadmap to Version 2.1
----------------------

* Collaboration with the PyTroll project will change almost everything...again.

    * The PyTroll and Polar2Grid teams have been working on a new interface for the mpop package that will allow greater
      flexibility and easier use by Polar2Grid.
    * Most python code in Polar2Grid will be absorbed by mpop (either added or use existing).
    * The remaining roadmap bullets are subject to change based on the PyTroll/Polar2Grid merger.

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

Version 1.2 (2014-08-16)
------------------------

* Fixed VIIRS CREFL C code and added custom version to repository (viirs_crefl)
* Added ability to use 'deg' units on grid origin definitions
* Latlong grids use degrees instead of radians (affects grid configurations and intermediate values in code)
* Added `wgs84_fit_250` grid
* AWIPS grids "fixed" to actually align properly in AWIPS. The grid specification says ellipsoid earth, but my results say spherical.

Version 1.1 (2013-02-13)
------------------------

* Added MODIS Frontend (limited number of bands)
* Added CREFL Frontend (including true color glue script)
* Changed default geotiff data type to unsigned 8-bit integer
* Added option to provide user created grid configuration files
* NinJo backend added for DWD added
* Version 1.1.7 (2013-07-07)

  * Non-TC geolocation used as backup option for VIIRS Frontend
  * Fixed major bug when creating true colors (Issue #81). If the high resolution data resolved to a different dynamic grid than the low resolution data then a true color could not be made.

* Version 1.1.6 (2013-05-31)

  * Fixed frontends handling of symbolic links for files

* Version 1.1.5 (2013-05-28)

  * Various CREFL fixes
  * Added MODIS geotiffs
  * Added MODIS 250m bands

Version 1.0 (2013-01-25)
------------------------

* Object oriented Frontend, Backend, and Rescaling
* Python version of ll2cr (still uses ms2gt fornav)
* Geotiff Backend
* Start of developer's guide in documentation
