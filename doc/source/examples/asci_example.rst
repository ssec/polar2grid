.. raw:: latex

    \newpage

Creating VIIRS Land and Atmosphere Product Images
-------------------------------------------------

This set of examples demonstrates how you can create VIIRS high quality
land and atmosphere color enhanced science product images using Polar2Grid.
The example data set is a NOAA-20 VIIRS direct broadcast 7 granule overpass
starting at 18:50 UTC, 5 June 2024, and covers a region from
Central America to a portion of North America over the United States.

Find the options available for creating VIIRS Environmental Data Record (EDR) GeoTIFFs:

   ``polar2grid.sh -r viirs_edr -w geotiff -h``

List the products that can be created from your VIIRS EDR NetCDF
files. In this case we have the VIIRS Aerosol Optical Depth (JRR-AOD*.nc),
VIIRS Cloud Height (JRR-CloudHeight*.nc) and VIIRS Land Surface Reflectance
(SurfRefl*.nc) NetCDF files available for our 7 granule overpass.

.. code-block:: bash

    polar2grid.sh -r viirs_edr -w geotiff --list-products -f *j01_s20240605185*.nc

Execution of this command results in the following list of Standard Products:

.. parsed-literal::

    ### Standard Available Polar2Grid Products
           AOD550
           CldTopHght
           CldTopTemp
           EVI
           NDVI
           surf_refl_i01
           surf_refl_i02
           surf_refl_i03
           surf_refl_m01
           surf_refl_m02
           surf_refl_m03
           surf_refl_m04
           surf_refl_m05
           surf_refl_m07
           surf_refl_m08
           surf_refl_m10
           surf_refl_m11
           true_color_surf

The standard Land Surface Reflectance products include Normalized Difference Vegetation Index
(NDVI), Enhanced Vegetation Index (EVI), and a true color image created from the surface
reflectance bands (`true_color_surf`). Polar2Grid defaults to producing all available
Standard Products. Users can create one or more selected products by using the `-p` option.
For instance, if I want to create just an image of the Aersol Optical Depth (AOD) for these
data files, I would use this command:

.. code-block:: bash

    polar2grid.sh -r viirs_edr -w geotiff -p AOD550 -f viirs/JRR-AOD_*j01_s20240605185*.nc

An aggregated GeoTIFF image will be created from the 7 granule input files with the data
re-projected into the WGS84 (Platte Carrée) projection by default. The image scaling
is defined in the ``viirs.yaml`` file located in the
``$POLAR2GRID_HOME/etc/polar2grid/enhancements`` directory.
This file contains VIIRS product scaling information.

The default scaling used for the VIIRS AOD files can be found under
`aod550`. The section of the viirs.yaml file that references the VIIRS AOD
product is listed below.

.. parsed-literal::

      136   aod550:
      137     name: AOD550
      138     sensor: viirs
      139     operations:
      140       - name: colorize
      141         method: !!python/name:polar2grid.enhancements.colorize
      142         kwargs:
      143           palettes:
      144             - min_value: 0.0
      145               max_value: 1.0
      146               colors: "rainbow"

This is used in the Polar2Grid software to scale the range of brightness
values in the output GeoTIFF file (0-255) to the AOD values they represent - in this
case 0.0 to 1.0. In addition, this product is by default color enhanced using the
``rainbow`` color map. AOD values above 1.0 are color enhanced using the last color value (dark red).
The scaling is done linearly. AOD values are filtered based upon a Quality Flag (QCAll)
that is either 0 or 1 (high or medium).  The output GeoTIFF image below shows the
end result of the polar2grid.sh command execution for this data.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/VIIRS_AOD_example.png
    :name: VIIRS_AOD_example.png
    :width: 80%
    :align: center

    CSPP NOAA-20 VIIRS Aerosol Optical Depth GeoTIFF image from 5 June 2024, 18:50 UTC (noaa20_viirs_AOD550_20240605_185031_wgs84_fit.tif).

Note that AOD retrievals are not made in sun glint regions.

We can add overlays to the image including a color bar, title and maps using the
``add_coastlines.sh`` script:

.. code-block:: bash

    add_coastlines.sh noaa20_viirs_AOD550_20240605_185031_wgs84_fit.tif --add-colorbar \
      --colorbar-text-color="black" --colorbar-title="VIIRS Aerosol Optical Depth" \
      --add-coastlines --coastlines-outline "black" --coastlines-level 1 \
      --coastlines-resolution=i --add-borders --borders-level 2 --borders-outline "gray" \
      --borders-width 1 --coastlines-width 2 --colorbar-tick-marks 0.1 \
      --colorbar-minor-tick-marks 0.05 --colorbar-height 125 --colorbar-text-size 100

