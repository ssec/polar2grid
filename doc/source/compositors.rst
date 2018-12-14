Composites
==========

.. ifconfig:: not is_geo2grid

    Compositors are optional components of Polar2Grid that can be used after
    :doc:`remapping <../remapping>`, but before a :doc:`writer <../writers/index>`.
    A compositor can be used to combine multiple Polar2Grid bands to create a new product.
    Normally these types of operations would be done in a :doc:`reader <../readers/index>`
    to create a :term:`secondary product`. However, sometimes calculations require combining
    products of different sizes and resolutions or creating a product with multiple levels like
    RGB images. These operations are much easier to handle after remapping, which is where
    compositors come in.

    Compositors can be specified on the command line for the :term:`glue script` or can be
    called from within python. Compositors can be used from the CSPP software bundle by
    specifying their names as the first arguments to a glue script, but the usual case of
    creating true color images is already the default for the ``crefl2gtiff.sh`` script.

    Compositors can be used from the python command line access by either calling the glue
    script::

        polar2grid.sh <reader> <writer> [<compositor> ...] ...

    What compositors are available can be customized with a configuration file specified
    with the ``--compositor-configs`` flag.

    .. note::

        Compositor's require a specific set of products to complete their calculations. If any required information
        is missing then the compositor will fail.

    Compositors that come with Polar2Grid are described below. Instructions for creating your own
    custom RGB composite are also below.

    .. note::

        Compositors and the way they are implemented will change in future releases after collaboration with the PyTroll
        team.

    .. automodule:: polar2grid.compositors.rgb

.. ifconfig:: is_geo2grid

    Compositing is the process in |project| of putting multiple products
    together to make a new one. Most often this is done to make RGB color
    images like the ``true_color`` or ``false_color`` products. The most
    common RGB recipes are already configured internally to |project|, but
    users can make their own combinations too. The below instructions will
    go over some basic examples of how to make your own composites.

    One type of composite that you may want to make is an image with one
    product shown on the night side of the data and another on the day side.
    An example of this type of composite can be found in:

    .. code-block:: bash

        $GEO2GRID_HOME/etc/satpy/composites/abi.yaml

    This ``abi.yaml`` file is meant to hold all custom user composites for the
    ABI instrument. There is also an ``ahi.yaml`` file in the same directory
    for the AHI instrument. In this file is the ``true_color_night``
    composite recipe which combines the ``true_color`` composite with the
    ``C14`` channel data in to one image. The file contents are copied below
    for reference:

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
        be made on the command line with the ``-p`` flag. In this example
        it is ``true_color_night``. The name for a composite should be unique
        within a single file or it may be overwritten.
    2. Compositor:
        The ``compositor`` is a pointer to the python code that does the work
        of combining the products together. In this case we are using the
        ``DayNightCompositor`` code from the SatPy package. Another common
        option is the ``GenericCompositor`` for joining three bands together
        in to an RGB.
    3. Inputs:
        The prerequisites are the products that are passed as inputs in to this
        compositor. In the case of the day/night compositor the first product
        listed will be used for day time and the second product listed will be
        used at night time.
    4. Standard Name:
        Used later in |project| processing to map
        a composite to a particular enhancement or scaling. For the
        ``DayNightCompositor`` this should almost always be ``day_night_mix``.

    The existing ``true_color_night`` composite can be modified directly or
    used as a template for additional composites. Make sure to change the
    composite name and what prerequisites are used in the composite. After
    that the composite can be loaded with your data by doing:

    .. code-block:: bash

        $GEO2GRID_HOME/bin/geo2grid.sh -r abi-l1b -w geotiff -p true_color_night -f /path/to/files*.nc

