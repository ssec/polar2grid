AWIPS NetCDF
============

The Advanced Weather Interactive Processing System (AWIPS) is a program used
by the United States National Weather Service (NWS) and others to view
different forms of weather imagery. Once AWIPS is configured for VIIRS data
the AWIPS NetCDF backend can be used to provide compatible products to the
system. The files created by this backend are compatible with both AWIPS and
AWIPS II.

The AWIPS NetCDF backend takes remapped binary image data and creates an
AWIPS-compatible NetCDF 3 file.  To accomplish this the backend must rescale
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
Fog                    :ref:`rescale_fog`
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

