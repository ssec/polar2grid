polar2grid
==========

polar2grid is a software package, mainly python, for converting polar
orbitting satellite data from various sources (VIIRS, MODIS, etc.) into
formats that are useable by meteorlogical visualization applications,
such as AWIPS, NINJO, etc.

Currently, polar2grid only works on converting a few VIIRS bands to
AWIPS-compatible NetCDF files.

SVN Conversion Notes
--------------------

The original repository included a "vendor" directory in the root repository
that was being used to store the vendor release of ms2gt.  The repository was
converted to git using "svn2git" which does not support this structure.
For now, the "vendor" directory is not included in the git repository although
it may be added later.

