#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2016 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    March 2016
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""SatPy compatible readers and legacy P2G frontends to wrap them.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2016 University of Wisconsin SSEC. All rights reserved.
:date:         Mar 2016
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

import sys

import logging
import numpy as np
import os
from pyresample.geometry import AreaDefinition
from satpy.scene import Scene
import dask.array as da

from polar2grid.core import containers, roles

LOG = logging.getLogger(__name__)


def area_to_swath_def(area, overwrite_existing=False):
    lons = area.lons
    lats = area.lats
    name = area.name
    name = name.replace(":", "")
    if lons.ndim == 1:
        rows, cols = lons.shape[0], 1
    else:
        rows, cols = lons.shape
    info = {
        "swath_name": name,
        "longitude": name + "_lon.dat",
        "latitude": name + "_lat.dat",
        "swath_rows": rows,
        "swath_columns": cols,
        "data_type": lons.dtype,
        "fill_value": np.nan,
    }
    if hasattr(area, "attrs"):
        info.update(area.attrs)

    # Write lons to disk
    filename = info["longitude"]
    if os.path.isfile(filename):
        if not overwrite_existing:
            LOG.error("Binary file already exists: %s" % (filename,))
            raise RuntimeError("Binary file already exists: %s" % (filename,))
        else:
            LOG.warning("Binary file already exists, will overwrite: %s", filename)
    LOG.info("Writing longitude data to disk cache...")
    lon_arr = np.memmap(filename, mode="w+", dtype=lons.dtype, shape=lons.shape)
    da.store(lons.data, lon_arr)

    # Write lats to disk
    filename = info["latitude"]
    if os.path.isfile(filename):
        if not overwrite_existing:
            LOG.error("Binary file already exists: %s" % (filename,))
            raise RuntimeError("Binary file already exists: %s" % (filename,))
        else:
            LOG.warning("Binary file already exists, will overwrite: %s", filename)
    LOG.info("Writing latitude data to disk cache...")
    lat_arr = np.memmap(filename, mode="w+", dtype=lats.dtype, shape=lats.shape)
    da.store(lats.data, lat_arr)
    return containers.SwathDefinition(**info)


def area_to_grid_definition(area, overwrite_existing=False):
    if isinstance(area, AreaDefinition):
        return containers.GridDefinition(
            grid_name=area.name,
            proj4_definition=area.proj4_string,
            cell_width=area.pixel_size_x,
            cell_height=-abs(area.pixel_size_y),
            width=area.x_size,
            height=area.y_size,
            origin_x=area.area_extent[0] + area.pixel_size_x / 2.,
            origin_y=area.area_extent[3] - area.pixle_size_y / 2.,
        )
    else:
        # assume we have a SwathDefinition, in which case we are
        # estimating a grid definition
        lons, lats = area.get_lonlats()
        return containers.GridDefinition(
            grid_name="sensor",
            proj4_definition="+proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs",
            cell_width=lons[0, 1] - lons[0, 0],
            cell_height=-abs(lats[1, 0] - lats[0, 0]),
            width=lons.shape[1],
            height=lons.shape[0],
            origin_x=lons[0, 0],
            origin_y=lats[0, 0],
        )


