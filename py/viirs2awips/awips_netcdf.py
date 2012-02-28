#!/usr/bin/env python
# encoding: utf-8
"""$Id$
Write AWIPS-compatible NetCDF files

ref http://www.nws.noaa.gov/noaaport/html/icdtb48_3.html
http://www.nco.ncep.noaa.gov/pmb/docs/on388/tableb.html
"""

NCDUMP = """# /data/fxa/modis/7380/20111127_0352
netcdf \20111127_0352 {
dimensions:
	y = 1280 ;
	x = 1100 ;
variables:
	double validTime ;
		validTime:units = "seconds since 1970-1-1 00:00:00.00 0:00" ;
	byte image(y, x) ;
		image:long_name = "image" ;

// global attributes:
		:depictorName = "westConus" ;
		:projName = "LAMBERT_CONFORMAL" ;
		:projIndex = 3 ;
		:lat00 = 54.53548f ;
		:lon00 = -152.8565f ;
		:latNxNy = 17.51429f ;
		:lonNxNy = -92.71996f ;
		:centralLat = 25.f ;
		:centralLon = -95.f ;
		:latDxDy = 39.25658f ;
		:lonDxDy = -117.4858f ;
		:dyKm = 3.931511f ;
		:dxKm = 3.932111f ;
		:rotation = 25.f ;
		:xMin = -0.2556496f ;
		:xMax = 0.01474848f ;
		:yMin = -0.8768771f ;
		:yMax = -0.5622397f ;
}
"""

import os, sys, logging, re
from numpy import *
from netCDF4 import Dataset

AWIPS_ATTRS = set(re.findall(r'\W:(\w+)', NCDUMP))

def create(nc_pathname, image, **attrs):
    nc = Dataset(pathname, 'w', format='NETCDF3_CLASSIC')

    r,c = image.shape
    dim_x = nc.createDimension('x', c)
    dim_y = nc.createDimension('y', r)

    if any((image > 255) | (image < 0)):
        LOG.warning('image has values outside of unsigned byte range!')
    if image.dtype != ubyte:
        LOG.warning('converting image to uint8')
        image = image.astype(ubyte)

    var_image = nc.createVariable('image', 'u1', ('y', 'x'))
    LOG.debug('image(%d,%d)' % (r,c))

    # transfer attributes, converting floating point values to 32-bit
    want_attrs = set(AWIPS_ATTRS)
    have_attrs = set()
    for k,v in attrs.items():
        if issubdtype(type(v), float):
            v = float32(v)
        LOG.debug('.%s = %r' % (k,v))
        setattr(nc, k, v)
        have_attrs.add(k)
    if not want_attrs.issubset(have_attrs):
        LOG.error('missing attributes: %r' % (want_attrs - have_attrs))
    nc.close()


if __name__=='__main__':
    for fn in sys.argv[1:]:
        go(fn)
