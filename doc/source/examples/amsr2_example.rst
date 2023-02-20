.. raw:: latex

    \newpage

Creating AMSR2 Reprojections
----------------------------

This example walks through some common tasks when working with
GCOM-W1 AMSR2 Level 1B data.

Creating AMSR2 GeoTIFF files
****************************

Find the options available for creating AMSR2 Level 1B GeoTIFFs:

   ``polar2grid.sh -r amsr2_l1b -w geotiff -h``

List all of the products that can be created from your AMSR2 HDF5 dataset:

    ``polar2grid.sh -r amsr2_l1b -w geotiff --list-products-all -f <path_to_l1b_file>``

To create AMSR2 GeoTIFF files of all default bands found in your data set
and reprojected to the default Platte Carrée projection:

    ``polar2grid.sh -r amsr2_l1b -w geotiff -f <path_to_l1b_file>``

Create the default set of GeoTIFF images for the AMSR2 Level 1B file acquired
on 10 September 2022, at 23:35 UTC:

.. code-block:: bash

    polar2grid.sh -r amsr2_l1b -w geotiff --fill-value 0 -f GW1AM2_202209102335_181A_L1DLBTBR_1110110.h5

Executing this command produces these files in WGS84 (Platte Carrée) projection:

.. parsed-literal::

    gcom-w1_amsr2_btemp_36\.5h_20220910_233500_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_36\.5v_20220910_233500_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0ah_20220910_233500_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0av_20220910_233500_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bh_20220910_233500_wgs84_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bv_20220910_233500_wgs84_fit\.tif

The GeoTIFF image for AMSR2 89.0ah GHz band is displayed below.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/gcom-w1_amsr2_btemp_89.0ah_20220910_233500_wgs84_fit.png
    :width: 40%
    :align: center

    GCOMW-1 AMSR2 L1B 89.0ah GHz brightness temperatures using default scaling.  Data set was observed at 23:35 UTC on 10 Setember 2022.

Naval Research Lab (NRL) Image Reproductions
********************************************

Polar2Grid inclues the capability to reproduce the AMSR2 color enhanced
images staged on the the Naval Research Lab (NRL) tropical cyclone
page:  http://www.nrlmry.navy.mil/TC.html

First, create a reprojected GeoTIFF in Lambert Conic Conformal (LCC) projection
and rescale the data. The data in this example is from 10 September 2022. We are pointing
to the rescale information that is stored in the `$POLAR2GRID_HOME/example_enhancements/amsr2_png/enhancements/generic.yaml` file.
This will produce a linear scaled output of data rangeing from 180.0 K to 280.0 K brightness temperatures
for our default products.

.. code-block:: bash

    polar2grid.sh -r amsr2_l1b -w geotiff --extra-config-path $POLAR2GRID_HOME/example_enhancements/amsr2_png -g lcc_fit --fill-value 0 -f GW1AM2_202209102335_181A_L1DLBTBR_1110110.h5

Executing this command produces these AMSR2 LCC GeoTIFF files:

.. parsed-literal::

    gcom-w1_amsr2_btemp_36\.5h_20220910_233500_lcc_fit\.tif
    gcom-w1_amsr2_btemp_36\.5v_20220910_233500_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0ah_20220910_233500_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0av_20220910_233500_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bh_20220910_233500_lcc_fit\.tif
    gcom-w1_amsr2_btemp_89\.0bv_20220910_233500_lcc_fit\.tif

Once the data has been rescaled, you are ready to apply the NRL colormaps to the data. In this example we
are using the 89A/H GHz file.

.. code-block:: bash

    add_colormap.sh $POLAR2GRID_HOME/libexec/python_runtime/etc/polar2grid/colormaps/amsr2_89h.cmap gcom-w1_amsr2_btemp_89.0ah_20220910_233500_lcc_fit.tif

This command adds the enhancement to the original GeoTIFF.  The rescaled and final color enhanced product are shown below:

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/gcom-w1_amsr2_btemp_89.0ah_20220910_233500_wgs84_lcc_fit_rescaled_and_colorized.png
    :name: gcom-w1_amsr2_btemp_89.0ah_20220910_233500_wgs84_lcc_fit_rescaled_and_colorized.png
    :width: 60%
    :align: center

    GCOMW-1 AMSR2 L1B 89.0A/H GHz brightness temperatures reprojected in Lambert Conic Conformal Projection and rescaled (left), and with a color table applied (right) using the Naval Research Lab color ehancement. The data set was collected at 23:35 UTC on 10 September 2022.
