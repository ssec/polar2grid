MODIS L1B Reader
================

.. automodule:: polar2grid.readers.modis_l1b
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.modis_l1b
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r modis_l1b -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh -r modis_l1b -w geotiff -f <path to files>/<list of files>

    polar2grid.sh -r modis_l1b -w geotiff -h

    polar2grid.sh -r modis_l1b -w geotiff --list-products -f /data

    polar2grid.sh -r modis_l1b -w geotiff -p true_color false_color -f ../l1b/a1.17006.1855.250m.hdf ../l1b/a1.17006.1855.500m.hdf ../l1b/a1.17006.1855.1000m.hdf ../l1b/a1.17006.1855.geo.hdf

    polar2grid.sh -r modis_l1b -w geotiff -p vis01 -f ../l1b/a1.17006.1855.250m.hdf ../l1b/a1.17006.1855.geo.hdf

    polar2grid.sh -r modis_l1b -w geotiff --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.yaml -g my_latlon -f ../l1b/a1.17006.1855.250m.hdf ../l1b/a1.17006.1855.geo.hdf

    polar2grid.sh -r modis_l1b -w awips_tiled --sector-id LCC -g lcc_conus_1km --letters --compress --bt-products --grid-coverage=.05 -f MOD021KM.A2017004.1732*.hdf MOD03.A2017004.1732*.hdf

    polar2grid.sh -r modis_l1b -w hdf5 --bt-products --add-geolocation --grid-coverage=.05 -f /data/MOD*.hdf

    polar2grid.sh -r modis_l1b -w hdf5 -g wgs84_fit_250 -f /data/rad/MOD02QKM.*.hdf /data/geo/MOD03.*.hdf


Product Explanation
-------------------

True Color
^^^^^^^^^^

The MODIS Level 1B "true_color" composite produced by |project| provides a view
of the Earth as the human eye would see it; or as close as we can come
to with satellite data and the channels we have available. This means
things like trees and grass are green, water is blue, deserts are
red/brown, and clouds are white. The True Color GeoTIFF 24 bit
image is an :ref:`RGB (Red, Green, Blue) image <explain_rgb_composite>`
consisting of a combination of Red: MODIS Band 1, Green: MODIS Band 4, and Blue: MODIS
Band 3 reflectance channels. Each channel goes through a series of
adjustments to produce the final high quality image output by |project|.

Creation of true color RGBs includes the following steps:

    * Atmospheric :ref:`Rayleigh Scattering Correction <crefl_rayleigh_correction>` of the RGB visible reflectances.
    * Creation of reflectances through :ref:`division by the cosine of the soloar zenith angle <sunz_correction>`.
    * Combining the 3 channels into a 24 bit output file.
    * :ref:`Sharpening of the image <ratio_sharpening>` to full 250m resolution
      if the MODIS 250m Band 1 is provided as input.
    * Application of a :ref:`non-linear enhancement <nonlinear_true_color_scaling>`.

See the :doc:`../examples/modis_example` example to see how |project| can be
used to make this product as a set of AWIPS compatible NetCDF files.

False Color
^^^^^^^^^^^

A false color image is any combination of 3 bands
outside of those used to create a "true color" image (see above). These
combinations can be used to highlight features in the observations that
may not be easily identified in individual band imagery.  |project|
can readily create a preconfigured legacy false color (product false_color)
GeoTIFF 24 bit image that consists of a combination :ref:`RGB (Red, Green, Blue)
image <explain_rgb_composite>` using Red: MODIS Band 7 (2.21 μm), Green: MODIS Band 2 (.86 μm)
and Blue: MODIS Band 1 (.65 μm). This band combination is very effective
at distinguishing land/water boundaries as well as burn scars.

Creation of MODIS legacy false color RGBs includes the following steps:

    * Atmospheric :ref:`Rayleigh Scattering Correction <crefl_rayleigh_correction>` of the RGB visible reflectances.
    * Creation of reflectances through :ref:`division by the cosine of the soloar zenith angle <sunz_correction>`.
    * Combining the 3 channels into a 24 bit output file.
    * :ref:`Sharpening of the image <ratio_sharpening>` to full 250m resolution
      if the MODIS 250m Band 2 is provided as input.
    * Application of a :ref:`non-linear enhancement <nonlinear_true_color_scaling>`.

See the :doc:`../examples/modis_example` example to see how |project| can be
used to make this product as AWIPS compatible NetCDF files.

    polar2grid.sh -r modis_l1b -w geotiff -p true_color false_color -f /aqua/a1.17006.1855.250m.hdf /aqua/a1.17006.1855.500m.hdf /aqua/a1.17006.1855.geo.hdf
