#!/usr/bin/env python
# encoding: utf-8
"""
Fill in AWIPS-compatible NetCDF template files with image data.  Also contains
the main AWIPS backend to the `polar2grid.viirs2awips` script.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2012
:license:      GNU GPLv3
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

from polar2grid.core import Workspace
from polar2grid.core import roles
from polar2grid.core.constants import *
from polar2grid.nc import create_nc_from_ncml
from polar2grid.core.rescale import Rescaler
from polar2grid.core.dtype import clip_to_data_type
from .awips_config import get_awips_info,load_config as load_awips_config,can_handle_inputs as config_can_handle_inputs

import os, sys, logging, re
import calendar
from datetime import datetime

log = logging.getLogger(__name__)
AWIPS_ATTRS = set(re.findall(r'\W:(\w+)', NCDUMP))
DEFAULT_8BIT_RCONFIG = "rescale_configs/rescale.8bit.conf"
DEFAULT_AWIPS_CONFIG = "awips_grids.conf"

def create_netcdf(nc_name, image, template, start_dt,
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
    image = clip_to_data_type(image, DTYPE_UINT8)

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

class Backend(roles.BackendRole):
    removable_file_patterns = [
            "SSEC_AWIPS_*"
            ]

    config = {}
    def __init__(self, backend_config=None, rescale_config=None, fill_value=DEFAULT_FILL_VALUE):
        # Load AWIPS backend configuration
        if backend_config is None:
            log.debug("Using default AWIPS configuration: '%s'" % DEFAULT_AWIPS_CONFIG)
            backend_config = DEFAULT_AWIPS_CONFIG

        self.backend_config = backend_config
        load_awips_config(self.config, self.backend_config)

        # Load rescaling configuration
        if rescale_config is None:
            log.debug("Using default 8bit rescaling '%s'" % DEFAULT_8BIT_RCONFIG)
            rescale_config = DEFAULT_8BIT_RCONFIG
        self.rescale_config = rescale_config
        self.fill_in = fill_value
        self.fill_out = DEFAULT_FILL_VALUE
        self.rescaler = Rescaler(config=self.rescale_config, fill_in=self.fill_in, fill_out=self.fill_out)

    def can_handle_inputs(self, sat, instrument, kind, band, data_kind):
        """Function for backend-calling script to ask if the backend will be
        able to handle the data that will be processed.  For the AWIPS backend
        it can handle any gpd grid that it is configured for in
        polar2grid/awips/awips.conf

        It is also assumed that rescaling will be able to handle the `data_kind`
        provided.
        """
        return config_can_handle_inputs(self.config, sat, instrument, kind, band, data_kind)

    def create_product(self, sat, instrument, kind, band, data_kind, data,
            start_time=None, end_time=None, grid_name=None,
            output_filename=None,
            ncml_template=None, fill_value=None):
        # Filter out required keywords
        if grid_name is None:
            log.error("'grid_name' is a required keyword for this backend")
            raise ValueError("'grid_name' is a required keyword for this backend")
        if start_time is None and output_filename is None:
            log.error("'start_time' is a required keyword for this backend if 'output_filename' is not specified")
            raise ValueError("'start_time' is a required keyword for this backend if 'output_filename' is not specified")

        fill_in = fill_value or self.fill_in
        data = self.rescaler(sat, instrument, kind, band, data_kind, data, fill_in=fill_in, fill_out=self.fill_out)

        # Get information from the configuration files
        awips_info = get_awips_info(self.config, sat, instrument, kind, band, data_kind, grid_name)
        # Get the proper output name if it wasn't forced to something else
        if output_filename is None:
            output_filename = start_time.strftime(awips_info["nc_format"])

        try:
            create_netcdf(output_filename,
                    data,
                    ncml_template or awips_info["ncml_template"],
                    start_time,
                    awips_info["awips2_channel"],
                    awips_info["awips2_source"],
                    awips_info["awips2_satellitename"]
                    )
        except StandardError:
            log.error("Error while filling in NC file with data")
            raise

def go(img_name, template, nc_name=None):
    from polar2grid.core import UTC
    UTC = UTC()

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

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    if len(sys.argv) != 4 and len(sys.argv) != 3:
        log.error("Need at least 2 arguments: <image> <template> [<output>]")
        sys.exit(-1)

    go(*sys.argv[1:])
    #for fn in sys.argv[1:]:
    #    go(fn)
