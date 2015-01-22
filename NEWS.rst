Release Notes
=============

Roadmap to Version 2.1
----------------------

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

Version 2.0
-----------

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

Version 1.2
-----------

* Fixed VIIRS CREFL C code and added custom version to repository (viirs_crefl)
* Added ability to use 'deg' units on grid origin definitions
* Latlong grids use degrees instead of radians (affects grid configurations and intermediate values in code)
* Added `wgs84_fit_250` grid
* AWIPS grids "fixed" to actually align properly in AWIPS. The grid specification says ellipsoid earth, but my results say spherical.

Version 1.1
-----------

* Added MODIS Frontend (limited number of bands)
* Added CREFL Frontend (including true color glue script)
* Changed default geotiff data type to unsigned 8-bit integer
* Added option to provide user created grid configuration files
* NinJo backend added for DWD added

Version 1.0
-----------

* Object oriented Frontend, Backend, and Rescaling
* Python version of ll2cr (still uses ms2gt fornav)
* Geotiff Backend
* Start of developer's guide in documentation
