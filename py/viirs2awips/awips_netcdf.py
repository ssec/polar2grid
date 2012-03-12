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
import shutil
import calendar
from datetime import datetime

from numpy import *
from netCDF4 import Dataset
from keoni.fbf import Workspace
from keoni.time.epoch import UTC


log = logging.getLogger(__name__)
UTC = UTC()
AWIPS_ATTRS = set(re.findall(r'\W:(\w+)', NCDUMP))

def create(nc_pathname, image, **attrs):
    # Clobber will not allow truncating of an existing file
    nc = Dataset(nc_pathname, 'w', format='NETCDF3_CLASSIC', clobber=False)

    r,c = image.shape
    dim_x = nc.createDimension('x', c)
    dim_y = nc.createDimension('y', r)

    if any((image > 255) | (image < 0)):
        log.warning('image has values outside of unsigned byte range!')
    #if image.dtype != ubyte:
    #    log.warning('converting image to uint8')
    #    image = image.astype(ubyte)
    if image.dtype != byte:
        # netCDF4 should do this automatically, but just in case
        log.warning('converting image to int8')
        image = image.astype(byte)

    var_image = nc.createVariable('image', 'b', ('y', 'x'))
    #var_image = nc.createVariable('image', 'u1', ('y', 'x'))
    log.debug('image(%d,%d)' % (r,c))

    # transfer attributes, converting floating point values to 32-bit
    want_attrs = set(AWIPS_ATTRS)
    have_attrs = set()
    for k,v in attrs.items():
        if issubdtype(type(v), float):
            v = float32(v)
        log.debug('.%s = %r' % (k,v))
        setattr(nc, k, v)
        have_attrs.add(k)
    if not want_attrs.issubset(have_attrs):
        log.error('missing attributes: %r' % (want_attrs - have_attrs))
    nc.close()

def fill(nc_name, image, template, start_dt):
    """Copy a template file to destination and fill it
    with the provided image data.

    WARNING: Timing information is not added
    """
    nc_name = os.path.abspath(nc_name)
    template = os.path.abspath(template)
    # TODO: How do I figure out the time?
    if not os.path.exists(template):
        log.error("Template does not exist %s" % template)
        return False

    if os.path.exists(nc_name):
        log.error("Output file %s already exists" % nc_name)
        return False

    try:
        shutil.copyfile(template, nc_name)
    except StandardError:
        log.error("Could not copy template file %s to destination %s" % (template,nc_name))
        return False

    nc = Dataset(nc_name, "a")
    if nc.file_format != "NETCDF3_CLASSIC":
        log.warning("Expected file format NETCDF3_CLASSIC got %s" % (nc.file_format))

    image_var = nc.variables["image"]
    if image_var.shape != image.shape:
        log.error("Image shapes aren't equal, expected %s got %s" % (str(image_var.shape),str(image.shape)))
        return False

    # Convert to signed byte keeping large values large
    large_idxs = nonzero(image > 255)
    small_idxs = nonzero(image < 0)
    image[large_idxs] = 255
    image[small_idxs] = 0

    image_var[:] = image
    # FIXME: Time needs to be derived from somewhere
    time_var = nc.variables["validTime"]
    time_var[:] = float(calendar.timegm( start_dt.utctimetuple() )) + float(start_dt.microsecond)/1e6
    nc.sync() # Just in case
    nc.close()
    log.debug("Data transferred into NC file correctly")
    return True

def go(img_name, template, nc_name=None):
    # Make up an NC name
    img_name = os.path.abspath(img_name)
    base_dir,img_fn = os.path.split(img_name)
    var_name = img_fn.split(".")[0]
    base_name = os.path.splitext(img_fn)[0]
    if base_name == '':
        log.error("Could not extract file's base name %s" % img_name)
        return False

    if nc_name is None:
        nc_name = base_name + ".nc"
        nc_path = os.path.join(base_dir, nc_name)
    else:
        nc_path = os.path.abspath(nc_name)

    # Open the image file
    try:
        W = Workspace(base_dir)
        img = getattr(W, var_name)[0]
        data = img.copy()
    except StandardError:
        log.error("Could not open img file %s" % img_name, exc_info=1)
        return False

    # Create the NC file
    fill(nc_path, data, template, datetime.utcnow().replace(tzinfo=UTC))
    return True

if __name__=='__main__':
    logging.basicConfig(level=logging.WARNING)
    if len(sys.argv) != 4 and len(sys.argv) != 3:
        log.error("Need at least 2 arguments: <image> <template> [<output>]")
        sys.exit(-1)

    go(*sys.argv[1:])
    #for fn in sys.argv[1:]:
    #    go(fn)
