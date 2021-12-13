.. raw:: latex

    \newpage

Creating ACSPO SST Reprojections
--------------------------------

This set of examples demonstrates how you can create high quality
Sea Surface Temperature (SST) color enhanced images
using a number of the functionalities available in Polar2Grid.

Creating ACSPO GeoTIFF files
****************************

Find the options available for creating ACSPO VIIRS SST GeoTIFFs:

   ``polar2grid.sh acspo gtiff -h``

List the products that can be created from your ACSPO NetCDF dataset:

    ``polar2grid.sh acspo gtiff --list-products -f <path_to_l1b_file>``

To create the default product image, which is `sst` taken from
the `sea_surface_temperature` array in the ACSPO file,
use the following command.  The example data set is the S-NPP VIIRS
direct broadcast overpass from 07:21 UTC, 17 December 2019. Since there is
often cloud cover and land in your datasets, use the ``--grid-coverage``
option to bypass the requirement for 10% coverage of data in the output
image.

.. code-block:: bash

    polar2grid.sh acspo gtiff --grid-coverage 0 \
      -f viirs/20191216072134-STAR-L2P_GHRSST-SSTskin-VIIRS_NPP-ACSPO_V2.61-v02.0-fv01.0.nc

The data set is re-projected into the WGS84 (Platte Carrée) projection
by default. The image scaling is defined in the
`resclale.ini <https://github.com/ssec/polar2grid/blob/main/polar2grid/core/rescale_configs/rescale.ini>`_ file. This file contains product
scaling information for all data parameters supported by Polar2Grid.
The default scaling used for the ACSPO Version
2.61 SST files can be found under data_kind `sea_surface_sub-skin_temperature`
which is taken from the array `standard_name` attribute.

.. parsed-literal::

      50  [rescale:default_sst3]
      51  data_kind=sea_surface_sub-skin_temperature
      52  method=linear
      53  min_in=267.317
      54  max_in=309.816

This is used in the Polar2Grid software to define the range of brightness
values in the output GeoTIFF file (0-255) to the temperatures they represent - in this
case 267.317 K to 309.816 K. Please Note: Previous versions of the ACSPO
sst files use a standard_name attribute of `sea_surface_skin_temperature`.
The scaling is done linearly. The output greyscale image below shows the
VIIRS M-Band 16 (11 micron) Brightness Temperature on the left, and
the ACSPO SST VIIRS image on the right.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/VIIRS_M16_ACSPO_SST_composite_example.png
    :name: VIIRS_M16_ACSPO_SST_composite_example.png
    :width: 100%
    :align: center

    S-NPP VIIRS M-Band 16 Brightness Temperature image (Left panel) and ACSPO Sea Surface Temperature image (Right Panel) from an entire direct broadcast pass acquired on 16 December 2019 covering the eastern portion of Canada and the United States. The default projection is WGS84 (Platte Carrée) and the default scaling is greyscale brightness values 0-255.

Now I would like to create an image cutting out a subset of this pass over a
region of interest that includes the waters surrounding the US state of Florida.
To do this, I need to create a new grid.  I will use the
:ref:`util_p2g_grid_helper` script to do this.

	``p2g_grid_helper.sh acspo_sst -80 30 1000 1000  1200 1200``

I named my grid `acspo_sst`, centered it on `-80 E Longitude` and `30 N Latitude`,
with `1000 m` spatial resolution in the X and Y directions, and defined the output
grid to be `1200 x 1200` lines and elements.

Executing this command results in the following proj4 grid definition:

	``acspo_sst, proj4, +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=30.00000 +lat_1=30.00000 +lon_0=-80.00000 +units=m +no_defs, 1200, 1200, 1000.00000, -1000.00000, -86.56812deg, 35.24785deg``

I store this grid in an ASCII text file named `mygrid.conf`, which I can
provide to `polar2grid.sh` to create an image over my subset region
by executing this command:

