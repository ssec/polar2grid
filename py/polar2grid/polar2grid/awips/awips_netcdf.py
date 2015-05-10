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
from polar2grid.nc import create_nc_from_ncml
from polar2grid.core.rescale import Rescaler, DEFAULT_RCONFIG
from polar2grid.core.dtype import clip_to_data_type, DTYPE_UINT8
from .awips_config import AWIPS2ConfigReader, CONFIG_FILE as DEFAULT_AWIPS_CONFIG, NoSectionError
from netCDF4 import Dataset
import numpy

import os
import sys
import logging
import calendar

LOG = logging.getLogger(__name__)


def create_netcdf(nc_name, image, template, start_dt, channel, source, sat_name):
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
        LOG.warning("Expected file format NETCDF3_CLASSIC got %s" % (nc.file_format,))

    image_var = nc.variables["image"]
    if image_var.shape != image.shape:
        LOG.error("Image shapes aren't equal, expected %s got %s" % (str(image_var.shape), str(image.shape)))
        raise ValueError("Image shapes aren't equal, expected %s got %s" % (str(image_var.shape), str(image.shape)))

    # Convert to signed byte keeping large values large
    image = clip_to_data_type(image, DTYPE_UINT8)

    image_var[:] = image
    time_var = nc.variables["validTime"]
    time_var[:] = float(calendar.timegm(start_dt.utctimetuple())) + float(start_dt.microsecond)/1e6

    # Add AWIPS 2 global attributes
    nc.channel = channel
    nc.source = source
    nc.satelliteName = sat_name

    nc.sync()  # Just in case
    nc.close()
    LOG.debug("Data transferred into NC file correctly")


# INI files ignore case on options, so we have to do this
GRID_ATTR_NAME = {
    "projname": "projName",
    "projindex": "projIndex",
    "lat00": "lat00",
    "lon00": "lon00",
    "latnxny": "latNxNy",
    "lonnxny": "lonNxNy",
    "centrallat": "centralLat",
    "centrallon": "centralLon",
    "latdxdy": "latDxDy",
    "londxdy": "lonDxDy",
    "dykm": "dyKm",
    "dxkm": "dxKm",
    "rotation": "rotation",
}
GRID_ATTR_TYPE = {
    "projindex": numpy.int32,
    "lat00": numpy.float32,
    "lon00": numpy.float32,
    "latnxny": numpy.float32,
    "lonnxny": numpy.float32,
    "centrallat": numpy.float32,
    "centrallon": numpy.float32,
    "latdxdy": numpy.float32,
    "londxdy": numpy.float32,
    "dykm": numpy.float32,
    "dxkm": numpy.float32,
    "rotation": numpy.float32,
    }

def create_awips2_netcdf3(filename, image, start_dt,
                          depictor_name, channel, source_name, satellite_name,
                          **grid_info):
    nc_name = os.path.abspath(filename)
    nc = Dataset(nc_name, mode='w', format="NETCDF3_CLASSIC")
    y_dim = nc.createDimension("y", size=image.shape[0])
    x_dim = nc.createDimension("x", size=image.shape[1])

    time_var = nc.createVariable("validTime", "f8")
    time_var.units = "seconds since 1970-1-1 00:00:00.00 0:00"
    time_var[:] = float(calendar.timegm(start_dt.utctimetuple())) + float(start_dt.microsecond)/1e6

    image_var = nc.createVariable("image", "i1", ("y", "x"))
    image_var.set_auto_maskandscale(False)
    image_var[:] = clip_to_data_type(image, DTYPE_UINT8)

    nc.depictorName = depictor_name
    nc.channel = channel
    nc.source = source_name
    nc.satelliteName = satellite_name

    for k, v in grid_info.items():
        attr_name = GRID_ATTR_NAME.get(k, k)
        attr_type = GRID_ATTR_TYPE.get(k, None)
        LOG.debug("Setting grid information for NetCDF file: %s -> %s", attr_name, v)
        if attr_type is not None:
            v = attr_type(v)
        setattr(nc, attr_name, v)

    nc.sync()
    nc.close()
    LOG.debug("Data transferred into NC file correctly")


class Backend(roles.BackendRole):
    def __init__(self, backend_configs=None, rescale_configs=None, **kwargs):
        backend_configs = backend_configs or [DEFAULT_AWIPS_CONFIG]
        rescale_configs = rescale_configs or [DEFAULT_RCONFIG]
        self.awips_config_reader = AWIPS2ConfigReader(*backend_configs)
        self.rescaler = Rescaler(*rescale_configs, **kwargs)
        super(Backend, self).__init__(**kwargs)

    @property
    def known_grids(self):
        return self.awips_config_reader.known_grids

    def create_output_from_product(self, gridded_product, **kwargs):
        data_type = DTYPE_UINT8
        inc_by_one = False
        fill_value = 0
        grid_def = gridded_product["grid_definition"]

        # awips_info = self.awips_config_reader.get_product_options(gridded_product)
        try:
            awips_info = self.awips_config_reader.get_product_info(gridded_product)
        except NoSectionError as e:
            LOG.error("Could not get information on product from backend configuration file")
            # NoSectionError is not a "StandardError" so it won't be caught normally
            raise RuntimeError(e.message)

        try:
            awips_info.update(self.awips_config_reader.get_grid_info(grid_def))
        except NoSectionError as e:
            LOG.error("Could not get information on grid from backend configuration file")
            # NoSectionError is not a "StandardError" so it won't be caught normally
            raise RuntimeError(e.msg)

        if "filename_scheme" in awips_info:
            # Let individual products have special names if needed (mostly for weird product naming)
            fn_format = awips_info.pop("filename_scheme")
        else:
            fn_format = self.awips_config_reader.get_filename_format()

        output_filename = self.create_output_filename(fn_format,
                                                       grid_name=grid_def["grid_name"],
                                                       rows=grid_def["height"],
                                                       columns=grid_def["width"],
                                                       **gridded_product)

        if os.path.isfile(output_filename):
            if not self.overwrite_existing:
                LOG.error("AWIPS file already exists: %s", output_filename)
                raise RuntimeError("AWIPS file already exists: %s" % (output_filename,))
            else:
                LOG.warning("AWIPS file already exists, will overwrite: %s", output_filename)

        # Create the netcdf file
        try:
            LOG.info("Scaling %s data to fit in netcdf file...", gridded_product["product_name"])
            data = self.rescaler.rescale_product(gridded_product, data_type,
                                                 inc_by_one=inc_by_one, fill_value=fill_value)

            LOG.info("Writing product %s to AWIPS NetCDF file", gridded_product["product_name"])
            create_awips2_netcdf3(output_filename, data, gridded_product["begin_time"], **awips_info)
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
    # group = parser.add_argument_group(title="Backend Output Creation")
    # group.add_argument("--ncml-template",
    #                    help="alternative AWIPS ncml template file from what is configured")
    return ["Backend Initialization"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    from polar2grid.core.containers import GriddedScene, GriddedProduct
    parser = create_basic_parser(description="Create AWIPS compatible NetCDF files")
    subgroup_titles = add_backend_argument_groups(parser)
    parser.add_argument("--scene", required=True, help="JSON SwathScene filename to be remapped")
    parser.add_argument("-p", "--products", nargs="*", default=None,
                        help="Specify only certain products from the provided scene")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(subgroup_titles=subgroup_titles, global_keywords=global_keywords)

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
