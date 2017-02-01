MODIS L1B Reader
================

.. automodule:: polar2grid.modis.modis_to_swath

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.modis.modis_to_swath
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh modis <writer>
    :passparser:

Examples:

.. code-block:: bash

    modis2gtiff.sh -f <path to files>/<list of files>

    modis2gtiff.sh -h 

    polar2grid.sh modis gtiff --list-products -f /data

    polar2grid.sh modis gtiff -p vis01 -f ../l1b/a1.17006.1855.250m.hdf ../l1b/a1.17006.1855.geo.hdf

    polar2grid.sh modis gtiff --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g my_latlon -f ../l1b/a1.17006.1855.250m.hdf ../l1b/a1.17006.1855.geo.hdf

    polar2grid.sh modis awips -g 211e --bt-products --grid-coverage=.05 -f MOD021KM.A2017004.1732*.hdf MOD03.A2017004.1732*.hdf

    polar2grid.sh modis awips -g 203 204 210 -p vis01 vis06 vis26 bt20 bt31 bt35 bt27 -f /data/modis/MOD021KM.A2017004.1732.005.2017023210017.hdf /data/modis/MOD03.A2017004.1732.005.2017023210017.hdf

    polar2grid.sh modis hdf5 --bt-products --add-geolocation --grid-coverage=.05 -f /data/MOD*.hdf

    polar2grid.sh modis hdf5 -g wgs84_fit_250 -f /data/rad/MOD02QKM.*.hdf /data/geo/MOD03.*.hdf

    polar2grid.sh modis binary -f /aqua/a1.17006.1855.500m.hdf /aqua/a1.17006.1855.geo.hdf 
    
