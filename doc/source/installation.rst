Installation
============

Polar2Grid is released as an all-in-one tarball for
Enterprise Linux systems. The tarball, or software bundle, provided by the CSPP team
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

Polar2Grid Software
-------------------

The Polar2Grid tarball can be found on either the CSPP website:

    http://cimss.ssec.wisc.edu/cspp/

Next, unpack the tarball::

    tar xf CSPP_IMAPP_POLAR2GRID_V2.2.1.tar.gz

This will create a Polar2Grid software bundle directory, ``polar2grid_v_2_2_1``.
To simplify calling scripts included in the bundle the following line should
be added to your ``.bash_profile``::

    export POLAR2GRID_HOME=/path/to/softwarebundle

All other environment information needed to run is automatically loaded by the
scripts provided by Polar2Grid. Scripts are typically invoked using::

    $POLAR2GRID_HOME/bin/<p2g_script.sh> ...

If you want to run commands without including the preceding directory path,
or if using in a script in its own background environment, then you can set
your path to include the /bin directory::

    export PATH=$PATH:$POLAR2GRID_HOME/bin

See :doc:`getting_started` for more information on running Polar2Grid.

Polar2Grid Test Data
--------------------

If you want to run the test case to verify your installation,
download the following file::

    CSPP_IMAPP_POLAR2GRID_V2.2.1_TEST_DATA.tar.gz

The test data should be unpacked in a directory separate from the Polar2Grid
installation::

    cd $HOME
    tar xf CSPP_IMAPP_POLAR2GRID_V2.2.1_TEST_DATA.tar.gz

This will create a ``polar2grid_test`` directory containing the test input,
output, and verification scripts for both MODIS and VIIRS instruments.

See :doc:`verification/index` for instructions on using the verification
test data.

