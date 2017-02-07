MIRS Reader
===========

.. automodule:: polar2grid.mirs.mirs2swath

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.mirs.mirs2swath
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh mirs <writer>
    :passparser:

Execution Examples
-----------------------

.. code-block:: bash

    mirs2gtiff.sh --list-products -f /atms/NPR-MIRS-IMG_v11r1_NPP_s201611111032500_e201611111044016_c201611111121100.nc

    polar2grid.sh mirs gtiff -p mirs_btemp_01 mirs_btemp_22 swe -g lcc_fit -f /atms/

    polar2grid.sh mirs awips -p swe tpw sea_ice mirs_rain_rate mirs_btemp_90 --grid-coverage=0 -g 204 -f /noaa18/IMG_SX.NN.D17037.S1358.E1409.B6037373.WE.HR.ORB.nc

    polar2grid.sh mirs hdf5 --add-geolocation -f ../metop/IMG_SX.M1.D17037.S1648.E1700.B0000001.WE.HR.ORB.nc

