viirs2awips
===========

.. |this_frontend| replace:: :doc:`VIIRS Frontend <../frontends/viirs>`
.. |this_backend| replace:: :doc:`AWIPS Backend <../backends/awips_netcdf>`
.. |this_glue| replace:: viirs2awips

:Python Script: ``polar2grid.viirs2awips``
:Bundle Script: ``viirs2awips.sh``

This script is used to process
:doc:`VIIRS imager data <../frontends/viirs>`
into
:doc:`AWIPS compatible NetCDF <../backends/awips_netcdf>`
files.  It can be run using the following command::

    $POLAR2GRID_HOME/bin/viirs2awips.sh -d /path/to/data/

or to force the gpd
:doc:`grid <../grids>` that will be mapped to::

    $POLAR2GRID_HOME/bin/viirs2awips.sh -g 203 -d /path/to/data/

for more options run::

    $POLAR2GRID_HOME/bin/viirs2awips.sh --help

`viirs2awips` does not have any special restrictions on the bands that can
be provided.  However, `viirs2awips` creates the
:ref:`SSEC Fog pseudoband <pseudo_viirs_ifog>` if the I05 and I04 bands are
provided.  This glue script will also scale the DNB data using the method
described :ref:`here <prescale_viirs_dnb>`.

See the :doc:`../backends/awips_netcdf` for more
information on what scaling it does to prepare the data for the
AWIPS-compatible NetCDF file.

.. program:: |this_glue|

.. include:: common_opts.rst

Command Line Options
--------------------

.. cmdoption:: -g <grid_name> [<grid_name> ...]
               --grids <grid_name> [<grid_name> ...]

    Specify the gpd grids to be gridded to. Specifying this option will skip
    the grid determination step. More than one grid can be specified at a
    time.

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

.. cmdoption:: --nc <ncml template>

    Force the NCML template that the AWIPS backend uses. See the
    :doc:`AWIPS Backend Documentation <../backends/awips_netcdf>` for more
    information.

.. cmdoption:: --backend-config <backend configuration>

    Specify the backend configuration to use. The default is determined by the
    backend. Backends can load pre-made configurations that are packaged with
    polar2grid. Backends can also load properly formatted CSV files if an
    absolute or relative path is specified. See the |this_backend| for more
    information.

.. cmdoption:: --rescale-config <rescale configuration>

    Specify the rescaling configuration to be used by the |this_backend|. If
    one is not specified the backend will decide which configuration is best
    for the format and data type specified.
