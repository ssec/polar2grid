Installation
============

|project| is released as an all-in-one tarball for
Enterprise Linux systems. The tarball, or software bundle, provided by the
|cspp_title| (|cspp_abbr|) team
includes a python runtime and all of the necessary third-party software
to run the features provided by |project|.
The tarball uses bash scripts for conveniently
calling the python software or utilities provided by third-party
vendors. The software bundle is only supported on x86_64 RHEL systems,
but may work on other Linux systems as well.
There are other ways to install
|project| on other operating systems, but the instructions to do so are
beyond the scope of this documentation.

.. ifconfig:: is_geo2grid

    Please
    `Contact Us <http://cimss.ssec.wisc.edu/contact-form/index.php?name=CSPP%20Geo%20Questions>`__
    if you have questions about installation.

.. ifconfig:: not is_geo2grid

    Please
    `Contact Us <http://cimss.ssec.wisc.edu/contact-form/index.php?name=CSPP%20Questions>`__
    if you have questions about installation.

|project| Software
------------------

The |project| tarball can be found on the CSPP website:

.. ifconfig:: is_geo2grid

        http://cimss.ssec.wisc.edu/csppgeo/

    Next, unpack the tarball:

    .. code-block:: bash

        tar xf CSPP_GEO2GRID_V1.0.0.tar.gz

    This will create a |project| software bundle directory, ``geo2grid_v_2_2_1``.
    To simplify calling scripts included in the bundle the following line should
    be added to your ``.bash_profile``:

    .. code-block:: bash

        export GEO2GRID_HOME=/path/to/softwarebundle

    All other environment information needed to run is automatically loaded by the
    scripts provided by |project|. Scripts are typically invoked using:

    .. code-block:: bash

        $GEO2GRID_HOME/bin/<p2g_script.sh> ...

    If you want to run commands without including the preceding directory path,
    or if using in a script in its own background environment, then you can set
    your path to include the /bin directory:

    .. code-block:: bash

        export PATH=$PATH:$GEO2GRID_HOME/bin

.. ifconfig:: not is_geo2grid

        http://cimss.ssec.wisc.edu/cspp/

    Next, unpack the tarball:

    .. code-block:: bash

        tar xf CSPP_POLAR2GRID_V2.2.1.tar.gz

    This will create a Polar2Grid software bundle directory, ``polar2grid_v_2_2_1``.
    To simplify calling scripts included in the bundle the following line should
    be added to your ``.bash_profile``:

    .. code-block:: bash

        export POLAR2GRID_HOME=/path/to/softwarebundle

    All other environment information needed to run is automatically loaded by the
    scripts provided by Polar2Grid. Scripts are typically invoked using:

    .. code-block:: bash

        $POLAR2GRID_HOME/bin/<p2g_script.sh> ...

    If you want to run commands without including the preceding directory path,
    or if using in a script in its own background environment, then you can set
    your path to include the /bin directory:

    .. code-block:: bash

        export PATH=$PATH:$POLAR2GRID_HOME/bin

See :doc:`getting_started` for more information on running |project|.

|project| Test Data
-------------------

.. ifconfig:: is_geo2grid

    If you want to run the test case to verify your installation,
    download the following file:

    .. code-block:: bash

        CSPP_GEO2GRID_V1.0.0_TEST_DATA.tar.gz

    The test data should be unpacked in a directory separate from the |project|
    installation:

    .. code-block:: bash

        cd $HOME
        tar xf CSPP_GEO2GRID_V1.0.0_TEST_DATA.tar.gz

    This will create a ``geo2grid_test`` directory containing the test input,
    output, and verification scripts for the ABI instrument.

.. ifconfig:: not is_geo2grid

    If you want to run the test case to verify your installation,
    download the following file:

    .. code-block:: bash

        CSPP_POLAR2GRID_V2.2.1_TEST_DATA.tar.gz

    The test data should be unpacked in a directory separate from the |project|
    installation:

    .. code-block:: bash

        cd $HOME
        tar xf CSPP_POLAR2GRID_V2.2.1_TEST_DATA.tar.gz

    This will create a ``polar2grid_test`` directory containing the test input,
    output, and verification scripts for both MODIS and VIIRS instruments.

See :doc:`verification/index` for instructions on using the verification
test data.

