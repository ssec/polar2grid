Installation
============

Polar2Grid is released as python packages and as an all-in-one tarball for
enterprise linux systems. The tarball, or software bundle, provided by the CSPP team
includes a python runtime and all of the necessary third-party software
to run the features provided by Polar2Grid. This is the most convenient way
to run Polar2Grid for people not familiar with python packaging or python software development.

The other remaining sections below should be used by those who want more control over their
environment, want to modify polar2grid source code, or want to run Polar2Grid on a platform
not supported by the CSPP tarball. These sections assume some basic
knowledge about python and python packaging.

Each installation method provides the same set of features except for
the CSPP tarball. The tarball comes with bash scripts for conveniently
calling the python command line tools or utilities provided by third-party
vendors. The main difference is that calling `viirs2gtiff.sh ...` from the
tarball installation is normally called as `p2g_glue viirs gtiff ...`
in a normal python installation.

Polar2Grid is used and tested on Linux and Mac systems. It may work on Windows systems,
but is not actively tested at this time. Polar2Grid is only Python 2 compatible, but
Python 3 compatibility is planned for a future release.

CSPP Software Bundle
--------------------

The CSPP team provides a tarball with a python runtime and
all third-party software required to run Polar2Grid. The tarball
can be found on the
`CSPP team's website <http://cimss.ssec.wisc.edu/cspp/>`_.

The software bundle is only supported on x86_64 RHEL systems, but may work on other Linux
systems as well. Once the software bundle tarball is on the destination system it can be
installed by simply untarring it::

    tar -xzf polar2grid_softwarebundle.tar.gz

This will create a Polar2Grid software bundle directory. To simplify scripts included in
the bundle the following line should be added to your ``.bash_profile``::

    export POLAR2GRID_HOME=/path/to/softwarebundle

The scripts that come with the Polar2Grid software bundle load all other environment
information when they are run.

See :ref:`Getting Started <getting_started_bundle>` for more information on running polar2grid.
To simplify calling scripts even more, the following line can be added below the
``export POLAR2GRID_HOME`` line in your ``.bash_profile``::

    export PATH=$POLAR2GRID_HOME/bin:$PATH

Including this line allows you to remove the ``$POLAR2GRID_HOME/bin/`` portion of the
command line examples.

Python Package Install
----------------------

Polar2Grid can be installed to an existing python environment by
running the following commands::

    pip install --user --trusted-host larch.ssec.wisc.edu --extra-index-url http://larch.ssec.wisc.edu/simple/ polar2grid[awips,gtiff,remap,utils]

This will install the main set of Polar2Grid features and their dependencies.
However, due to the modular design of Polar2Grid some frontends, backends, or
other features may need to be installed separately. Some packages have their
own set of dependencies or special installation instructions, see the
associated page for more information. By substituting the
following package names for `polar2grid[all]` in the above command you can
install the associated component:

 - :doc:`polar2grid.acspo <frontends/acspo>`
 - :doc:`polar2grid.crefl <frontends/crefl>`
 - :doc:`polar2grid.drrtv <frontends/drrtv>`
 - :doc:`polar2grid.mirs <frontends/mirs>`
 - :doc:`polar2grid.modis <frontends/modis>`
 - :doc:`polar2grid.viirs <frontends/viirs>`


Installing from Source
----------------------

To use the most recent changes and bug fixes of polar2grid you can install the
packages directly from the source. This method allows you to customize your
python and dependency locations to your preference. Installing from source
code is the same method used by developers of polar2grid and as such the
instructions mention contributing to the project, but this is entirely
optional.

Instructions can be found here: :doc:`dev_guide/dev_env`
