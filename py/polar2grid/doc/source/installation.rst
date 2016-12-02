Installation
============

Polar2Grid is released as an all-in-one tarball for
enterprise linux systems. The tarball, or software bundle, provided by the CSPP team
includes a python runtime and all of the necessary third-party software
to run the features provided by Polar2Grid.
The tarball uses bash scripts for conveniently
calling the python software or utilities provided by third-party
vendors. The software bundle is only supported on x86_64 RHEL systems,
but may work on other Linux systems as well.
There are other ways to install
Polar2Grid on other operating systems, but the instructions to do so are
beyond the scope of this documentation. Please
`Contact Us <http://cimss.ssec.wisc.edu/contact-form/index.php?name=CSPP%20Questions>`_
if you have questions about installation.

The CSPP tarball can be found on the
`CSPP team's website <http://cimss.ssec.wisc.edu/cspp/>`_.

Once the software bundle tarball is on the destination system it can be
installed by simply untarring it::

    tar -xzf polar2grid_softwarebundle.tar.gz

This will create a Polar2Grid software bundle directory. To simplify calling
scripts included in the bundle the following lines should be added to your
``.bash_profile``::

    export POLAR2GRID_HOME=/path/to/softwarebundle
    export PATH=$POLAR2GRID_HOME/bin:$PATH

All other environment information needed to run is automatically loaded by the
scripts provided by Polar2Grid.
See :ref:`Getting Started <getting_started_bundle>` for more information on
running Polar2Grid.

