Backends
========

AWIPS NetCDF
------------

The AWIPS NetCDF backend takes remapped binary image data and creates an
AWIPS-compatible NetCDF file.  To accomplish this the backend must rescale
the image data to a 0-255 range, where 0 is a fill/invalid value.  AWIPS
requires unsigned byte integers for its data which results in this range.
It then fills in a NetCDF file template with the rescaled image data.

Reflectance data is rescaled using the following formula:

.. math:: rescaleddata = round(\sqrt{data * 100.0} * 25.5)

Brightness Temperature data is rescaled using the following formula:

    if temp_value < 242.0:

    .. math:: rescaleddata = 418 - temp

    if temp_value >- 242.0:

    .. math:: rescaleddata = 660 - (2 * temp)
