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

    polar2grid.sh -r clavrx -w awips_tiled --sector-id LCC --list-products -f clavrx_npp_d20260218_t1710291_e1711532_b74163.level2.hdf

    polar2grid.sh -r clavrx -w geotiff -p cld_height_acha cloud_phase cloud_type -f noaa20/clavrx_j01*.hdf

    polar2grid.sh -r clavrx -w hdf5 --grid-coverage 0.002 -p cld_opd_nlcomp cld_reff_nlcomp refl_lunar_dnb_nom -f snpp/night/clavrx_npp*.hdf

    polar2grid.sh -r clavrx -w binary -f clavrx_a1.26048.2127.1000m.level2.hdf

    polar2grid.sh -r clavrx -w awips_tiled -p cld_height_acha --num-workers 6 --grid-coverage .002 -g polar_alaska_1km --sector-id Polar --letters --compress -f /metopc/clavrx_hrpt_M03_20260218_0759_37795.l1b.level2.hdf
