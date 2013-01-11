viirs2gtiff
===========

.. |this_frontend| replace:: :doc:`VIIRS Frontend <../frontends/viirs>`
.. |this_backend| replace:: :doc:`Geotiff Backend <../backends/gtiff>`
.. |this_glue| replace:: viirs2gtiff

.. versionadded:: 1.0.0

:Python Script: ``polar2grid.viirs2gtiff``
:Bundle Script: ``viirs2gtiff.sh``

This is used to process
:doc:`VIIRS imager data <../frontends/viirs>`
into
:doc:`Geotiff images <../backends/gtiff>`.
It can be run using the following command::

    $POLAR2GRID_HOME/bin/viirs2gtiff.sh -d /path/to/data

or for a specific set of files and to force the PROJ.4
:doc:`grid <../grids>`::

    $POLAR2GRID_HOME/bin/viirs2gtiff.sh -g lcc_fit -f /path/to/files*.h5

for more options run::

    $POLAR2GRID_HOME/bin/viirs2gtiff.sh --help

.. program:: |this_glue|

.. include:: common_opts.rst

Command Line Options
--------------------

.. cmdoption:: -g <grid_name> [<grid_name> ...]
               --grids <grid_name> [<grid_name> ...]

    Specify the PROJ.4 grids to be gridded to. The default grid used by
    |this_glue| is ':ref:`wgs84_fit <wgs84_fit>`'. More than one grid can be specified at a
    time. To have grid determination find all grids that can fit the data use the grid name 'all'.

.. cmdoption:: --fornav-d <float>

    Specify the '-d' option for the fornav command line. From the fornav
    documentation::

         weight_distance_max: distance in grid cell units at which to apply a
         weight of weight_min. Default is 1.0. Must be greater than 0.

    The default for this glue script is 2.

.. cmdoption:: --fornav-D <float>

    Specify the '-D' option for the fornav command line. From the fornav
    documentation::

        weight_delta_max: maximum distance in grid cells in each grid
        dimension over which to distribute a single swath cell.
        Default is 10.0.

    The default for this glue script is 40.

.. cmdoption:: --num-procs <int>

    Specify the number of processes in the pool that ll2cr/fornav
    jobs are assigned to. The default is 1, meaning if multiple ll2cr
    jobs are to be run, they will be run 1 at a time. If this flag is
    set to 4, for example, then up to 4 ll2cr jobs can be run at once (in
    parallel), then 4 fornav jobs can be run at once.

.. cmdoption:: --sp

    Force processing of navigation sets to happen serially instead of in
    parallel. This does not affect the `--num-procs` option described above.

.. cmdoption:: --no-pseudo

    Don't create any pseudo-bands possible by the frontend. See the
    |this_frontend| documentation for more information on the
    pseudo-bands it creates.

.. cmdoption:: --rescale-config <rescale configuration>

    Specify the rescaling configuration to be used by the |this_backend|. If
    one is not specified the backend will decide which configuration is best
    for the format and data type specified.

.. cmdoption:: --dtype <data_type>

    Specify the data type (size) for the output format. Not all data types are
    supported (see the |this_backend| documentation for more details). The
    acceptable values are stored in the
    `constants <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid_core/polar2grid/core/constants.py>`_
    file, prefixed with ``DTYPE_``. Use the value not the constant name.

    |this_glue| defaults to ``uint2`` a 16-bit unsigned integer.

.. cmdoption:: --dont_inc

    Tell the backend to tell the rescaler to not increment the rescaled data
    by 1. Incrementing the data is done automatically for the common case of
    0 as a fill value in output data. So, if data is scaled from 0-254 and
    this flag is not specified, the data will be incremented so valid data is
    between 1 and 255. This allows the backend to clip any data below 0 to the
    value 0.

    If the rescaling configuration is not specified, most backends that
    support the :option:`--dont_inc` will choose a correct default rescaling
    configuration file to scale the data to the proper range.

.. cmdoption:: -p <output_pattern>
               --pattern <output_pattern>

    Specify the python formatting string for the output filename of produced
    files. For more information on the default available keywords see the
    :py:func:`create_output_filename <polar2grid.core.roles.BackendRole.create_output_filename>`
    method. See the
    |this_backend| documentation for any possible keywords added by the
    backend filename formatting. The output pattern specified should be
    contained in double quotes to avoid conflicts with the command line
    shell trying to interpret keywords. Pattern keywords are specified using
    the python formatting syntax ``%(sat)s`` to specify the ``sat`` keyword.

