#!/usr/bin/env python
# encoding: utf-8
"""
Fill in AWIPS-compatible NetCDF template files with image data.  Also contains
the main AWIPS backend to the `polar2grid.viirs2awips` script.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3

Copyright (C) 2013 Space Science and Engineering Center (SSEC),
 University of Wisconsin-Madison.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

This file is part of the polar2grid software package. Polar2grid takes
satellite observation data, remaps it, and writes it to a file format for
input into another program.
Documentation: http://www.ssec.wisc.edu/software/polar2grid/

    Written by David Hoese    January 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

from polar2grid.core import Workspace
from polar2grid.core import roles
from polar2grid.core.constants import *
from polar2grid.nc import create_nc_from_ncml
from polar2grid.core.rescale import Rescaler
from polar2grid.core.dtype import clip_to_data_type
from .awips_config import AWIPSConfigReader,CONFIG_FILE as DEFAULT_AWIPS_CONFIG

import os, sys, logging
import calendar
from datetime import datetime

log = logging.getLogger(__name__)
DEFAULT_8BIT_RCONFIG = "rescale_configs/rescale.8bit.conf"

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

    def __init__(self, backend_config=None, rescale_config=None, fill_value=DEFAULT_FILL_VALUE):
        # Load AWIPS backend configuration
        if backend_config is None:
            log.debug("Using default AWIPS configuration: '%s'" % DEFAULT_AWIPS_CONFIG)
            backend_config = DEFAULT_AWIPS_CONFIG
        self.awips_config_reader = AWIPSConfigReader(backend_config)

        # Load rescaling configuration
        if rescale_config is None:
            log.debug("Using default 8bit rescaling '%s'" % DEFAULT_8BIT_RCONFIG)
            rescale_config = DEFAULT_8BIT_RCONFIG
        self.fill_in = fill_value
        self.fill_out = DEFAULT_FILL_VALUE
        self.rescaler = Rescaler(rescale_config, fill_in=self.fill_in, fill_out=self.fill_out)

    def can_handle_inputs(self, sat, instrument, nav_set_uid, kind, band, data_kind):
        """Function for backend-calling script to ask if the backend will be
        able to handle the data that will be processed.  For the AWIPS backend
        it can handle any gpd grid that it is configured for in
        polar2grid/awips/awips.conf

        It is also assumed that rescaling will be able to handle the `data_kind`
        provided.
        """
        return [ config_info["grid_name"] for config_info in self.awips_config_reader.get_all_matching_entries(sat, instrument, nav_set_uid, kind, band, data_kind) ]

    def create_product(self, sat, instrument, nav_set_uid, kind, band, data_kind, data,
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
        data = self.rescaler(sat, instrument, nav_set_uid, kind, band, data_kind, data, fill_in=fill_in, fill_out=self.fill_out)

        # Get information from the configuration files
        awips_info = self.awips_config_reader.get_config_entry(sat, instrument, nav_set_uid, kind, band, data_kind, grid_name)
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
