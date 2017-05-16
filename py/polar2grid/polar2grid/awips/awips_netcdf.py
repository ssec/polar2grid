#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2012-2015 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
#     input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    October 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""The AWIPS backend is used to create AWIPS compatible NetCDF files.
The Advanced Weather Interactive Processing System (AWIPS) is a program used
by the United States National Weather Service (NWS) and others to view
different forms of weather imagery. Once AWIPS is configured for specific products
the AWIPS NetCDF backend can be used to provide compatible products to the
system. The files created by this backend are compatible with AWIPS II (AWIPS I is no
longer supported).

The AWIPS NetCDF backend takes remapped binary image data and creates an
AWIPS-compatible NetCDF 3 file.  To accomplish this the backend must rescale
the image data to a 0-255 range, where 0 is a fill/invalid value.  AWIPS
requires unsigned byte integers for its data which results in this range.
It then fills in a NetCDF file template with the rescaled image data.

Rescaling will attempt to fit the provided data in the best visual range for
AWIPS, but can not always do this for outliers.  To correct for this the
AWIPS NetCDF backend also clips any post-rescaling values above 255 to 255
and any values below 0 to 0.  This could result in "washed out" portions of
data in the AWIPS NetCDF file.

Both the AWIPS backend and the AWIPS client must be configured to handle certain
products over certain grids. By default the AWIPS backend is configured with the
`AWIPS configuration file <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid/polar2grid/awips/awips_grids.conf>`_
that comes with Polar2Grid. This following AWIPS grids are supported in Polar2Grid:

    +-------------+----------------------------+
    | Grid Name   | Description                |
    +=============+============================+
    | 211e        | East CONUS                 |
    +-------------+----------------------------+
    | 211w        | West CONUS                 |
    +-------------+----------------------------+
    | 203         | Alaska                     |
    +-------------+----------------------------+
    | 204         | Hawaii                     |
    +-------------+----------------------------+
    | 210         | Puerto Rico                |
    +-------------+----------------------------+

 .. warning::

     The AWIPS backend does not default to using a specfic grid; the software will create
     reprojected NetCDF files for any AWIPS grid that the data overlays. Therefore, 
     it is recommended to specify one or more grids for remapping by using the `-g` flag.

"""
__docformat__ = "restructuredtext en"

import sys
from netCDF4 import Dataset

import calendar
import logging
import numpy
import os
from polar2grid.core.rescale import Rescaler, DEFAULT_RCONFIG
from polar2grid.core.dtype import clip_to_data_type, DTYPE_UINT8
from polar2grid.core import roles

from polar2grid.awips.awips_config import AWIPS2ConfigReader, CONFIG_FILE as DEFAULT_AWIPS_CONFIG, NoSectionError

LOG = logging.getLogger(__name__)

DEFAULT_OUTPUT_PATTERN = '{source_name}_AWIPS_{satellite}_{instrument}_{product_name}_{grid_name}_{begin_time}.nc'

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

    def create_output_from_product(self, gridded_product, output_pattern=None,
                                   source_name=None, **kwargs):
        data_type = DTYPE_UINT8
        inc_by_one = False
        fill_value = 0
        grid_def = gridded_product["grid_definition"]

        try:
            awips_info = self.awips_config_reader.get_product_info(gridded_product)
            if source_name:
                awips_info['source_name'] = source_name
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

        if not output_pattern:
            if "filename_scheme" in awips_info:
                # Let individual products have special names if needed (mostly for weird product naming)
                output_pattern = awips_info.pop("filename_scheme")
            else:
                output_pattern = self.awips_config_reader.get_filename_format(default=DEFAULT_OUTPUT_PATTERN)

        if "{" in output_pattern:
            # format the filename
            of_kwargs = gridded_product.copy(as_dict=True)
            of_kwargs["data_type"] = data_type
            output_filename = self.create_output_filename(output_pattern,
                                                          grid_name=grid_def["grid_name"],
                                                          rows=grid_def["height"],
                                                          columns=grid_def["width"],
                                                          source_name=awips_info.get('source_name'),
                                                          **gridded_product)
        else:
            output_filename = output_pattern

        if os.path.isfile(output_filename):
            if not self.overwrite_existing:
                LOG.error("AWIPS file already exists: %s", output_filename)
                raise RuntimeError("AWIPS file already exists: %s" % (output_filename,))
            else:
                LOG.warning("AWIPS file already exists, will overwrite: %s", output_filename)

        # Create the netcdf file
        try:
            LOG.debug("Scaling %s data to fit in netcdf file...", gridded_product["product_name"])
            data = self.rescaler.rescale_product(gridded_product, data_type,
                                                 inc_by_one=inc_by_one, fill_value=fill_value, clip_zero=True)

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
    group = parser.add_argument_group(title="Backend Output Creation")
    # group.add_argument("--ncml-template",
    #                    help="alternative AWIPS ncml template file from what is configured")
    group.add_argument("--output-pattern", default=DEFAULT_OUTPUT_PATTERN,
                       help="output filenaming pattern")
    group.add_argument("--source-name", default='SSEC',
                       help="specify processing source name used in attributes and filename (default 'SSEC')")
    return ["Backend Initialization", "Backend Output Creation"]


def main():
    from polar2grid.core import create_basic_parser, create_exc_handler, setup_logging
    from polar2grid.core import GriddedScene, GriddedProduct
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