def dataarray_to_swath_product(ds, swath_def, overwrite_existing=False):
    info = ds.attrs.copy()
    info.pop("area")
    if ds.ndim == 3:
        # RGB composite
        if ds.shape[0] in [3, 4]:
            channels = ds.shape[0]
        else:
            # unpreferred array orientation
            channels = ds.shape[-1]
            ds = np.rollaxis(ds, 2)
    else:
        channels = 1

    if ds.ndim == 1:
        rows, cols = ds.shape[0], 1
    else:
        rows, cols = ds.shape[-2:]
    if np.issubdtype(np.dtype(ds.dtype), np.floating):
        dtype = np.float32
    else:
        dtype = ds.dtype

    if isinstance(info["sensor"], bytes):
        info["sensor"] = info["sensor"].decode("utf-8")

    p2g_metadata = {
        "product_name": info["name"],
        "satellite": info["platform_name"].lower(),
        "instrument": info["sensor"].lower() if isinstance(info["sensor"], str) else list(info["sensor"])[0].lower(),
        "data_kind": info["standard_name"],
        "begin_time": info["start_time"],
        "end_time": info["end_time"],
        "fill_value": np.nan,
        "swath_columns": cols,
        "swath_rows": rows,
        "rows_per_scan": info.get("rows_per_scan", rows),
        "data_type": dtype,
        "swath_definition": swath_def,
        "channels": channels,
    }

    info.update(p2g_metadata)

    if channels == 1:
        filename = info["name"] + ".dat"
        info["swath_data"] = filename
        if os.path.isfile(filename):
            if not overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)
        LOG.info("Writing band data to disk cache...")
        p2g_arr = np.memmap(filename, mode="w+", dtype=dtype, shape=ds.shape)
        ds = ds.where(ds.notnull(), np.nan)
        da.store(ds.data.astype(dtype), p2g_arr)
        yield containers.SwathProduct(**info)
    else:
        for chn_idx in range(channels):
            tmp_info = info.copy()
            tmp_info["product_name"] = info["product_name"] + "_rgb_{:d}".format(chn_idx)
            filename = tmp_info["product_name"] + ".dat"
            tmp_info["swath_data"] = filename
            if os.path.isfile(filename):
                if not overwrite_existing:
                    LOG.error("Binary file already exists: %s" % (filename,))
                    raise RuntimeError("Binary file already exists: %s" % (filename,))
                else:
                    LOG.warning("Binary file already exists, will overwrite: %s", filename)
            LOG.info("Writing band data to disk cache...")
            p2g_arr = np.memmap(filename, mode="w+", dtype=dtype, shape=ds.shape[-2:])
            da.store(ds.data[chn_idx].astype(dtype), p2g_arr)
            yield containers.SwathProduct(**tmp_info)


def dataarray_to_gridded_product(ds, grid_def, overwrite_existing=False):
    info = ds.attrs.copy()
    info.pop("area", None)
    if ds.ndim == 3:
        # RGB composite
        if ds.shape[0] in [3, 4]:
            channels = ds.shape[0]
        else:
            # unpreferred array orientation
            channels = ds.shape[-1]
            ds = np.rollaxis(ds, 2)
    else:
        channels = 1

    if np.issubdtype(np.dtype(ds.dtype), np.floating):
        dtype = np.float32
    else:
        dtype = ds.dtype

    p2g_metadata = {
        "product_name": info["name"],
        "satellite": info["platform_name"].lower(),
        "instrument": info["sensor"].lower() if isinstance(info["sensor"], str) else list(info["sensor"])[0].lower(),
        "data_kind": info["standard_name"],
        "begin_time": info["start_time"],
        "end_time": info["end_time"],
        "fill_value": np.nan,
        # "swath_columns": cols,
        # "swath_rows": rows,
        "rows_per_scan": info["rows_per_scan"],
        "data_type": dtype,
        "channels": channels,
        "grid_definition": grid_def,
    }
    info.update(p2g_metadata)

    filename = info["name"] + ".dat"
    info["grid_data"] = filename
    if os.path.isfile(filename):
        if not overwrite_existing:
            LOG.error("Binary file already exists: %s" % (filename,))
            raise RuntimeError("Binary file already exists: %s" % (filename,))
        else:
            LOG.warning("Binary file already exists, will overwrite: %s", filename)
    p2g_arr = np.memmap(filename, mode="w+", dtype=dtype, shape=ds.shape)
    da.store(ds.data.astype(dtype), p2g_arr)
    return containers.GriddedProduct(**info)


def convert_satpy_to_p2g_swath(frontend, scene):
    p2g_scene = containers.SwathScene()
    overwrite_existing = frontend.overwrite_existing
    areas = {}
    for ds in scene:
        a = ds.attrs['area']
        area_name = getattr(a, 'name', None)
        if area_name is None:
            # generate an identifying name
            a.name = area_name = "{}_{}".format(a.lons.attrs['name'], a.lats.attrs['name'])
        if area_name in areas:
            swath_def = areas[area_name]
        else:
            areas[area_name] = swath_def = area_to_swath_def(ds.attrs["area"], overwrite_existing=overwrite_existing)
            def_rps = ds.shape[0] if ds.ndim <= 2 else ds.shape[-2]
            swath_def.setdefault("rows_per_scan", ds.attrs.get("rows_per_scan", def_rps))

        for swath_product in dataarray_to_swath_product(ds, swath_def, overwrite_existing=overwrite_existing):
            p2g_scene[swath_product["product_name"]] = swath_product

    return p2g_scene


