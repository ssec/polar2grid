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

    polar2grid.sh -r viirs_sdr -w awips_tiled -p i04 adaptive_dnb dynamic_dnb --awips-true-color --awips-false-color --sza-threshold=90.0 --letters --compress --sector-id Polar -g polar_alaska_1km -f <path to files>

    polar2grid.sh -r viirs_sdr -w hdf5 --compress gzip --m-bands -f ../sdr/*.h5

    polar2grid.sh -r viirs_sdr -w binary -g lcc_fit -p m15 -f ../sdr/SVM15*.h5 ../sdr/GMTCO*.h5

Product Explanation
-------------------

True Color
^^^^^^^^^^

The VIIRS SDR "true_color" composite produced by |project| provides a view
of the Earth as the human eye would see it; or as close as we can come
to with satellite data and the channels we have available. This means
things like trees and grass are green, water is blue, deserts are
red/brown, and clouds are white. The True Color
image is an :ref:`RGB (Red, Green, Blue) image <explain_rgb_composite>`
consisting of the VIIRS M05, M04, and M03 reflectance channels. Each
channel goes through a series of modifications to produce the final high
quality image output by |project|.


All bands involved in the true color composite have the
:ref:`sunz_correction` and
:ref:`Rayleigh Scattering Correction <crefl_rayleigh_correction>` applied.

To improve the general spatial quality of the image, a
:ref:`ratio_sharpening` technique is applied. This only happens if the high
resolution I01 band is available. Lastly, a
:ref:`Non-linear enhancement <nonlinear_true_color_scaling>` is applied.

See the :doc:`../examples/viirs_example` example to see how |project| can be
used to make this product as a geotiff and KMZ file.

False Color
^^^^^^^^^^^

A false color image is any combination of 3 bands
outside of those used to create a "true color" image (see above).
|project| can also readily create a
false color :ref:`RGB (Red, Green, Blue) image <explain_rgb_composite>`.
using Red:VIIRS M-Band 11 (2.25 μm) or MODIS Band 7 (2.21 μm),
Green:VIIRS M-Band 7 (.87 μm) or MODIS Band 2 (.86 μm)
and Blue:VIIRS M-Band 5 (.67 μm) or MODIS Band 1 (.65 μm).
If the I-Band 2 data is also present in a CREFL file,
then it will be used to
:ref:`spatially sharpen <ratio_sharpening>` the image.
All bands involved in the composite have the
:ref:`sunz_correction` and
:ref:`Rayleigh Scattering Correction <crefl_rayleigh_correction>` applied.
This band combination is very effective at distinguishing
land/water boundaries as well as burn scars.

See the :doc:`../examples/viirs_example` example to see how |project| can be
used to make this product as a geotiff.

Fog - Temperature Difference
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The VIIRS SDR reader can also produce a "ifog" product which is a simple
difference of the brightness temperature data between the I05 and I04 bands
(I05 - I04). The result is scaled linearly between -10.0 and 10.0 Kelvin
before being saved to an output image.

Day Night Band
^^^^^^^^^^^^^^

|project| allows the user to request the raw ``dnb`` product from the VIIRS
data files. However, due to various properties of the instrument basic linear
scaling is not enough to make useful images from this data. |project| provides
4 specially normalized versions of the DNB data to bring out more information
when the data is saved as an image. These products include ``historgram_dnb``,
``adaptive_dnb``, ``dynamic_dnb``, and `hncc_dnb``. The explanation for these
products is described in more detail in the :doc:`../viirs_day_night_band`
appendix.

I01 through I03 and M01 through M11
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The I01-I03 and M01-M11 bands are all reflectance channels on the VIIRS
instrument. Besides the basic calibration necessary to
convert the radiance values to reflectances, the data is passed through
a square root function before being written to a grayscale image. The
square root operation has the effect of brightening dark regions of the
image.

I04 through I05 and M12 through M16
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These channels are all brightness temperature (infrared/IR) channels. To
produce a grayscale image with dark land and white clouds, the data is
inverted and scaled linearly in two segments. The first segment is from
163K to 242K, the second 242K to 330K. This is a common scaling used by
the National Weather Service (NWS) for their AWIPS visualization clients.
