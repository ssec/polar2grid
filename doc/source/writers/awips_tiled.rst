AWIPS Tiled Writer
==================

.. automodule:: polar2grid.writers.awips_tiled
    :noindex:

Command Line Arguments
----------------------

.. ifconfig:: is_geo2grid

    .. argparse::
        :module: polar2grid.writers.awips_tiled
        :func: add_writer_argument_groups
        :prog: |script| -r <reader> -w awips_tiled
        :passparser:

.. raw:: latex

    \newpage

Lettered Sectors
----------------

.. figure:: ../_static/example_images/scmi_grid_LCC.png
    :width: 100%
    :align: center

    `"LCC" Sector Lettered Grid <https://www.ssec.wisc.edu/~davidh/polar2grid/scmi_grids/scmi_grid_LCC.png>`_

.. figure:: ../_static/example_images/scmi_grid_Pacific.png
    :width: 100%
    :align: center

    `"Pacific" Sector Lettered Grid <https://www.ssec.wisc.edu/~davidh/polar2grid/scmi_grids/scmi_grid_Pacific.png>`_

.. figure:: ../_static/example_images/scmi_grid_Mercator.png
    :width: 100%
    :align: center

    `"Mercator" Sector Lettered Grid <https://www.ssec.wisc.edu/~davidh/polar2grid/scmi_grids/scmi_grid_Mercator.png>`_

.. figure:: ../_static/example_images/scmi_grid_Polar.png
    :width: 100%
    :align: center

    `"Polar" Sector Lettered Grid <https://www.ssec.wisc.edu/~davidh/polar2grid/scmi_grids/scmi_grid_Polar.png>`_

.. raw:: latex

    \newpage

Examples:

.. ifconfig:: not is_geo2grid

    .. code-block:: bash

        polar2grid.sh -r acspo -w awips_tiled --letters --compress -g lcc_conus_300 --sector-id LCC -f 20170717185500-STAR-L2P_GHRSST-SSTskin-MODIS_T-ACSPO_V2.40-v02.0-fv01.0.nc

        polar2grid.sh -r clavrx -w awips_tiled --sector-id Polar --letters --compress -g polar_alaska_700 -p refl_lunar_dnb_nom cloud_phase cld_height_acha -f /data/clavrx_npp_d20170706_t0806562_e0808204_b29481.level2.hdf

        polar2grid.sh -r viirs_sdr -w awips_tiled -g merc_pacific_1km --sector-id Pacific --letters --compress -f /path/to/files*.h5

.. ifconfig:: is_geo2grid

    .. code-block:: bash

        geo2grid.sh -r abi_l1b -w awips_tiled --letters --compress --sector-id GOES_EAST -f /path/to/files*.nc
