Release Notes
=============

Release notes for polar2grid's releases.

Future Plans
------------

 - More unit and integration tests

New in Version 1.1.0
--------------------

 - Added MODIS Frontend (limited number of bands)
 - Added CREFL Frontend (VIIRS and MODIS)
    - Includes glue script to make true color images (crefl2gtiff)
    - Optional sharpening depending on what bands were provided
 - NinJo backend for DWD added
 - Removed internal 'copy' of pylibtiff, polar2grid now depends on pylibtiff
 - Updated ms2gt makefiles to work on more systems
 - Made grids API object oriented (Cartographer)
 - Grid determination now uses polygon math (much faster)
 - Added command line option to add user created grid configuration files
 - :option:`viirs2gtiff -g` flag can now have 'all' specified and other forced grids
 - Changed behavior of forced grids, they are now preferred but not required to complete without error
 - Dynamic grids are not added during grid determination anymore
 - Simple unit tests added.
 - Fixed bug where AWIPS NetCDF files had doubles (64-bits) instead of 32-bit floats
 - Various other bug fixes

New in Version 1.0.0
--------------------

 - Major Release
 - Updated ms2gt to version 0.24 (customized to 0.24a)
 - Major interface changes (too many to note)
 - Object oriented Frontend, Backend, and Rescaler
 - Python version of ll2cr
 - Geotiff Backend
 - Start of a developer's guide
 - Bug fixes
 - New Tests:
    * p2g-v2g-ak-tests-1.0.0
    * p2g-v2g-econus-tests-1.0.0
 - Uses Tests:
    * p2g-v2a-ak-tests-1.0.3

New in Version 0.0.7
--------------------

 - Updated ms2gt to version 0.23
 - Updated known good test data due to algorithm change in ms2gt 0.23
 - Uses Tests:
    * p2g-v2a-ak-tests-1.0.2

New in Version 0.0.6
--------------------

 - Fixed plot_ncdata.sh for proper AWIPS NC plotting
 - Uses Tests:
    * p2g-v2a-ak-tests-1.0.1

New in Version 0.0.5
--------------------

 - First release
 - Basic viirs2awips functionality
 - Uses Tests:
    * p2g-v2a-ak-tests-1.0.0

