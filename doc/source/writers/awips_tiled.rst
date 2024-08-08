AWIPS Tiled Writer
==================

.. automodule:: polar2grid.writers.awips_tiled
    :noindex:

Command Line Arguments
----------------------

.. ifconfig:: not is_geo2grid

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

        polar2grid.sh -r viirs_sdr -w awips_tiled --awips-true-color --awips-false-color --num-workers 8 -g lcc_conus_300 --sector-id LCC --letters --compress -f viirs/*.h5

        polar2grid.sh -r modis_l1b -w awips_tiled -p vis01 bt31 -g lcc_conus_1km --sector-id LCC --letters --compress -f a1.22261.1857.250m.hdf a1.22261.1857.1000m.hdf a1.22261.1857.geo.hdf

        polar2grid.sh -r amsr2_l1b -w awips_tiled --num-workers 4 -grid-coverage 0.002 -g polar_alaska_1km --sector-id Polar --letters --compress -f $data_dir/GW1AM2_202209102335_181A_L1DLBTBR_1110110.h5

        polar2grid.sh -r amsr2_l1b -w awips_tiled --grid-coverage 0 -g merc_pacific_1km --sector-id Pacific --letters --compress -f GW1AM2_202209120018_188A_L1DLBTBR_1110110.h5

        polar2grid.sh -r viirs_edr -w awips_tiled -p AOD -g lcc_conus_300 --sector-id LCC --letters --compress --grid-coverage 0.002 -f JRR-AOD_*.nc

        polar2grid.sh -r viirs_edr -w awips_tiled -p NDVI -g lcc_conus_300 --sector-id LCC --letters --compress --grid-coverage 0.002 --maximum-weight-mode -f SurfRefl*.nc

        polar2grid.sh -r acspo -w awips_tiled --num-workers 8 --grid-coverage 0 -g lcc_conus_750 --sector-id LCC --letters --compress --method ewa --weight-delta-max 40.0 --weight-distance-max 1.0 -f $data_dir/202*VIIRS_NPP-ACSPO_V2.80*.nc


.. ifconfig:: is_geo2grid

    .. code-block:: bash

        geo2grid.sh -r abi_l1b -w awips_tiled --letters --compress --sector-id GOES_EAST -f /path/to/files*.nc
