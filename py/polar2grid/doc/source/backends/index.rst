Backends
========

Backends are the final step in the Polar2Grid processing chain. They take
gridded data, scale it to fit in an output format, and write the data to
one or more output files. These files can then be provided to a visualization
tool that is optimized for viewing the data.

.. toctree::
    :maxdepth: 1

    awips_netcdf
    binary
    gtiff
    hdf5
    ninjo

