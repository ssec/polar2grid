Remapping
=========

Remapping is the process of mapping polar-orbiting satellite data pixels to
an evenly spaced grid.  This grid is either equal-area or equal-angle
depending on the projection provided.
Polar2grid's remapping step is actually 2 separate steps. The first step
known as ll2cr (lat/lon to col/row) calculates each pixels location in the
newly projected grid. It takes a longitude/latitude location and maps it to
a column/row location in the grid being mapped to.  This grid location is a
decimal value (fractional pixel locations) used in the second remapping step.
The second step known as fornav (forward navigation) takes the output of the
first remapping step and weights each input image pixel to calculate the
output grid pixel.

Grid specifications are provided to remapping via grid names and the first
step of remapping will pull the information from the `grids.conf` file (see
the :doc:`grids` section below).  There are 2 methods of accessing
the remapping process.  The first is calling the 2 steps of remapping
separately using the following::

    from polar2grid.remap import run_ll2cr,run_fornav
    ll2cr_output = run_ll2cr(sat, instrument, kind, lon_fbf, lat_fbf,
                        grid_jobs, **kwargs)
    fornav_output = run_fornav(sat, instrument, kind, grid_jobs, ll2cr_output,
                        **kwargs)

See the API documentation for more information on possible keyword arguments.

TODO API Link

The second method is by calling::

    from polar2grid.remap import remap_bands
    fornav_output = remap_bands(sat, instrument, kind, lon_fbf, lat_fbf,
                        grid_jobs, **kwargs)

This function simply calls ``run_ll2cr`` and ``run_fornav``.
See the API documentation for more information on possible keyword arguments.

TODO API Link