.. code-block:: bash

    polar2grid.sh acspo gtiff --grid-coverage 0 --grid-configs mygrid.conf \
      -g acspo_sst -f viirs/*.nc

Note that you need to provide the full path to the `mygrid.conf` if it is not located in the
execution directory.  The subset image that is created from executing this command is
shown below.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/npp_viirs_sst_20191216_072134_acspo_sst.png
    :name: npp_viirs_sst_20191216_072134_acspo_sst.png
    :width: 80%
    :align: center

    S-NPP VIIRS ACSPO SST subset image over our area of interest.

To add a color enhancement to this image, I use the *add_colormap.sh* utility
script and a rainbow color table `p2g_sst_palette.txt` that is included as part of
the Polar2Grid package.  This table is formatted as described in the
:ref:`util_add_colormap` section. You can view the file
`online <https://github.com/ssec/polar2grid/blob/main/swbundle/colormaps/p2g_sst_palette.txt>`_.

This colormap will assign a color value to each of the 0-255 brightness range
in the GeoTIFF image.  Again, the default brightness range is associated with a
temperature range of 267.317 K to 309.816 K.

    ``add_colormap.sh $POLAR2GRID_HOME/colormaps/p2g_sst_palette.txt npp_viirs_sst_20191216_072134_acspo_sst.tif``

The filename will not change, but a color enhancement will be added to the image
as shown below.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/npp_viirs_sst_20191216_072134_acspo_sst_wcolor.png
    :name: npp_viirs_sst_20191216_072134_acspo_sst_wcolor.png
    :width: 80%
    :align: center

    S-NPP VIIRS ACSPO SST color enhanced subset image over our area of interest.

We can tighten the temperature range that is displayed in our region of interest
by creating our own local rescale configuration file, thereby using the
full range of brightness values.  Since I am superseding the standard
rescale.ini file, I use the same default name and data_kind, but redefine the
relationship between the brightness values and the data.  I tighten the
temperature range to be between 279.0 K and 304.0 K.  The contents of
my new rescale file is shown below (my_rescale.ini).

.. parsed-literal::

    [rescale:default_sst3]
    data_kind=sea_surface_sub-skin_temperature
    method=linear
    min_in=279.00
    max_in=304.00

I can then apply this new rescaling file by referencing the file
in the `polar2grid.sh` execution.  In the example below, my_rescale.ini
file is located in the execution directory.  If it is not, you will need
to provide the full path to the file. Please Note: Polar2Grid does not overwrite
output files, so you will need to either rename or delete the original
ACSPO GeoTIFF output file.

.. code-block:: bash

    polar2grid.sh acspo gtiff --rescale-configs my_rescale.ini \
      --grid-coverage 0 --grid-configs mygrid.conf -g acspo_sst -f viirs/*.nc

The result of applying this rescaling to my image and applying my colormap is shown below.

.. figure:: ../_static/example_images/npp_viirs_sst_20191216_072134_acspo_sst_rescaled_wcolor.png
    :name: npp_viirs_sst_20191216_072134_acspo_sst_rescaled_wcolor.png
    :width: 80%
    :align: center

    S-NPP VIIRS ACSPO SST color enhanced subset image over our area of interest using a customized rescaling that linearly maps brightness values of 0-255 to a temperature range of 279.0 K to 304.0 K.

To further enhance this ACSPO SST image I can add a color bar
using the `add_coastlines.sh` script.  There are many options to this script
all of which are listed in the :ref:`util_add_coastlines` section. Users
can control the location and size of the color bar, a color bar title, fonts,
etc. The script overlays the color bar and text onto the image storing
it as a .png file.

For example, executing the following command:

.. code-block:: bash

   add_coastlines.sh npp_viirs_sst_20191216_072134_acspo_sst.tif \
     --add-colorbar --colorbar-text-color="white" \
     --colorbar-units="°K" --colorbar-align top \
     --colorbar-title="VIIRS ACSPO SST  16 December 2019  07:21 UTC" \
     --colorbar-text-size 20 --colorbar-height=35

results in the creation of the file `npp_viirs_sst_20191216_072134_acspo_sst.png`
as displayed below.

.. figure:: ../_static/example_images/npp_viirs_sst_20191216_072134_acspo_sst_rescaled_wcolor_colortable_resize.png
    :name: npp_viirs_sst_20191216_072134_acspo_sst_rescaled_wcolor_colortable_resize.png
    :width: 85%
    :align: center

    S-NPP VIIRS ACSPO SST color enhanced subset image over our area of interest using a customized rescaling that linearly maps brightness values of 0-255 to a temperature range of 279.0 K to 304.0 K including a overlaid color table.

If you wanted to display a more familiar SST temperature scale such as Celsius
or Fahrenheit, you can do that by using the ``--colorbar-min`` and
``--colorbar-max`` options to `add_coastlines.sh`. This will not change
any data values in the file, but it will change the color table display.
For example, I have set the dataset range in my file to be 279.0 K to
304.0 K.  This is equivalent to a range in Degrees Celsius of 5.85 C to 30.85 C.
So by executing the following command, I can display the image
with a color bar in Degrees Celsius.

.. code-block:: bash

    add_coastlines.sh npp_viirs_sst_20191216_072134_acspo_sst.tif \
      --add-colorbar --colorbar-text-color='white' \
      --colorbar-units="°C" --colorbar-min=5.85 \
      --colorbar-max=30.85 --colorbar-tick-marks 5.0 \
      --colorbar-align top \
      --colorbar-title="VIIRS ACSPO SST  16 December 2019  07:21 UTC" \
      --colorbar-text-size 20 --colorbar-height=35

I can perform a similar conversion of the temperature range to
Degrees Fahrenheit and create an image with a color bar labeled
in those units.

.. code-block:: bash

    add_coastlines.sh npp_viirs_sst_20191216_072134_acspo_sst.tif \
      --add-colorbar --colorbar-text-color='white' \
      --colorbar-units="°F" --colorbar-min=42.53 \
      --colorbar-max=87.53 --colorbar-tick-marks 5.0 \
      --colorbar-align top \
      --colorbar-title="VIIRS ACSPO SST  16 December 2019  07:21 UTC" \
      --colorbar-text-size 20 --colorbar-height=35

I can also use the same add_coastlines.sh command to overlay maps
including borders and latitiude longitude grids. For example, if
I execute the command,

.. code-block:: bash

    add_coastlines.sh npp_viirs_sst_20191216_072134_acspo_sst.tif  \
      --add-coastlines --coastlines-outline yellow \
      --coastlines-level 1 --coastlines-resolution=i \
      --add-borders --borders-level 2 --borders-outline gray \
      --add-colorbar --colorbar-text-color='white' \
      --colorbar-units="°C" --colorbar-min=5.85 --colorbar-max=30.85 \
      --colorbar-tick-marks 5.0 --colorbar-align top \
      --colorbar-title="VIIRS ACSPO SST  16 December 2019  07:21 UTC" \
      --colorbar-text-size 20 --colorbar-height=35

it will result in the creation of the final image product that
is a re-gridded, re-scaled, color enhanced image with a color bar labeled in
Degrees Celsius and coastline overlays.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/npp_viirs_sst_20191216_072134_acspo_sst_final_resize.png
    :name: npp_viirs_sst_20191216_072134_acspo_sst_final_resize.png
    :width: 95%
    :align: center

    Final S-NPP VIIRS ACSPO SST image created from data acquired by direct broadcast on 16 December 2019 beginning at 07:21 UTC. The image creation includes re-gridding, re-scaling, color enhanced with color table and map overlays.
