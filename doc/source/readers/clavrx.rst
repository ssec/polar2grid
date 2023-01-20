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

    polar2grid.sh -r clavrx -w awips_tiled --sector-id LCC --list-products -f clavrx_npp_d20220902_t0742031_e0756141_b56210.level2.hdf

    polar2grid.sh -r clavrx -w geotiff -p cld_height_acha cloud_phase cloud_type -f noaa20/clavrx_j01*.hdf

    polar2grid.sh -r clavrx -w hdf5 --grid-coverage 0.002 -p cld_opd_nlcomp cld_reff_nlcomp refl_lunar_dnb_nom -f snpp/night/clavrx_npp*.hdf

    polar2grid.sh -r clavrx -w binary -f clavrx_a1.22245.0759.1000m.level2.hdf

    polar2grid.sh -r clavrx -w awips_tiled --num-workers 6 -g lcc_conus_300 --sector-id LCC --letters --compress --grid-coverage 0.002 -p cld_temp_acha cld_height_acha cloud_phase cld_opd_dcomp -f noaa19/clavrx_hrpt_noaa19_*.hdf