def convert_satpy_to_p2g_gridded(frontend, scene):
    p2g_scene = containers.GriddedScene()
    overwrite_existing = frontend.overwrite_existing
    areas = {}
    for ds in scene:
        if ds.attrs["area"].name in areas:
            grid_def = areas[ds.attrs["area"].name]
        else:
            areas[ds.attrs["area"].name] = grid_def = area_to_grid_definition(ds.attrs["area"],
                                                                             overwrite_existing=overwrite_existing)
        gridded_product = dataarray_to_gridded_product(ds, grid_def, overwrite_existing=overwrite_existing)
        p2g_scene[gridded_product["name"]] = gridded_product

    return p2g_scene


class ReaderWrapper(roles.FrontendRole):
    FILE_EXTENSIONS = []
    DEFAULT_READER_NAME = None
    DEFAULT_DATASETS = []
    # This is temporary until a better solution is found for loading start/end time on init
    PRIMARY_FILE_TYPE = None

    def __init__(self, **kwargs):
        self.reader = kwargs.pop("reader", self.DEFAULT_READER_NAME)
        super(ReaderWrapper, self).__init__(**kwargs)
        pathnames = self.find_files_with_extensions()
        # Remove keyword arguments that Satpy won't understand
        for key in ('search_paths', 'keep_intermediate',
                    'overwrite_existing', 'exit_on_error'):
            kwargs.pop(key, None)
        # Create a satpy Scene object
        self.scene = Scene(reader=self.reader, filenames=pathnames, reader_kwargs=kwargs)
        self._begin_time = self.scene.start_time
        self._end_time = self.scene.end_time
        self.wishlist = set()

    @property
    def begin_time(self):
        return self._begin_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def available_product_names(self):
        return self.scene.available_dataset_names(reader_name=self.reader, composites=True)

    @property
    def all_product_names(self):
        return self.scene.all_dataset_names(reader_name=self.reader, composites=True)

    @property
    def default_products(self):
        return self.DEFAULT_DATASETS

    def filter(self, scene):
        pass

    def create_scene(self, products=None, **kwargs):
        LOG.debug("Loading scene data...")
        # If the user didn't provide the products they want, figure out which ones we can create
        if products is None:
            LOG.debug("No products specified to frontend, will try to load logical defaults products")
            products = self.default_products

        kwargs.pop("overwrite_existing")
        kwargs.pop("exit_on_error")
        kwargs.pop("keep_intermediate")
        self.scene.load(products, **kwargs)
        self.wishlist = self.scene.wishlist

        # Apply Filters
        self.filter(self.scene)

        # Delete the satpy scene so memory is cleared out if it isn't used by the caller
        scene = self.scene
        self.scene = None
        return scene


def main(description=None, add_argument_groups=None):
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    parser = create_basic_parser(description=description)
    subgroup_titles = add_argument_groups(parser)
    parser.add_argument('-f', dest='data_files', nargs="+", default=[],
                        help="List of data files or directories to extract data from")
    parser.add_argument('-o', dest="output_filename", default=None,
                        help="Output filename for JSON scene (default is to stdout)")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(subgroup_titles=subgroup_titles, global_keywords=global_keywords)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)
    LOG.debug("Starting script with arguments: %s", " ".join(sys.argv))

    list_products = args.subgroup_args["Frontend Initialization"].pop("list_products")
    f = ReaderWrapper(search_paths=args.data_files, **args.subgroup_args["Frontend Initialization"])

    if list_products:
        print("\n".join(f.available_product_names))
        return 0

    if args.output_filename and os.path.isfile(args.output_filename):
        LOG.error("JSON file '%s' already exists, will not overwrite." % (args.output_filename,))
        raise RuntimeError("JSON file '%s' already exists, will not overwrite." % (args.output_filename,))

    scene = f.create_scene(**args.subgroup_args["Frontend Swath Extraction"])
    json_str = scene.dumps(persist=True)
    if args.output_filename:
        with open(args.output_filename, 'w') as output_file:
            output_file.write(json_str)
    else:
        print(json_str)
    return 0

