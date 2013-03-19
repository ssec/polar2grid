Backends
========

Backends are polar2grid components that, given remapped image data and meta data,
produce a file that can be used in another piece of software optimized for
viewing of that data.

For developers, the main advantage of defining backends is that it is rather
simple to swap backends to make new polar2grid :term:`glue scripts`.

.. toctree::
    :maxdepth: 1

    awips_netcdf
    gtiff
    binary
    ninjo

