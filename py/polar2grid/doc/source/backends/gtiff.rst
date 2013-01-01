Geotiff
=======

.. include:: ../global.rst

The geotiff backend puts gridded image data into a standard geotiff file.  It
uses the GDAL python API to create the geotiff files.  Currently it can handle
8-bit and 16-bit data and will scale depending on the 'etype' provided.  See
the :doc:`Glue Scripts <../glue_scripts/index>` documentation for geotiff backend options
made available to the user.

The Geotiff backend can handle any PROJ.4 grid.

.. versionadded:: 1.0.0

