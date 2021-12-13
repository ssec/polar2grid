Software Bundle
===============

Software bundles are the preferred method of distributing polar2grid by
the |ssec|. Software bundles are gzipped tarballs with a binary installation
of polar2grid and all of its dependencies. Software bundles distributed by
the |ssec| are built for RHEL7 x86_64 systems.

Note that normal development of Polar2Grid and Geo2Grid does not require
building a software bundle. Building the bundle is generally an automated
processing done by CI services running on the development servers.

Creating a Software Bundle
--------------------------

A conda environment with all necessary dependencies must be activated before running the build process. To create
this environment run the following using the "build_environment.yml" file from the git repository::

    conda env create -n p2g_build -f build_environment.yml
    conda activate p2g_build

To create a software bundle tarball run the software bundle creation script::

    cd /path/to/repos/polar2grid/
    ./create_conda_software_bundle.sh /path/to/swbundle
