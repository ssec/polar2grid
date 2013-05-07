viirs2ninjo
===========

.. |this_frontend| replace:: :doc:`VIIRS Frontend <../frontends/viirs>`
.. |this_backend| replace:: :doc:`NinJo Backend <../backends/ninjo>`
.. |this_glue| replace:: viirs2ninjo

:Python Script: ``polar2grid.viirs2ninjo``
:Bundle Script: ``viirs2ninjo.sh``

This script is used to process
:doc:`VIIRS imager data <../frontends/viirs>`
into
:doc:`NinJo compatible TIFF <../backends/ninjo>`
files.

`viirs2ninjo` does not have any special restrictions on the bands that can
be provided. This glue script will also scale the DNB data using the method
described :ref:`here <prescale_viirs_dnb>`.

See the :doc:`../backends/ninjo` backend for more
information on what scaling it does to prepare the data for the
NinJo compatible TIFF file.

.. program:: viirs2ninjo

.. include:: common_opts.rst

Command Line Options
--------------------

.. cmdoption:: -g <grid_name> [<grid_name> ...]
               --grids <grid_name> [<grid_name> ...]

    Specify the gpd grids to be gridded to. Specifying this option will skip
    the grid determination step. More than one grid can be specified at a
    time.  To have grid determination find all grids that can fit the data use
    the grid name 'all'. All possible grid names can be found
    :doc:`here <../grids>`.

.. cmdoption:: --grid-configs <grid_config.conf> [<grid_config.conf> ...]

    Specify the grid configuration files to use. If the grids being
    specified should be added to the built-in set of grids, the first
    argument should be |default_grid_config|. Config. files are processed
    in the order they are specified. If a grid is specified in more than
    one config. file the most recently processed file's entry will be used.
    See the :doc:`../dev_guide/grids` section for information on creating
    and adding your own grids.

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

.. cmdoption:: --rescale-config <rescale configuration>

    Specify the rescaling configuration to be used by the |this_backend|. If
    one is not specified the backend will decide which configuration is best
    for the format and data type specified.
