CLAVR-x Cloud Product Reader
============================

.. automodule:: polar2grid.readers.clavrx
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.clavrx
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r clavrx -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh -r clavrx -w geotiff -h

    polar2grid.sh -r clavrx -w awips_tiled --sector-id LCC --list-products -f snpp/clavrx_npp*.hdf

    polar2grid.sh -r clavrx -w geotiff -p cld_height_acha cloud_phase cloud_type -f clavrx_npp_d20170520_t2058143_e2059385_b28822.level2.hdf

    polar2grid.sh -r clavrx -w hdf5 --grid-coverage=.01 -p cld_opd_nlcomp cld_reff_nlcomp refl_lunar_dnb_nom -f snpp/night/clavrx_npp*.hdf

    polar2grid.sh -r clavrx -w binary -f clavrx_hrpt_noaa19_20170517_0936_42605.l1b.level2.hdf

    polar2grid.sh -r clavrx -w awips_tiled -g polar_alaska_1km --sector-id Polar --letters --compress -p cld_temp_acha --grid-coverage=.05 -f /modis/clavrx_a1.17140.2129.1000m.level2.hdf
