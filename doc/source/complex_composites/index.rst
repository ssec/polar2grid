Complex Composites
==================

Many composites in |project| take advantage of various corrections or
adjustments to produce the best looking imagery possible. The below
sections describe the corrections used in |project| and also describe
a few key composites provided in |project| and which of these
corrections they use.

.. _sunz_correction:

Solar Zenith Angle Modification
-------------------------------

Visible channel data is not truly a "reflectance" until it has been adjusted
for the amount of sun reflecting off of the atmosphere. While this is a very
common change when working with numeric reflectance data, some RGB recipes
may not include it.

.. _psp_rayleigh_correction:

Rayleigh Scattering Correction - Pyspectral
-------------------------------------------

Due to atmospheric molecules, some visible channels are scattered obscuring
the measurement of the surface which we typically want in RGB images. One
method to correct for this is implemented in the Pyspectral Python library.
A detailed description of the algorithm used by Pyspectral and other features
of the library can be found in the official Pyspectral documentation:

https://pyspectral.readthedocs.io/en/latest/rayleigh_correction.html

.. _ratio_sharpening:

Ratio Sharpening
----------------

Some sensors include channels that measure radiance at the same wavelength,
but at different spatial resolutions. When making an RGB image that uses one
of these multi-resolution wavelengths combined with other channels that are
only available at lower resolutions, we can use the multi-resolution channels
to sharpen the other channels. For example, if the high-resolution channel is
used for R, and lower resolution channels for G and B, we can do::

    R_ratio = R_hi / R_lo
    new_R = R_hi
    new_G = G * R_ratio
    new_B = B * R_ratio

By upsampling the lower resolution G and B channels and multiplying by the
ratio of high and low resolution R channels, we can produce a sharper looking
final image. That is, the lower resolution channels appear to have a better
spatial resolution than they did originally.

.. _self_ratio_sharpening:

Self Ratio Sharpening
---------------------

Similar to the :ref:`ratio_sharpening` described above, it is possible to
apply a similar sharpening when one of the channels of the RGB is only
provided in a high resolution. In this case, we can downsample the high
resolution channel to the resolution of the other channels (averaging the
pixels), then upsample the result again. By taking the ratio of the original
high resolution and this averaged version, we can produce a ratio similar
to that in the above ratio sharpening technique.

.. _nonlinear_true_color_scaling:

Non-linear True Color Scaling
-----------------------------

As a final "enhancement" or scaling method, Geo2Grid uses a series of linear
interpolation ranges to bring out certain regions of the image and lessen the
effect of others. For lack of a better name, these multiple linear stretches
make up an overall non-linear scaling. A typical scaling where reflectance
data (0 - 1) has been multiplied by 255 (8-bit unsigned integer) would be:

.. list-table::
    :header-rows: 1

    * - **Input Range**
      - **Output Range**
    * - 0 - 25
      - 0 - 90
    * - 25 - 55
      - 90 - 140
    * - 55 - 100
      - 140 - 175
    * - 100 - 255
      - 175 - 255

.. ifconfig:: not is_geo2grid

    .. include:: polar2grid_composites.rst

.. ifconfig:: is_geo2grid

    .. include:: geo2grid_composites.rst

