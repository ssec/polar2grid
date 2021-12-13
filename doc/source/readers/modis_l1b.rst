MODIS L1B Reader
================

.. automodule:: polar2grid.readers.modis_l1b
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.modis_l1b
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r modis_l1b -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh -r modis_l1b -w geotiff -f <path to files>/<list of files>

    polar2grid.sh -r modis_l1b -w geotiff -h

    polar2grid.sh -r modis_l1b -w geotiff --list-products -f /data

    polar2grid.sh -r modis_l1b -w geotiff -p vis01 -f ../l1b/a1.17006.1855.250m.hdf ../l1b/a1.17006.1855.geo.hdf

    polar2grid.sh -r modis_l1b -w geotiff --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.yaml -g my_latlon -f ../l1b/a1.17006.1855.250m.hdf ../l1b/a1.17006.1855.geo.hdf

    polar2grid.sh -r modis_l1b -w awips_tiled --sector-id LCC -g lcc_conus_1km --letters --compress --bt-products --grid-coverage=.05 -f MOD021KM.A2017004.1732*.hdf MOD03.A2017004.1732*.hdf

    polar2grid.sh -r modis_l1b -w hdf5 --bt-products --add-geolocation --grid-coverage=.05 -f /data/MOD*.hdf

    polar2grid.sh -r modis_l1b -w hdf5 -g wgs84_fit_250 -f /data/rad/MOD02QKM.*.hdf /data/geo/MOD03.*.hdf

    polar2grid.sh -r modis_l1b -w binary -f /aqua/a1.17006.1855.500m.hdf /aqua/a1.17006.1855.geo.hdf
