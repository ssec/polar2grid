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

To save on space usage for github the AWIPS NetCDF templates were not included
in the svn to git conversion (via the "--exclude '.*\.nc'" command line flag).
For proper execution of polar2grid from the git repository these files will
have to be downloaded and placed in the
``py/polar2grid/polar2grid/grids/`` directory.  These can be downloaded from
the following location:

    * http://www.secc.wisc.edu/software/polar2grid/_downloads/grid211e.nc
    * http://www.secc.wisc.edu/software/polar2grid/_downloads/grid211w.nc
    * http://www.secc.wisc.edu/software/polar2grid/_downloads/grid203.nc
    * http://www.secc.wisc.edu/software/polar2grid/_downloads/grid204.nc

Note that since these are not in version control through git, there is no
easy way to tell if the files have changed through github.

