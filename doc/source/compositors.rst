Composites
==========

Compositing is the process in |project| of combining multiple products
together to make a new one. Most often this is done to make RGB color
images like ``true_color`` and ``false_color``. The most
common RGB recipes are already configured internally to |project|, but
users can make their own combinations too. The following instructions will
go over some basic examples of how to make your own composites.

.. ifconfig:: not is_geo2grid

    One common request is to make an RGB image by combining 3 bands from the
    reader's products. We can see an example of this in the ``true_color_raw``
    composite built in to |project|

    .. code-block:: bash

        $POLAR2GRID_HOME/etc/polar2grid/composites/viirs.yaml

    This ``viirs.yaml`` file is meant to hold all custom user composites for
    the VIIRS instrument. There are other YAML files for other instruments.
    The ``true_color_raw`` in this file combines the M05, M04, and M03 bands
    that it gets from the reader. The contents of the YAML file are displayed
    below for reference.

    .. code-block:: yaml

      true_color_raw:
        compositor: !!python/name:satpy.composites.GenericCompositor
        prerequisites:
        - name: M05
          modifiers: [sunz_corrected]
        - name: M04
          modifiers: [sunz_corrected]
        - name: M03
          modifiers: [sunz_corrected]
        standard_name: true_color

    A composite recipe consists of 4 main parts:

    1. Name:
        The name of the composite which will be used to request the product
        on the command line with the ``-p`` flag. In this example
        it is ``true_color_raw``. The name for a composite should be unique
        within a single file or it may be overwritten.
    2. Compositor:
        The ``compositor`` is a pointer to the python code that does the work
        of combining the products together. In this case we are using the
        ``GenericCompositor`` code from the SatPy package which is a simple
        way to combine multiple products as RGBs.
    3. Inputs:
        The prerequisites are the products that are passed as inputs to this
        compositor. In this case we have M05 as the Red channel, M04 as Green,
        and M03 as Blue. These dependencies are specified by their name, but
        have an added "modifier" specified. All the bands have the
        ``sunz_corrected`` modifier which applies the ``/ cos(SZA)`` operation
        necessary to produce proper reflectance data.
    4. Standard Name:
        Used later in |project| processing to map
        a composite to a particular enhancement or scaling. For
        ``true_color_raw`` we're using the ``true_color`` name which has a
        pre-configured enhancement in |project|. If you change this and there
        is no matching enhancement configured, then the default will be used
        which is a dynamic linear stretch from the minimum to maximum of the
        data being processed.

    Once the composite recipe has been added to the ``<instrument>.yaml``
    file it will appear in the list of available products when using the
    ``--list-products`` option.  It can then be invoked like any other
    product to |script_literal|.

    The existing ``true_color_raw`` composite can be modified directly or
    used as a template for additional composites. Make sure to change the
    composite name and what prerequisites are used in the composite. After
    that the composite can be loaded with your data by using the following
    command:

    .. code-block:: bash

        $POLAR2GRID_HOME/bin/polar2grid.sh -r viirs_sdr -w geotiff -p true_color_raw -f /path/to/files*.nc

.. ifconfig:: is_geo2grid

    One type of composite that you may want to make is an image that combines
    one type of product for the night side of the data and another on the day side.
    An example of this type of day/night composite can be found in:

    .. code-block:: bash

        $GEO2GRID_HOME/etc/polar2grid/composites/abi.yaml

    This ``abi.yaml`` file is meant to hold all custom user composites for the
    ABI instrument. There is also an ``ahi.yaml`` file in the same directory
    for the AHI instrument. This file contains the ``true_color_night``
    composite recipe which combines the visible reflectance daytime ``true_color`` 
    composite with the nighttime ABI Channel 14 ``C14`` infrared 11 micron 
    brightness temperatures into one image. The ``abi.yaml`` file contents 
    are displayed below for reference:

    .. code-block:: yaml

        sensor_name: visir/abi

        composites:
          true_color_night:
            compositor: !!python/name:satpy.composites.DayNightCompositor
            prerequisites:
              - true_color
              - C14
            standard_name: day_night_mix

    A composite recipe consists of 4 main parts:

    1. Name:
        The name of the composite which will be used to request the product
        on the command line with the ``-p`` flag. In this example
        it is ``true_color_night``. The name for a composite should be unique
        within a single file or it may be overwritten. 
    2. Compositor:
        The ``compositor`` is a pointer to the python code that does the work
        of combining the products together. In this case we are using the
        ``DayNightCompositor`` code from the SatPy package. Another common
        option is the ``GenericCompositor`` for joining three bands together
        in to an RGB.
    3. Inputs:
        The prerequisites are the products that are passed as inputs to this
        compositor. In the case of the day/night compositor the first product
        listed will be used for day time observations and the second product 
        listed will be used for night time data.
    4. Standard Name:
        Used later in |project| processing to map
        a composite to a particular enhancement or scaling. For the
        ``DayNightCompositor`` this should almost always be ``day_night_mix``.

    Once the composite recipe has been added to the ``<instrument>.yaml`` 
    file it will appear in the list of available products when using the 
    ``--list-products`` option.  It can then be invoked like any other
    product to |script_literal|.

    The existing ``true_color_night`` composite can be modified directly or
    used as a template for additional composites. Make sure to change the
    composite name and what prerequisites are used in the composite. After
    that the composite can be loaded with your data by using the following
    command:

    .. code-block:: bash

        $GEO2GRID_HOME/bin/geo2grid.sh -r abi_l1b -w geotiff -p true_color_night -f /path/to/files*.nc

    The image created by executing the command on a GOES-16 ABI Full Disk dataset from 12:30 UTC, 
    12 November 2018 is shown below.

    .. figure:: _static/example_images/GOES-16_ABI_RadF_true_color_night_20181112_123034_GOES-East_new.png
        :width: 90%
        :align: center

    GOES-16 ABI true color day/Channel 14 brightness temperature night composite using input Full Disk 
    observations from 12:30 UTC, 12 November 2018.

    It is possible to use the compositor to combine RGBs as well.  In the following example, I want
    to use the day/night compositor to combine the true color RGB for day data and the nighttime
    microphysics RGB for nighttime data.  In this case, I can add the following lines to the 
    ``abi.yaml`` file.  Make sure to follow the formatting exactly, including the indentations.

    .. code-block:: yaml

        true_color_night_microphysics:
          compositor: !!python/name:satpy.composites.DayNightCompositor
          prerequisites:
            - true_color
            - night_microphysics
          standard_name: day_night_mix

    Once the .yaml files has been updated, the composite can be generated using the following
    command:

    .. code-block:: bash

        $GEO2GRID_HOME/bin/geo2grid.sh -r abi_l1b -w geotiff -p true_color_night_microphysics -f /path/to/files*.nc

    The image created by executing the command on a GOES-16 ABI Full Disk dataset from 12:30 UTC, 
    12 November 2018 is shown below.

    .. figure:: _static/example_images/GOES-16_ABI_RadF_true_color_night_microphysics_20181112_123034_GOES-East_new.png
        :width: 90%
        :align: center

    GOES-16 ABI true color RGB day/nighttime microphysics RGB night composite using input Full Disk
    observations from 12:30 UTC, 12 November 2018.
