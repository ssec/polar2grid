Software Bundle
===============

Software bundles are the preferred method of distributing polar2grid by
the |ssec|. Software bundles are gzipped tarballs with a binary installation
of polar2grid and all of its dependencies. Software bundles distributed by
the |ssec| are built for RHEL6 x86_64 systems.

Creating Software Bundle from Github Repository
---------------------------------------------------

.. warning::

    When using the ``tar`` command make sure the version used properly
    handles symbolic links (the fornav, ll2cr, and polar2grid symlinks).

Follow these steps to recreate the software bundle ``*.tar.gz`` file.

    1. Create the software bundle directory and change to it::

        mkdir polar2grid-swbundle-<version>
        cd polar2grid-swbundle-<version>

    2. Create binary directory::

        mkdir bin

    3. Download polar2grid's version of ms2gt into the bundle directory, untar it, and link to the used utilities:

        http://www.ssec.wisc.edu/~davidh/polar2grid/ms2gt/

        Soft link it::

            tar -xzf ms2gt<ms2gt-version>.tar.gz
            # if needed, rename ms2gt directory:
            mv ms2gt<version> ms2gt
            ln -s ../ms2gt/bin/fornav bin/fornav
            ln -s ../ms2gt/bin/ll2cr bin/ll2cr

        .. note:: If you need a new/patched version of ms2gt, see :ref:`building_ms2gt`.

    4. Copy/install precompiled ShellB3 (core-cspp) package:

        ftp://ftp.ssec.wisc.edu/pub/shellb3/

        Extract it::

            tar -xzf ShellB3-<SB3-version>.tar.gz


    5. Download the polar2grid python package, uncompress it, and link to it:
           
        Prerequisite - Make the polar2gird python package::

            cd /path/to/repos/checkout/root/py/
            # make clean (optional)
            make all_sdist

            # put the eggs in the repository if ready (SSEC internal only)
            make torepos

        Install the packages directly from the tarball files::

            cd /path/to/polar2grid-swbundle-<version>

            # All dependencies should be installed automatically with this command:
            ShellB3/bin/python -m easy_install -U /path/to/repos/checkout/root/py/dist/*.tar.gz

    6. Copy any bundle scripts and environment scripts to software bundle directory::

        cp /path/to/repos/checkout/root/swbundle/*.{sh,txt} /path/to/polar2grid-swbundle-<version>/bin/

    7. Copy the grid config example directory:

        cp -r /path/to/repos/checkout/root/swbundle/grid_configs /path/to/polar2grid-swbundle-version/

    8. Compress software bundle into a tarball::

        tar -czf polar2grid-swbundle-<version>.tar.gz polar2grid-swbundle-<version>

.. _building_ms2gt:

Building ms2gt
--------------

The following steps say how to build ms2gt on a Linux machine. To be
completely compatible with the Software Bundle and ShellB3, it should be
built on a RHEL 5 "clean room" (MilliCentOS5m64 Virtual Machine).

::

    cd /path/to/repos/root/ms2gt/
    # Build ms2gt
    make
    # Package it into a tarball
    make tar
    # Move (or scp) to the bundle build directory
    mv ms2gt<ms2gt-version>.tar.gz /path/to/polar2grid-swbundle-<version>

    # To delete the temporary directory that was made:
    rm -r ms2gt<ms2gt-version>

.. _ms2gt_changes:

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

