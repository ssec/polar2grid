Geotiff
=======

.. versionadded:: 1.0.0

The geotiff backend puts gridded image data into a standard geotiff file.  It
uses the GDAL python API to create the geotiff files.  See
the :doc:`Glue Scripts <../glue_scripts/index>` documentation for geotiff backend options
made available to the user.

The geotiff backend can perform 4 different types of rescaling depending on
how it is configured. One of the determining factors is the :term:`data type`
specified by the user. The backend defaults to 8-bit unsigned integers
(:data:`uint1 <DTYPE_UINT8 = uint1>`), but can also do
16-bit unsigned integer geotiffs (:data:`uint2 <DTYPE_UINT16 = uint2>`). The
second determining factor is whether or not rescaling should increment the
data by 1 (:doc:`../rescaling`). The geotiff backend defaults to NOT
incrementing the data, but may be set differently depending on the
:term:`glue script`. See the documentation for your specific
:doc:`glue_script <../glue_scripts/index>` for details.

This backend will use the following rescaling configuration files to scale
the data provided to it. After rescaling the data is also clipped by casting
the data to the :term:`data type` chosen. For example, for 8-bit unsigned
integers anything below 0 will be clipped to 0 and anything above 255 will
be clipped to 255.

+---------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Data Type     | Increment | Default Rescaling Configuration                                                                                                                               |
+===============+===========+===============================================================================================================================================================+
| uint2         | No        | `rescale.16bit.conf <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid_core/polar2grid/core/rescale_configs/rescale.16bit.conf>`_           |
+---------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| uint2         | Yes       | `rescale_inc.16bit.conf <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid_core/polar2grid/core/rescale_configs/rescale_inc.16bit.conf>`_   |
+---------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| uint1         | No        | `rescale.8bit.conf <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid_core/polar2grid/core/rescale_configs/rescale.8bit.conf>`_             |
+---------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| uint1         | Yes       | `rescale_inc.8bit.conf <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid_core/polar2grid/core/rescale_configs/rescale_inc.8bit.conf>`_     |
+---------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+

The Geotiff backend can handle any PROJ.4 grid.

