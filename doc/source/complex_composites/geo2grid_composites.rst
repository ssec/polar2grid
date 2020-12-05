ABI - True Color
----------------

The ABI L1b "true_color" composite produced by Geo2Grid is an RGB
(Red, Green, Blue) image consisting of the ABI C02 reflectance channel, a
pseudo-green reflectance channel, and the ABI C01 reflectance channel. Each
channel goes through a series of modifications to produce the final high
quality image output by Geo2Grid.

The pseudo-green channel is a simple combination of 46.5% of C01, 46.5% of
C02, and 7% of C03. While it is impossible to completely reproduce what a
dedicated "green" channel on the ABI instrument would see, this method
provides a good approximation while also limiting the computational
requirements to produce it.

All bands involved in the true color composite have the
:ref:`sunz_correction` and
:ref:`Rayleigh Scattering Correction <psp_rayleigh_correction>` applied,
except for C03 in the pseudo-green band where rayleigh correction is not
applied due to the minimal effect it would have at that wavelength.

To improve the general spatial quality of the image, a
:ref:`self_ratio_sharpening` is also applied. Lastly, a
:ref:`Non-linear enhancement <nonlinear_true_color_scaling>` is applied.