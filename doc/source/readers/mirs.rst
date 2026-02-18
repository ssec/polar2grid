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

    polar2grid.sh -r mirs -w geotiff --list-products -f /atms/NPR-MIRS-IMG_v11r9_n21_s202602180700298_e202602180712134_c202602180739560.nc

    polar2grid.sh -r mirs -w geotiff --list-products-all -f /atms/NPR-MIRS-IMG_v11r9_n20_s202602181730163_e202602181743039_c202602181809040.nc

    polar2grid.sh -r mirs -w geotiff -p btemp_88v btemp_183h3 swe -g lcc_fit -f /atms/

    polar2grid.sh -r mirs -w awips_tiled --num-workers 4 --grid-coverage 0 -g merc_pacific_1km --sector-id Pacific --letters --compress -p swe tpw sea_ice rain_rate btemp_89v1 -f /metopc/NPR-MIRS-IMG_v11r9_ma3_s202602111553000_e202602111605000_c202602111613350.nc

    polar2grid.sh -r mirs -w awips_tiled --bt-channels -g lcc_conus_750 --sector-id LCC --letters --compress -f ../input/NPR-MIRS-IMG_v11r9_npp_s202602181711063_e202602181722179_c202602181745360.nc

    polar2grid.sh -r mirs -w hdf5 --add-geolocation --dtype float32 -f ../metopc/NPR-MIRS-IMG_v11r9_ma3_s202602111553000_e202602111605000_c202602111613350.nc

.. raw:: latex

    \end{minipage}
