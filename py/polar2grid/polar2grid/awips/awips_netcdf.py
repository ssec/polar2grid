#!/usr/bin/env python
# encoding: utf-8
"""
Fill in AWIPS-compatible NetCDF template files with image data.  Also contains
the main AWIPS backend to the `polar2grid.viirs2awips` script.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

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

from polar2grid.core import Workspace,UTC
from polar2grid.nc import create_nc_from_ncml
from polar2grid.rescale import rescale,post_rescale_dnb
from netCDF4 import Dataset
import numpy

import os, sys, logging, re
import shutil
import calendar
from datetime import datetime
from glob import glob

log = logging.getLogger(__name__)
UTC = UTC()
AWIPS_ATTRS = set(re.findall(r'\W:(\w+)', NCDUMP))

def fill(nc_name, image, template, start_dt,
        channel, source, sat_name):
    """Copy a template file to destination and fill it
    with the provided image data.

    WARNING: Timing information is not added
    """
    nc_name = os.path.abspath(nc_name)
    template = os.path.abspath(template)
    if not os.path.exists(template):
        log.error("Template does not exist %s" % template)
        raise ValueError("Template does not exist %s" % template)

    if os.path.exists(nc_name):
        log.error("Output file %s already exists" % nc_name)
        raise ValueError("Output file %s already exists" % nc_name)

    try:
        nc = create_nc_from_ncml(nc_name, template, format="NETCDF3_CLASSIC")
    except StandardError:
        log.error("Could not create base netcdf from template %s" % template)
        raise ValueError("Could not create base netcdf from template %s" % template)

    if nc.file_format != "NETCDF3_CLASSIC":
        log.warning("Expected file format NETCDF3_CLASSIC got %s" % (nc.file_format))

    image_var = nc.variables["image"]
    if image_var.shape != image.shape:
        log.error("Image shapes aren't equal, expected %s got %s" % (str(image_var.shape),str(image.shape)))
        raise ValueError("Image shapes aren't equal, expected %s got %s" % (str(image_var.shape),str(image.shape)))

    # Convert to signed byte keeping large values large
    large_idxs = numpy.nonzero(image > 255)
    small_idxs = numpy.nonzero(image < 0)
    image[large_idxs] = 255
    image[small_idxs] = 0

    image_var[:] = image
    time_var = nc.variables["validTime"]
    time_var[:] = float(calendar.timegm( start_dt.utctimetuple() )) + float(start_dt.microsecond)/1e6

    # Add AWIPS 2 global attributes
    nc.channel = channel
    nc.source = source
    nc.satelliteName = sat_name

    nc.sync() # Just in case
    nc.close()
    log.debug("Data transferred into NC file correctly")

def awips_backend(img_filepath, nc_template, nc_filepath,
        kind, band, data_kind, start_dt,
        channel, source, sat_name, **kwargs):
    try:
        W = Workspace('.')
        img_attr = os.path.split(img_filepath)[1].split('.')[0]
        img_data = getattr(W, img_attr)
        img_data = img_data.copy()
    except StandardError:
        log.error("Could not open img file %s" % img_filepath)
        log.debug("Files matching %r" % glob(img_attr + "*"))
        raise

    if kind != "DNB":
        try:
            rescaled_data = rescale(img_data,
                    kind=kind,
                    band=band,
                    data_kind=data_kind,
                    **kwargs)
            log.debug("Data min: %f, Data max: %f" % (rescaled_data.min(), rescaled_data.max()))
        except StandardError:
            log.error("Unexpected error while rescaling data", exc_info=1)
            raise
    else:
        rescaled_data = post_rescale_dnb(img_data)

    try:
        fill(nc_filepath, rescaled_data, nc_template, start_dt,
                channel, source, sat_name)
    except StandardError:
        log.error("Error while filling in NC file with data")
        raise

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
        img = getattr(W, var_name)
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
