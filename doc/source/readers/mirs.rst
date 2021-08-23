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

    polar2grid.sh -r mirs -w geotiff --list-products -f /atms/NPR-MIRS-IMG_v11r1_NPP_s201611111032500_e201611111044016_c201611111121100.nc

    polar2grid.sh -r mirs -w geotiff -p btemp_23v btemp_183h3 swe -g lcc_fit -f /atms/

    polar2grid.sh -r mirs -w awips_tiled -p swe tpw sea_ice rain_rate btemp_89v1 --grid-coverage=0 -g merc_pacific_1km --sector-id Pacific --letters --compress  -f /noaa18/IMG_SX.NN.D17037.S1358.E1409.B6037373.WE.HR.ORB.nc

    polar2grid.sh -r mirs -w awips_tiled --bt-channels -g lcc_conus_750 --sector-id LCC --letters --compress -f ../input/NPR-MIRS-IMG_v11r1_NPP_s201611111032500_e201611111044016_c201611111121100.nc

    polar2grid.sh -r mirs -w hdf5 --add-geolocation -f ../metop/IMG_SX.M1.D17037.S1648.E1700.B0000001.WE.HR.ORB.nc

.. raw:: latex

    \end{minipage}
