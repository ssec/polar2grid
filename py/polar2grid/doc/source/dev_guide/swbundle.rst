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

