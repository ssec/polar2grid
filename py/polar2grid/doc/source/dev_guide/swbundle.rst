Software Bundle
===============

Software bundles are the preferred method of distributing polar2grid by
the |ssec|. Software bundles are gzipped tarballs with a binary installation
of polar2grid and all of its dependencies. Software bundles distributed by
the |ssec| are built for RHEL6 x86_64 systems.

Creating a Software Bundle
--------------------------

To create a software bundle tarball run the software bundle creation script from a clone of the github repository::

    cd /path/to/repos/polar2grid/
    ./create_software_bundle.sh /path/to/swbundle

Optionally you can provide a specific version of ShellB3 (local/remote tarball or path)::

    ./create_software_bundle.sh /path/to/swbundle ftp://ftp.ssec.wisc.edu/pub/shellb3/ShellB3.tar.gz

When this script has completed there will be a ``/path/to/swbundle`` directory and a ``/path/to/swbundle.tar.gz``
file.

.. note::

    The software bundle creation script uses various Makefiles throughout the source tree. If these Makefiles are not
    up-to-date then the software bundle may not build correctly or with the correct version of software.

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
            MAKEFLAGS variable.  The previous usage was::

                $(MAKE) $(MAKEFLAGS) ...

            The current usage is::

                $(MAKE) ...

            ``make`` passes these flags automatically in the background.
            Those 2 make files also redeclared the MAKE variable as ``make``.
            The ``make`` utility already does this for you.

