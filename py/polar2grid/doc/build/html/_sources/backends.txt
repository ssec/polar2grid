Backends
========

Backends are blocks of software that, given remapped image data and meta data,
produce a file that can be used in another piece of software optimized for
viewing of that data.

For developers, the main advantage of defining backends is that it should be
rather simple to swap backends to make new polar2grid scripts.  This should
simplify and shorten the development cycle of imager to product scripts.

.. _awips_netcdf_backend:

AWIPS NetCDF
------------

The AWIPS NetCDF backend takes remapped binary image data and creates an
AWIPS-compatible NetCDF file.  To accomplish this the backend must rescale
the image data to a 0-255 range, where 0 is a fill/invalid value.  AWIPS
requires unsigned byte integers for its data which results in this range.
It then fills in a NetCDF file template with the rescaled image data.

Reflectance data is rescaled using the following formula:

.. math:: \text{rescaled\_data} = \operatorname{round}(\sqrt{\text{data} * 100.0} * 25.5)

Brightness Temperature data is rescaled using the following formula:

.. math::

    \text{rescaled\_data} = 
    \begin{cases} 
        418 - \text{temp} & \text{temp} < 242.0 \\
        660 - (2 * \text{temp}) & \text{temp}\ge 242.0
     \end{cases}


Rescaling will attempt to fit the provided data in the best visual range for
AWIPS, but can not always do this for outliers.  To correct for this the
AWIPS NetCDF backend also forces any post-rescaling values above 255 to 255
and any values below 0 to 0.  This could result in "washed out" portions of
data in the AWIPS NetCDF file.


