Backends
========

Backends are polar2grid components that, given remapped image data and meta data,
produce a file that can be used in another piece of software optimized for
viewing of that data.

For developers, the main advantage of defining backends is that it is rather
simple to swap backends to make new polar2grid glue scripts.  This should
simplify and shorten the development cycle of imager to product scripts.

.. _backend_awips_netcdf:

AWIPS NetCDF
------------

The AWIPS NetCDF backend takes remapped binary image data and creates an
AWIPS-compatible NetCDF file.  To accomplish this the backend must rescale
the image data to a 0-255 range, where 0 is a fill/invalid value.  AWIPS
requires unsigned byte integers for its data which results in this range.
It then fills in a NetCDF file template with the rescaled image data.

The AWIPS NetCDF backend uses
`NCML templates <http://www.unidata.ucar.edu/software/netcdf/ncml/>`_
to generate the output netcdf files.  Currently, the backend only handles
gpd/mapx grids and since the products are intended for AWIPS they must be
of grids understood by the AWIPS software.  The rescaling done by this backend
uses the following rescaling functions in the most common use cases.  Since
rescaling and the AWIPS backend are configurable please see the
`AWIPS configuration file <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/awips/awips_grids.conf>`_
and the default
`rescaling configuration file <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid_core/polar2grid/core/rescale_configs/rescale.8bit.conf>`_
for more details.

====================== ==================
Data Kind              Rescaling Function
====================== ==================
Reflectance            :ref:`rescale_square_root_enhancement`
Brightness Temperature :ref:`rescale_btemp`
Radiance               :ref:`rescale_linear`
====================== ==================

Rescaling will attempt to fit the provided data in the best visual range for
AWIPS, but can not always do this for outliers.  To correct for this the
AWIPS NetCDF backend also clips any post-rescaling values above 255 to 255
and any values below 0 to 0.  This could result in "washed out" portions of
data in the AWIPS NetCDF file.

The AWIPS backend can handle the following grids and uses the listed NCML
file:

========= =========
Grid Name NCML File
========= =========
211e      `grid211e.ncml <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/awips/ncml/grid211e.ncml>`_
211w      `grid211w.ncml <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/awips/ncml/grid211w.ncml>`_
203       `grid203.ncml <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/awips/ncml/grid203.ncml>`_
204       `grid204.ncml <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/awips/ncml/grid204.ncml>`_
========= =========

.. _backend_geotiff:

Geotiff
-------

The geotiff backend puts gridded image data into a standard geotiff file.  It
uses the GDAL python API to create the geotiff files.  Currently it can handle
8-bit and 16-bit data and will scale depending on the 'etype' provided.  See
the :doc:`Glue Scripts <glue_scripts/index>` documentation for geotiff backend options
made available to the user.

The Geotiff backend can handle any PROJ.4 grid.

.. versionadded:: 1.0.0

.. _backend_binary:

Binary
------

The binary backend is a very simple backend that outputs the gridded data in
a flat binary file for each band of data.  The binary backend can handle any
grid, gpd or PROJ.4.

