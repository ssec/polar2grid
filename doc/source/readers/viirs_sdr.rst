VIIRS SDR Reader
================

.. automodule:: polar2grid.readers.viirs_sdr
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.viirs_sdr
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r viirs_sdr -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh -r viirs_sdr -w geotiff -f <path to files>/<list of files>

    polar2grid.sh -r viirs_sdr -w geotiff -h

    polar2grid.sh -r viirs_sdr -w geotiff --list-products -f ../sdr/*.h5

    polar2grid.sh -r viirs_sdr -w geotiff --fill-value 0 -f ../sdr/*.h5

    polar2grid.sh -r viirs_sdr -w geotiff -p true_color false_color --num-workers 8 --no-tiled -f ../sdr/*.h5

    polar2grid.sh -r viirs_sdr -w awips_tiled -p i04 adaptive_dnb dynamic_dnb --awips-true-color --awips-false-color --sza-threshold=90.0 --letters --compress --sector-id Polar -g polar_alaska_1km --dnb-saturation-correction -f <path to files>

    polar2grid.sh -r viirs_sdr -w hdf5 --compress gzip --m-bands -f ../sdr/*.h5

    polar2grid.sh -r viirs_sdr -w binary -g lcc_fit -p m15 --num-workers 8 -f ../sdr/SVM15*.h5 ../sdr/GMTCO*.h5

Product Explanation
-------------------

True Color
^^^^^^^^^^

The VIIRS SDR "true_color" composite produced by |project| provides a view
of the Earth as the human eye would see it; or as close as we can come
to with satellite data and the channels we have available. This means
things like trees and grass are green, water is blue, deserts are
red/brown, and clouds are white. The True Color GeoTIFF 24 bit
image is an :ref:`RGB (Red, Green, Blue) image <explain_rgb_composite>`
consisting of a combination of Red: VIIRS M-Band 5, Green: VIIRS M-Band 4,
and Blue: VIIRS M-Band 3 reflectance channels. Each
channel goes through a series of adjustments to produce the final high
quality image output by |project|.

Creation of true color RGBs includes the following steps:

    * Atmospheric :ref:`Rayleigh Scattering Correction <crefl_rayleigh_correction>` of the RGB visible reflectances.
    * Combining the 3 channels into a 24 bit output file.
    * :ref:`Sharpening of the image <ratio_sharpening>` to full 350m resolution
      if the VIIRS I-Band 1 is provided as input.
    * Application of a :ref:`non-linear enhancement <nonlinear_true_color_scaling>`.

See the :doc:`../examples/viirs_example` example to see how |project| can be
used to make this product as a GeoTIFF and KMZ file.

False Color
^^^^^^^^^^^

A false color image is any combination of 3 bands outside of those used
to create a "true color" image (see above). These combinations can be used to
highlight features in the observations that may not be easily identified in
individual band imagery. |project| can readily create a preconfigured legacy
false color (product false_color) GeoTIFF 24 bit image that consists of a combination
:ref:`RGB (Red, Green, Blue) image <explain_rgb_composite>` using uses Red:VIIRS M-Band 11 (2.25 μm), Green:VIIRS M-Band 7 (.87 μm) and Blue:VIIRS M-Band 5 (.67 μm).
This band combination is very effective at distinguishing
land/water boundaries as well as burn scars.

Creation of VIIRS legacy false color RGBs includes the following steps:

    * Atmospheric :ref:`Rayleigh Scattering Correction <crefl_rayleigh_correction>` of the RGB visible reflectances.
    * Combining the 3 channels into a 24 bit output file.
    * :ref:`Sharpening of the image <ratio_sharpening>` to full 350m resolution
      if the VIIRS I-Band 2 is provided as input.
    * Application of a :ref:`non-linear enhancement <nonlinear_true_color_scaling>`.

See the :doc:`../examples/viirs_example` example to see how |project| can be
used to make this product as a GeoTIFF and KMZ output file.

Fog - Temperature Difference
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The VIIRS SDR reader can also produce a "ifog" product which is a simple
difference of the infrared brightness temperatures between the I05 (11.45 μm)
and I04 (3.74 μm) bands (I05 - I04). The result is scaled linearly
between -10.0 and 10.0 Kelvin before being saved to an output image.

Day Night Band
^^^^^^^^^^^^^^

|project| allows the user to create images from the VIIRS Day/Night Band, which
contains observations of visible radiances for both day and night.
|project| provides 4 options for enhancing and scaling the DNB data.
A full description of these options are described in detail in the :doc:`../viirs_day_night_band` appendix.

Reflectance I-Bands 01-03 and M-Bands 01-11
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The I01-I03 and M01-M11 bands are visible reflectance channels on the VIIRS
instrument. Besides the basic calibration necessary to
convert the radiance values to reflectances, the data is passed through
a square root function before being written to a grayscale image. The
square root operation has the effect of balancing the bright and dark
regions of the image.

Infrared I-Bands 04-05 and M-Bands 12-16
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The I04-I05 and M12-M16 bands are all brightness temperature
(infrared (IR)) channels. To produce a grayscale image with dark land
and white clouds, the data is inverted and scaled linearly in two
segments. The first segment is from 163K to 242K, the second
242K to 330K. This is a common scaling used by the National
Weather Service (NWS) for their AWIPS visualization clients.
