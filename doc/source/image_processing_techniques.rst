Image Processing Techniques
===========================

Many composites in |project| take advantage of various corrections or
adjustments to produce the best looking imagery possible. The below
sections describe the corrections and other related topics used in
|project|. See the various :doc:`readers/index` documentation for more
information on what products are available and descriptions of what
corrections are used.

.. _explain_rgb_composite:

RGB Images
----------

Satellite imagers can simultaneously observe the Earth in multiple spectral
channels, while the human eye is sensitive to only the visible channels. By
mapping data from imager channels to the visible red, green, and blue channels
in different ways, we can produce “RGB” images that show the Earth as a human
would see it from space (“true color”), or that emphasize certain features
that can be detected using combinations of different channels (“false color”).

Luminance (L), or single band, images are also used when displaying a single
imager channel in grayscale. Another popular way of showing single imager
channels is to apply a "colormap" to the data. In these cases, each data value
of a single satellite imager channel is represented by a color. This is
different than the RGB composites described above where multiple channels go
into making a single color image.

Depending on the configuration and writer used, |project| may also add an
additional "Alpha" channel (ex. RGBA) to an image. This Alpha
channel is used to determine the opaqueness or transparency of an image. This
is typically used in |project| to make invalid or missing data values
transparent (completely opaque or completely transparent).

.. _sunz_correction:

Solar Zenith Angle Modification
-------------------------------

Reflectance is defined as the reflected radiation as a fraction of the
incident radiation. To calculate reflectance, the solar zenith angle is needed,
in addition to the radiance measured by the sensor. This modification, used by
some RGB recipes, involves dividing the channel data by the cosine of the
solar zenith angle.

.. _crefl_rayleigh_correction:

Rayleigh Scattering Correction - CREFL
--------------------------------------

Due to the size of molecules that make up our atmosphere, some visible channel
light is preferentially scattered more than others, especially at larger
viewing angles.
The Corrected Reflectance algorithm performs a simple atmospheric correction
with MODIS visible, near-infrared, and short-wave infrared bands (1 to 16).
Later versions of the software were adapted to work with VIIRS data. Both
implementations have been merged and made available as a "modifier" in the
Satpy Python library and used by |project|.
This algorithm was originally developed by the MODIS Rapid Response Team
(http://rapidfire.sci.gsfc.nasa.gov/) and made available by cooperative
agreement, with subsequent additions by the University of South Florida (USF)
and the NASA Direct Readout Laboratory (DRL).

The algorithm corrects for molecular (Rayleigh) scattering and gaseous absorption (water
vapor, ozone) using climatological values for gas contents.  It requires no
real-time input of ancillary data.  The algorithm performs no aerosol
correction.  The Corrected Reflectance products are very similar to the MODIS
Land Surface Reflectance product (MOD09) in clear atmospheric conditions, since
the algorithms used to derive both are based on the 6S Radiative Transfer Model
(Vermote et al.1994).  The products show differences in the presence of
aerosols, however, because the MODIS Land Surface Reflectance product uses a
more complex atmospheric correction algorithm that includes a correction for
aerosols.

.. _psp_rayleigh_correction:

Rayleigh Scattering Correction - Pyspectral
-------------------------------------------

Due to the size of molecules that make up our atmosphere, some visible channel
light is preferentially scattered more than others, especially at larger
viewing angles. One
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

As a final step for some RGB images, |project| scales the image values using a
series of linear interpolation ranges to bring out certain regions of the
image and lessen the
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
