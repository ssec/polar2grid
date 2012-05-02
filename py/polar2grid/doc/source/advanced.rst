Advanced Topics
===============

Python Package Install
----------------------

If you would like more control over your python/polar2grid environment
you can install the polar2grid python package like any basic python egg:

    ``easy_install -f http://larch.ssec.wisc.edu/cgi-bin/repos.cgi polar2grid``

Installing polar2grid in this way does require, however, that the ms2gt
utilities ``ll2cr`` and ``fornav`` must be in your $PATH environment
variable.  The polar2grid python package also has the following prerequisite
packages:

    - numpy
    - h5py
    - netCDF4
    - matplotlib

Creating Software Bundle from Subversion Repository
---------------------------------------------------

Follow these steps to recreate the software bundle ``*.tar.gz`` file.

    1. Create the software bundle directory and change to it::

        mkdir polar2grid_swbundle_<version>
        cd polar2grid_swbundle_<version>

    2. Create binary directory::

        mkdir bin

    3. Download ms2gt, compile it, and link to the used utilities:

        Prerequisite - Make a ms2gt source package (from the development repository)::

            cd /path/to/repos/checkout/trunk/ms2gt/
            make tar
            mv ms2gt<ms2gt-version>.tar.gz /path/to/polar2grid_swbundle_<version>
            cd /path/to/polar2grid_swbundle_<version>

        Or you can download the .tar.gz file from here:
            http://www.ssec.wisc.edu/~davidh/polar2grid/ms2gt/

        Compile and link it::

            tar -xzf ms2gt<ms2gt-version>.tar.gz
            cd ms2gt
            make
            cd ..
            ln -s ../ms2gt/bin/fornav bin/fornav
            ln -s ../ms2gt/bin/ll2cr bin/ll2cr

    4. Download the polar2grid python package, uncompress it, and link to it:
           
        Prerequisite - Make the polar2gird python package::

            cd /path/to/repos/checkout/trunk/py/polar2grid/
            python setup.py sdist
            mv dist/polar2grid-<py-package-version>.tar.gz /path/to/polar2grid_swbundle_<version>/
            cd /path/to/polar2grid_swbundle_<version>/

        Or you can download the .tar.gz file from here:
            http://larch.ssec.wisc.edu/eggs/repos/polar2grid/

        Link it::

            tar -xzf polar2grid-<py-package-version>.tar.gz
            ln -sf polar2grid-<py-package-version> polar2grid

    5. Copy any companion scripts to software bundle directory::

        cp /path/to/repos/checkout/trunk/py/viirs2awips/viirs2awips.sh /path/to/polar2grid_swbundle_<version>/bin/

    6. Copy/install precompiled ShellB3 package::

        tar -xzf ShellB3-<SB3-version>.tar.gz

    .. note:: Currently there aren't any publicly available ShellB3 tarball packages, contact us to get one.

    7. Create any desired test/work directories and populate with test data.

    8. Create a README text file that describes the package and its author.

    9. Compress software bundle into a tarball::

        tar -czf polar2grid_swbundle_<version>.tar.gz polar2grid_swbundle_<version>

ms2gt Changes or Known issues
-----------------------------

The original ms2gt was last updated May 31st, 2001.  To fit the needs of
polar2grid some of fornav and ll2cr had to be changed/fixed.  The following
changes were made:

    fornav:

        * Allow for fill values other than 0 in the outputted grid:
              This usually would not be an issue, but for certain data cases
              0 is a valid data point.  If 0 was used as the fill value then
              invalid and valid data points would be indistinguishable.
        * Allow provided data channels to have different fill masks:
              fornav "shared" fill masks between data channels/bands.  So if
              one data channel was found to be invalid for a location then so
              was the other.  This fix causes slightly more memory to be used,
              but is necessary for fornav to be used as intended.
        * [Not Fixed] fornav does not properly handle navigation data be
          invalid.  This could also be from ll2cr.

    ll2cr:

        * Allow for lower-case multi-word projection names:
              ll2cr uses a mapx.c library file that has a subfunction for
              converting the name/type of the projection mentioned in the
              gpd (or .mpp) file.  ll2cr was intended to be case-insensitive.
              The mapx function had a bug that resulted in only lower-case
              multi-word projection names being unknown.  This function was
              patched to resolve this issue.

    other:

        * Makefiles did not compile on Enterprise Linux 5 (at least):
            The root Makefile and the src Makefile had incorrect usage of the
            MAKEFLAGS variable.  They did this
            ::

                $(MAKE) $(MAKEFLAGS) ...

            when all you need to do is
            ::

                $(MAKE) ...

            ``make`` passes these flags automatically in the background.
            Those 2 make files also redeclared the MAKE variable as ``make``.
            The ``make`` utility already does this for you.


