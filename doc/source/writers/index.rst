Writers
=======

Writers are the final step in the |project| processing chain. They take
gridded data, scale it to fit in an output format, and write the data to
one or more output files. These files can then be provided to a visualization
tool that is optimized for viewing the data.

.. ifconfig:: not is_geo2grid

    .. toctree::
        :maxdepth: 1

        scmi
        binary
        gtiff
        hdf5
        ninjo

.. ifconfig:: is_geo2grid

    .. toctree::
        :maxdepth: 1

        geotiff
