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

from polar2grid.core import roles
from polar2grid.core.constants import *
from polar2grid.nc import create_nc_from_ncml
from polar2grid.core.rescale import Rescaler
from polar2grid.core.dtype import clip_to_data_type
from .awips_config import AWIPSConfigReader, CONFIG_FILE as DEFAULT_AWIPS_CONFIG

import os, sys, logging
import calendar

LOG = logging.getLogger(__name__)
DEFAULT_RCONFIG      = "rescale_configs/rescale.ini"

def create_netcdf(nc_name, image, template, start_dt,
        channel, source, sat_name):
    """Copy a template file to destination and fill it
    with the provided image data.

    WARNING: Timing information is not added
    """
    nc_name = os.path.abspath(nc_name)
    template = os.path.abspath(template)
    if not os.path.exists(template):
        LOG.error("Template does not exist %s" % template)
        raise ValueError("Template does not exist %s" % template)

    try:
        nc = create_nc_from_ncml(nc_name, template, format="NETCDF3_CLASSIC")
    except StandardError:
        LOG.error("Could not create base netcdf from template %s" % template)
        raise

    if nc.file_format != "NETCDF3_CLASSIC":
        LOG.warning("Expected file format NETCDF3_CLASSIC got %s" % (nc.file_format))

    image_var = nc.variables["image"]
    if image_var.shape != image.shape:
        LOG.error("Image shapes aren't equal, expected %s got %s" % (str(image_var.shape),str(image.shape)))
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
    LOG.debug("Data transferred into NC file correctly")


class Backend(roles.BackendRole):
    def __init__(self, backend_configs=None, rescale_configs=None,
                 overwrite_existing=False, keep_intermediate=False, exit_on_error=True):
        backend_configs = backend_configs or [DEFAULT_AWIPS_CONFIG]
        rescale_configs = rescale_configs or [DEFAULT_RCONFIG]
        # FIXME: Redo the config reader
        self.awips_config_reader = AWIPSConfigReader(*backend_configs)
        self.rescaler = Rescaler(*rescale_configs)
        self.overwrite_existing = overwrite_existing
        self.keep_intermediate = keep_intermediate
        self.exit_on_error = exit_on_error

    def create_output_from_scene(self, gridded_scene):
        output_filenames = []
        for product_name, gridded_product in gridded_scene.items():
            try:
                output_fn = self.create_output_from_product(gridded_product)
                output_filenames.append(output_fn)
            except StandardError:
                LOG.error("Could not create output for '%s'", product_name)
                if self.exit_on_error:
                    raise
                LOG.debug("Backend exception: ", exc_info=True)
                continue
        return output_filenames

    def create_output_from_product(self, gridded_product, ncml_template=None):
        data_type = DTYPE_UINT8
        inc_by_one = False
        fill_value = 0
        awips_info = self.awips_config_reader.get_product_options(gridded_product)
        output_filename = gridded_product["begin_time"].strftime(awips_info["filename_format"])

        if os.path.isfile(output_filename):
            if not self.overwrite_existing:
                LOG.error("AWIPS file already exists: %s", output_filename)
                raise RuntimeError("AWIPS file already exists: %s" % (output_filename,))
            else:
                LOG.warning("AWIPS file already exists, will overwrite: %s", output_filename)

        # Create the geotiff
        try:
            LOG.info("Scaling %s data to fit in geotiff...", gridded_product["product_name"])
            data = self.rescaler.rescale_product(gridded_product, data_type, inc_by_one=inc_by_one, fill_value=fill_value)

            LOG.info("Writing product %s to AWIPS NetCDF file", gridded_product["product_name"])
            create_netcdf(output_filename, data, ncml_template or awips_info["ncml_template"],
                          gridded_product["begin_time"],
                          awips_info["awips2_channel"], awips_info["awips2_source"], awips_info["awips2_satellite_name"])
        except StandardError:
            LOG.error("Error while filling in NC file with data: %s", output_filename)
            if not self.keep_intermediate and os.path.isfile(output_filename):
                os.remove(output_filename)
            raise

        return output_filename


def add_backend_argument_groups(parser):
    group = parser.add_argument_group(title="Backend Initialization")
    group.add_argument("--backend-configs", nargs="*", dest="backend_configs",
                       help="alternative backend configuration files")
    group.add_argument("--rescale-configs", nargs="*", dest="rescale_configs",
                       help="alternative rescale configuration files")
    group = parser.add_argument_group(title="Backend Output Creation")
    group.add_argument("--ncml-template",
                       help="alternative AWIPS ncml template file from what is configured")
    return ["Backend Initialization"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    from polar2grid.core.meta import GriddedScene, GriddedProduct
    parser = create_basic_parser(description="Create AWIPS compatible NetCDF files")
    subgroup_titles = add_backend_argument_groups(parser)
    parser.add_argument("--scene", required=True, help="JSON SwathScene filename to be remapped")
    parser.add_argument("-p", "--products", nargs="*", default=None,
                        help="Specify only certain products from the provided scene")
    args = parser.parse_args(subgroup_titles=subgroup_titles)

    # Logs are renamed once data the provided start date is known
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)

    LOG.info("Loading scene or product...")
    gridded_scene = GriddedScene.load(args.scene)
    if args.products and isinstance(gridded_scene, GriddedScene):
        for k in gridded_scene.keys():
            if k not in args.products:
                del gridded_scene[k]

    LOG.info("Initializing backend...")
    backend = Backend(**args.subgroup_args["Backend Initialization"])
    if isinstance(gridded_scene, GriddedScene):
        backend.create_output_from_scene(gridded_scene, **args.subgroup_args["Backend Output Creation"])
    elif isinstance(gridded_scene, GriddedProduct):
        backend.create_output_from_product(gridded_scene, **args.subgroup_args["Backend Output Creation"])
    else:
        raise ValueError("Unknown Polar2Grid object provided")

if __name__ == '__main__':
    sys.exit(main())