More thorough examples of rescaling and adding overlays can be found in the :doc:`acspo_example`.

The annotated image with overlays is shown below.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/VIIRS_AOD_example_with_overlays.png
    :name: VIIRS_AOD_example_with_overlays.png
    :width: 100%
    :align: center

    CSPP VIIRS NOAA-20 Aerosol Optical Depth PNG image with added borders, coastlines and an annotated colorbar. The retrievals were created from June 5, 2024, 18:50 UTC observations.

Other CSPP VIIRS EDR product images can be created in a similar manner.
For example, the Polar2Grid commands to create a VIIRS Cloud Top Temperature
color enhanced image with overlays are shown below.

.. code-block:: bash

    polar2grid.sh -r viirs_edr -w geotiff -p CldTopTemp -f JRR-CloudHeigh*.nc

    add_coastlines.sh noaa20_viirs_CldTopTemp_20240605_185031_wgs84_fit.tif \
    --add-colorbar --colorbar-text-color="black" \
    --colorbar-title="VIIRS Cloud Top Temperature (°K)" --add-coastlines \
    --coastlines-outline "black" --coastlines-level 1 \
    --coastlines-resolution=i --add-borders --borders-level 2 \
    --borders-outline gray --coastlines-width 2 --colorbar-tick-marks 10 \
    --colorbar-height 125 --colorbar-text-size 100

And the resulting image is shown below:

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/VIIRS_CTT_example_with_overlays.png
    :name: VIIRS_CTT_example_with_overlays.png
    :width: 100%
    :align: center

    CSPP VIIRS NOAA-20 Cloud Top Temperature PNG image with added borders, coastlines and an annotated colorbar. The retrievals were created from June 5, 2024, 18:50 UTC observations.

Similarly, the commands to create a Normalized Difference Vegetation Index (NDVI)
color enhanced image with overlays from the VIIRS Surface Reflectance products
is shown below, followed by the output image.

.. code-block:: bash

    polar2grid.sh -r viirs_edr -w geotiff -p NDVI -f SurfRefl_*.nc

    add_coastlines.sh noaa20_viirs_NDVI_20240605_185031_wgs84_fit.tif \
    --add-colorbar --colorbar-text-color="red" \
    --colorbar-title="Normalized Difference Vegetation Index (NDVI)" --add-coastlines \
    --coastlines-outline "black" --coastlines-level 1 \
    --coastlines-resolution=i --add-borders --borders-level 2 \
    --borders-outline gray --coastlines-width 2 --colorbar-tick-marks 0.1 \
    --colorbar-height 150 --colorbar-text-size 100

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/VIIRS_NDVI_example_with_overlays.png
    :name: VIIRS_NDVI_example_with_overlays.png
    :width: 100%
    :align: center


    CSPP VIIRS NOAA-20 NDVI PNG image with added borders, coastlines and an annotated colorbar. The retrievals were created from June 5, 2024, 18:50 UTC observations.

Polar2Grid supports the creation of individual band and true color images from VIIRS EDR Land Surface
Reflectance output files (SurfRefl*.nc).  Surface reflectances differ from
Top-Of-Atmosphere (TOA) reflectances in that they are corrected to remove the influence
of the atmosphere, thereby preserving only the portion that is being reflected
from the surface below. For more information about the CSPP Surface Reflectance products,
please visit the `CSPP Distribution Website: <https://cimss.ssec.wisc.edu/cspp/viirs_lsr_v1.1.shtml>`_

The commands to create a true color image from the surface reflectance files
with overlays are shown below.  These images are sharpened to 375 m spatial resolution; the
images are not cloud cleared nor water cleared, although the reflectances are
valid only over land.  The commands are followed by the resulting output image.

.. code-block:: bash

    polar2grid.sh -r viirs_edr -w geotiff -p true_color_surf -f SurfRefl_*.nc

    add_coastlines.sh noaa20_viirs_true_color_surf_20240605_185031_wgs84_fit.tif \
    --add-coastlines --coastlines-outline "black" --coastlines-level 1 \
    --coastlines-resolution=i --add-borders --borders-level 2 \
    --borders-outline yellow --coastlines-width 2

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/VIIRS_SurfReflectance_True_Color_example_with_overlays.png
    :name: VIIRS_SurfReflectance_True_Color_example_with_overlays.png
    :width: 100%
    :align: center


    CSPP VIIRS NOAA-20 Land Surface Reflectance True Color image with added borders and coastlines. The retrievals were created from June 5, 2024, 18:50 UTC observations.
