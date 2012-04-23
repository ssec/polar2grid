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

.. math:: \text{rescaled\_data} = \operatorname{round}(\sqrt{\text{data} * 100.0} * 25.5)

Brightness Temperature data is rescaled using the following formula:

.. math::

    \text{rescaled\_data} = 
    \begin{cases} 
        418 - \text{temp} & \text{temp} < 242.0 \\
        660 - (2 * \text{temp}) & \text{temp}\ge 242.0
     \end{cases}

