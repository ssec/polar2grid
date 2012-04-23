Installation
============

The polar2grid python package can be installed in 2 types of environments,
as an individually installed python package or as part of the polar2grid
software bundle.  The software bundle is the preferred, recommended,
and intended method of installing the polar2grid software.

polar2grid Software Bundle
--------------------------

The polar2grid software bundle is a pre-compiled set of software required
to run the polar2grid scripts.  It includes a minimal python 2.7 install,
with the variaous packages required by the polar2grid python package.

Once the software bundle tarball is on the destination system it can be
installed first by untarring it:

    ``tar -xzf polar2grid_softwarebundle.tar.gz``

Next, it is suggested that you add this line to your .bash_profile:

    ``export PATH=path/to/softwarebundle/bin:$PATH``

Without any other work, polar2grid scripts must be used to run any
remappings from satellite data to grid format as they setup the rest
of the environment. See :doc:`scripts </scripts>` for more information.


See :doc:`Advanced Topics </advanced>` for python package installing.

