#!/usr/bin/env python3
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
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    January 2013
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""The Binary backend is a very simple backend that outputs the gridded data in
a flat binary file for each band of data. The binary writer supports data on any grid.
"""
__docformat__ = "restructuredtext en"

import sys

import logging
import numpy
import os
import shutil

from polar2grid.core import roles
from polar2grid.core.dtype import str_to_dtype, clip_to_data_type
from polar2grid.core.rescale import Rescaler, DEFAULT_RCONFIG

LOG = logging.getLogger(__name__)
DEFAULT_OUTPUT_PATTERN = "{satellite}_{instrument}_{product_name}_{begin_time}_{grid_name}.dat"


class Backend(roles.BackendRole):
    """Simple backend for renaming or rescaling binary files created from remapping.

    Rescale configuration files are only used for non-float data types.
    """
    def __init__(self, rescale_configs=None, **kwargs):
        self.rescale_configs = rescale_configs or [DEFAULT_RCONFIG]
        self.rescaler = Rescaler(*self.rescale_configs)
        super(Backend, self).__init__(**kwargs)

    @property
    def known_grids(self):
        # should work regardless of grid
        return None

    def create_output_from_product(self, gridded_product, output_pattern=None,
                                   data_type=None, inc_by_one=None, fill_value=None, **kwargs):
        inc_by_one = inc_by_one or False
        data_type = data_type or gridded_product["data_type"]
        fill_value = fill_value or gridded_product["fill_value"]
        same_fill = numpy.isnan(fill_value) and numpy.isnan(gridded_product["fill_value"]) or fill_value == gridded_product["fill_value"]
        grid_def = gridded_product["grid_definition"]
        if not output_pattern:
            output_pattern = DEFAULT_OUTPUT_PATTERN
        if "{" in output_pattern:
            # format the filename
            of_kwargs = gridded_product.copy(as_dict=True)
            of_kwargs["data_type"] = data_type
            output_filename = self.create_output_filename(output_pattern,
                                                          grid_name=grid_def["grid_name"],
                                                          rows=grid_def["height"],
                                                          columns=grid_def["width"],
                                                          **of_kwargs)
        else:
            output_filename = output_pattern

        if os.path.isfile(output_filename):
            if not self.overwrite_existing:
                LOG.error("Geotiff file already exists: %s", output_filename)
                raise RuntimeError("Geotiff file already exists: %s" % (output_filename,))
            else:
                LOG.warning("Geotiff file already exists, will overwrite: %s", output_filename)

        # if we have a floating point data type, then scaling doesn't make much sense
        if data_type == gridded_product["data_type"] and same_fill:
            LOG.info("Saving product %s to binary file %s", gridded_product["product_name"], output_filename)
            shutil.copyfile(gridded_product["grid_data"], output_filename)
            return output_filename
        elif numpy.issubclass_(data_type, numpy.floating):
            # we didn't rescale any data, but we need to convert it
            data = gridded_product.get_data_array()
        else:
            try:
                LOG.debug("Scaling %s data to fit data type", gridded_product["product_name"])
                data = self.rescaler.rescale_product(gridded_product, data_type,
                                                     inc_by_one=inc_by_one, fill_value=fill_value)
                data = clip_to_data_type(data, data_type)
            except ValueError:
                if not self.keep_intermediate and os.path.isfile(output_filename):
                    os.remove(output_filename)
                raise

        LOG.info("Saving product %s to binary file %s", gridded_product["product_name"], output_filename)
        data = data.astype(data_type)
        fill_mask = gridded_product.get_data_mask()
        data[fill_mask] = fill_value
        data.tofile(output_filename)

        return output_filename


def add_backend_argument_groups(parser):
    parser.set_defaults(forced_grids=["wgs84_fit"])
    group = parser.add_argument_group(title="Backend Initialization")
    group.add_argument('--rescale-configs', nargs="*", dest="rescale_configs",
                       help="alternative rescale configuration files")
    group = parser.add_argument_group(title="Backend Output Creation")
    group.add_argument("--output-pattern", default=DEFAULT_OUTPUT_PATTERN,
                       help="output filenaming pattern")
    group.add_argument('--dont-inc', dest="inc_by_one", default=True, action="store_false",
                       help="do not increment data by one (ex. 0-254 -> 1-255 with 0 being fill)")
    group.add_argument("--dtype", dest="data_type", type=str_to_dtype, default=None,
                       help="specify the data type for the backend to output")
    return ["Backend Initialization", "Backend Output Creation"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    from polar2grid.core.containers import GriddedScene, GriddedProduct
    parser = create_basic_parser(description="Create binary files from provided gridded scene or product data")
    subgroup_titles = add_backend_argument_groups(parser)
    parser.add_argument("--scene", required=True, help="JSON SwathScene filename to be remapped")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(subgroup_titles=subgroup_titles, global_keywords=global_keywords)

    # Logs are renamed once data the provided start date is known
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)

    LOG.info("Loading scene or product...")
    gridded_scene = GriddedScene.load(args.scene)

    LOG.info("Initializing backend...")
    backend = Backend(**args.subgroup_args["Backend Initialization"])
    if isinstance(gridded_scene, GriddedScene):
        backend.create_output_from_scene(gridded_scene, **args.subgroup_args["Backend Output Creation"])
    elif isinstance(gridded_scene, GriddedProduct):
        backend.create_output_from_product(gridded_scene, **args.subgroup_args["Backend Output Creation"])
    else:
        raise ValueError("Unknown Polar2Grid object provided")

if __name__ == "__main__":
    sys.exit(main())
