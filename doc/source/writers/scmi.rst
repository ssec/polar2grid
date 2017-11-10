AWIPS SCMI Writer
=================

.. automodule:: polar2grid.awips.scmi_backend


Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.awips.scmi_backend
    :func: add_backend_argument_groups
    :prog: polar2grid.sh <reader> scmi
    :passparser:

.. raw:: latex

    \newpage

Lettered Sectors
----------------

.. figure:: ../_static/example_images/scmi_grid_LCC.png
    :width: 100%
    :align: center

    "LCC" Sector Lettered Grid

.. figure:: ../_static/example_images/scmi_grid_Pacific.png
    :width: 100%
    :align: center

    "Pacific" Sector Lettered Grid

.. figure:: ../_static/example_images/scmi_grid_Mercator.png
    :width: 100%
    :align: center

    "Mercator" Sector Lettered Grid

.. figure:: ../_static/example_images/scmi_grid_Polar.png
    :width: 100%
    :align: center

    "Polar" Sector Lettered Grid

.. raw:: latex

    \newpage

Examples:

.. code-block:: bash

	polar2grid.sh acspo scmi --letters --compress -g lcc_conus_300 --sector-id LCC  --grid-coverage=0.0 -f 20170717185500-STAR-L2P_GHRSST-SSTskin-MODIS_T-ACSPO_V2.40-v02.0-fv01.0.nc

	polar2grid.sh clavrx scmi --sector-id Polar --letters --compress -g polar_alaska_700 -p refl_lunar_dnb_nom cloud_phase cld_height_acha --grid-coverage=0.0 -f /data/clavrx_npp_d20170706_t0806562_e0808204_b29481.level2.hdf

	polar2grid.sh viirs_sdr scmi -g merc_pacific_1km --sector-id Pacific --letters --compress -f /path/to/files*.h5

	




