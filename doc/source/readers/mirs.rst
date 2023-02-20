MIRS Reader
===========

.. automodule:: polar2grid.readers.mirs
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.mirs
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r mirs -w <writer>
    :passparser:

Execution Examples
-----------------------

.. raw:: latex

    \begin{minipage}{\linewidth}

.. code-block:: bash

    polar2grid.sh -r mirs -w geotiff --list-products -f /atms/NPR-MIRS-IMG_v11r8_n20_s202208250741413_e202208250753249_c202208250817490.nc

    polar2grid.sh -r mirs -w geotiff --list-products-all -f /atms/NPR-MIRS-IMG_v11r8_npp_s202208250653413_e202208250704529_c202208250730310.nc

    polar2grid.sh -r mirs -w geotiff -p btemp_88v btemp_183h3 swe -g lcc_fit -f /atms/

    polar2grid.sh -r mirs -w awips_tiled --num-workers 4 --grid-coverage 0 -g merc_pacific_1km --sector-id Pacific --letters --compress -p swe tpw sea_ice rain_rate btemp_89v1 -f /noaa19/NPR-MIRS-IMG_v11r8_n19_s202208250310331_e202208250314143_c202208251718490.nc

    polar2grid.sh -r mirs -w awips_tiled --bt-channels -g lcc_conus_750 --sector-id LCC --letters --compress -f ../input/NPR-MIRS-IMG_v11r1_NPP_s201611111032500_e201611111044016_c201611111121100.nc

    polar2grid.sh -r mirs -w hdf5 --add-geolocation --dtype float32 -f ../metopc/NPR-MIRS-IMG_v11r8_ma3_s202208251542209_e202208251554261_c202208251742030.nc

.. raw:: latex

    \end{minipage}
