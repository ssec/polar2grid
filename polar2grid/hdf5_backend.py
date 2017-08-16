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
#     input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    December 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""The HDF5 backend creates HDF5 files with gridded products. By default it creates
one HDF5 file with all products in the same file. Products are grouped together in
HDF5 data groups for the grid that they are remapped to. Each grid data group has
attributes describing the grid it represents. See the command line arguments for
this backend for information on compressing the HDF5 files and including longitude
and latitude datasets in the files.

"""
__docformat__ = "restructuredtext en"


import sys

import h5py
import logging
import os

from polar2grid.core.rescale import Rescaler, DEFAULT_RCONFIG
from polar2grid.core import roles

LOG = logging.getLogger(__name__)
DEFAULT_OUTPUT_PATTERN = "{satellite}_{instrument}_{begin_time}.h5"


class Backend(roles.BackendRole):
    def __init__(self, rescale_configs=None, **kwargs):
        self.rescale_configs = rescale_configs or [DEFAULT_RCONFIG]
        self.rescaler = Rescaler(*self.rescale_configs)
        super(Backend, self).__init__(**kwargs)

    @property
    def known_grids(self):
        # should work regardless of grid
        return None

    def determine_output_filename(self, gridded_scene, output_pattern=None):
        if "grid_definition" in gridded_scene:
            grid_def = gridded_scene["grid_definition"]
            gridded_product = gridded_scene
        else:
            k = gridded_scene.keys()[0]
            grid_def = gridded_scene[k]["grid_definition"]
            gridded_product = gridded_scene[k]

        if not output_pattern:
            output_pattern = DEFAULT_OUTPUT_PATTERN
        if "{" in output_pattern:
            # format the filename
            of_kwargs = gridded_product.copy(as_dict=True)
            # of_kwargs["data_type"] = data_type
            output_filename = self.create_output_filename(output_pattern,
                                                          grid_name=grid_def["grid_name"],
                                                          rows=grid_def["height"],
                                                          columns=grid_def["width"],
                                                          **of_kwargs)
        else:
            output_filename = output_pattern

        return output_filename

    def create_output_from_scene(self, gridded_scene, **kwargs):
        kwargs["compression"] = kwargs.get("compression", None)
        if kwargs["compression"] == "none":
            kwargs["compression"] = None

        output_filename = self.determine_output_filename(gridded_scene, output_pattern=kwargs["output_pattern"])
        # get all of the grids in this gridded scene, should only be one in most cases
        grids = {x["grid_definition"]["grid_name"]: x["grid_definition"] for x in gridded_scene.values()}

        try:
            h = self.create_hdf5_file(output_filename, append=kwargs.get("append", True))
        except ValueError:
            LOG.error("Could not create hdf5 file: %s", output_filename)
            raise

        for grid_name, grid_definition in grids.items():
            h5_group = self.create_group_from_grid_definition(grid_definition, h, **kwargs)

            for product_name, gridded_product in gridded_scene.items():
                try:
                    LOG.info("Creating HDF5 output for product: %s", product_name)
                    self.create_output_from_product(gridded_product, parent=h5_group, **kwargs)
                except ValueError:
                    LOG.error("Could not create output for '%s'", product_name)
                    if self.exit_on_error:
                        raise
                    LOG.debug("Backend exception: ", exc_info=True)
                    continue

        h.close()
        return [output_filename]

    def create_group_from_grid_definition(self, grid_definition, parent, add_geolocation=False, **kwargs):
        if grid_definition["grid_name"] in parent:
            return parent[grid_definition["grid_name"]]

        group = parent.create_group(grid_definition["grid_name"])
        for a in ["proj4_definition", "height", "width", "cell_height", "cell_width", "origin_x", "origin_y"]:
            group.attrs[a] = grid_definition[a]

        if add_geolocation:
            LOG.info("Adding geolocation 'longitude' and 'latitude' datasets for grid %s", grid_definition["grid_name"])
            lon_data, lat_data = grid_definition.get_geolocation_arrays()
            group.create_dataset("longitude", shape=lon_data.shape, dtype=lon_data.dtype, data=lon_data,
                                 compression=kwargs["compression"])
            group.create_dataset("latitude", shape=lat_data.shape, dtype=lat_data.dtype, data=lat_data,
                                 compression=kwargs["compression"])

        return group

    def create_hdf5_file(self, output_filename, append=True):
        if os.path.isfile(output_filename):
            if append:
                LOG.info("Will append to existing file: %s", output_filename)
                mode = "a"
            elif not self.overwrite_existing:
                LOG.error("HDF5 file already exists: %s", output_filename)
                raise RuntimeError("HDF5 file already exists: %s" % (output_filename,))
            else:
                LOG.warning("HDF5 file already exists, will overwrite/truncate: %s", output_filename)
                mode = "w"
        else:
            LOG.info("Creating HDF5 file: %s", output_filename)
            mode = "w"

        h5_group = h5py.File(output_filename, mode)
        return h5_group

    def create_output_from_product(self, gridded_product, parent=None, append=True,
                                   output_pattern=None, data_type=None, inc_by_one=None, fill_value=0, **kwargs):
        if data_type is not None:
            raise NotImplementedError("Specifying alternate data type is not supported in HDF5 backend yet")
        # data_type = data_type or gridded_product["data_type"]
        # inc_by_one = inc_by_one or False
        kwargs["compression"] = kwargs.get("compression", None)
        if kwargs["compression"] == "none":
            kwargs["compression"] = None

        output_filename = None
        if parent is None:
            output_filename = self.determine_output_filename(gridded_product, output_pattern=output_pattern)
            parent = self.create_hdf5_file(output_filename, append=append)

        try:
            # Create the dataset
            data = gridded_product.get_data_array()
            product_name = gridded_product["product_name"]
            if product_name in parent:
                LOG.warning("Product %s already exists in hdf5 group, will delete existing dataset", product_name)
                del parent[product_name]
            LOG.info("Creating dataset '%s'...", product_name)
            ds = parent.create_dataset(product_name, shape=gridded_product.shape,
                                         dtype=gridded_product["data_type"], data=data,
                                         compression=kwargs["compression"])

            for a in ["satellite", "instrument"]:
                ds.attrs[a] = gridded_product[a]
            ds.attrs["begin_time"] = gridded_product["begin_time"].isoformat()
            ds.attrs["end_time"] = gridded_product["end_time"].isoformat()
        except ValueError:
            if not self.keep_intermediate and output_filename and os.path.isfile(output_filename):
                os.remove(output_filename)
            raise

        return output_filename


def add_backend_argument_groups(parser):
    parser.set_defaults(forced_grids=["wgs84_fit"])
    group = parser.add_argument_group(title="Backend Initialization")
    group.add_argument('--rescale-configs', nargs="*", dest="rescale_configs",
                       help="alternative rescale configuration files")
    group = parser.add_argument_group(title="Backend Output Creation")
    group.add_argument("--output-pattern", default=DEFAULT_OUTPUT_PATTERN,
                       help="output filenaming pattern")
    # group.add_argument('--dont-inc', dest="inc_by_one", default=True, action="store_false",
    #                    help="do not increment data by one (ex. 0-254 -> 1-255 with 0 being fill)")
    group.add_argument("--compress", dest="compression", default="none", choices=["none", "gzip", "lzf", "szip"],
                       help="Specify compression method for hdf5 datasets")
    group.add_argument("--no-append", dest="append", action="store_false",
                       help="Don't append to the hdf5 file if it already exists (otherwise may overwrite data)")
    group.add_argument("--add-geolocation", dest="add_geolocation", action="store_true",
                       help="Add 'longitude' and 'latitude' datasets for each grid")
    # group.add_argument("--dtype", dest="data_type", type=str_to_dtype, default=None,
    #                     help="specify the data type for the backend to output")
    return ["Backend Initialization", "Backend Output Creation"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    from polar2grid.core.containers import GriddedScene, GriddedProduct
    parser = create_basic_parser(description="Create HDF5 files from provided gridded scene or product data")
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
