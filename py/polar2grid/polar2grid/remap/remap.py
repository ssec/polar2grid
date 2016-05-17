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
"""Remapping is the process of mapping satellite data swaths to a uniform grid. Mapping
data to a uniform grid makes it easier to view, manipulate, and store the data.
In Polar2Grid, this is usually done using a 2-step process.

Gridding
--------

The first step is called 'll2cr' which stands for "longitude/latitude to
column/row". This step maps the pixel location (lon/lat space) into grid
space. Polar2Grid uses grids defined by a PROJ.4 projection specification.
Other parameters that define a grid like its width and height can be
determined dynamically during this step. A grid is defined by the following parameters:

 - Grid Name
 - PROJ.4 String (either lat/lon or metered projection space)
 - Width (number of pixels in the X direction)
 - Height (number of pixels in the Y direction)
 - Cell Width (pixel size in the X direction in grid units)
 - Cell Height (pixel size in the Y direction in grid units)
 - X Origin (upper-left X coordinate in grid units)
 - Y Origin (upper-left Y coordinate in grid units)

Polar2Grid supports static and dynamic grids. Grids are static if they have all of the
above attributes defined. Grids are dynamic if some of the attributes are not defined.
These attributes are then computed at run time based on the data being remapped. Only
width/height and x/y origin can be unspecified in dynamic grids.

For information on defining your own custom grids see the :doc:`Developer's Guide <dev_guide/grids>`.

Resampling
----------

The second step of remapping is
to resample the input swath pixels to each output grid pixel. Polar2Grid
provides an 'elliptical weight averaging' or 'EWA' resampling method as
well as the traditional nearest neighbor method, with other algorithms
planned for future releases. In the past both of these steps were handled
by third-party software, but have been rewritten to be directly accessed
from python.

.. note::

    The nearest neighbor resampling method (nearest) is experimental and will be
    replaced by a more stable implementation in future releases.


:author:       David Hoese (davidh)
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012-2015 University of Wisconsin SSEC. All rights reserved.
:date:         Oct 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

from polar2grid.core.containers import GriddedProduct, GriddedScene, SwathScene, GridDefinition
from polar2grid.remap import ll2cr as ll2cr  # gridinator
from polar2grid.remap import fornav
from polar2grid.grids import GridManager
from satpy import Scene

import os
import sys
import logging
import signal
from collections import defaultdict
from itertools import izip

import numpy
from scipy.interpolate.interpnd import _ndim_coords_from_arrays
from scipy.spatial import cKDTree

LOG = logging.getLogger(__name__)
SWATH_USAGE = os.environ.get("P2G_SWATH_USAGE", 0)
GRID_COVERAGE = os.environ.get("P2G_GRID_COVERAGE", 0.1)
# resampling 'methods' that accept satpy Scenes instead of P2G scenes
SATPY_RESAMPLERS = ["sensor"]


def mask_helper(arr, fill):
    if numpy.isnan(fill):
        return numpy.isnan(arr)
    else:
        return arr == fill


def init_worker():
    """Used in multiprocessing to initialize pool workers.

    If this isn't done then the listening process will hang forever and
    will have to be killed with the "kill" command even after the outer-most
    process is Ctrl+C'd out of existence.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class Remapper(object):
    def __init__(self, grid_configs=[],
                 overwrite_existing=False, keep_intermediate=False, exit_on_error=True, **kwargs):
        self.grid_manager = GridManager(*grid_configs)
        self.overwrite_existing = overwrite_existing
        self.keep_intermediate = keep_intermediate
        self.exit_on_error = exit_on_error
        self.methods = {
            "ewa": self._remap_scene_ewa,
            "nearest": self._remap_scene_nearest,
            "sensor": self._remap_scene_sensor,
        }
        self.ll2cr_cache = {}

    def highest_resolution_swath_definition(self, swath_scene_or_product):
        if isinstance(swath_scene_or_product, SwathScene):
            swath_defs = [product_def["swath_definition"] for product_def in swath_scene_or_product.values()]
            # choose the highest resolution swath definition navigation (the one with the most columns)
            swath_def = max(swath_defs, key=lambda d: d["swath_columns"])
        else:
            # given a single product
            swath_def = swath_scene_or_product["swath_definition"]
        return swath_def

    def remap_scene(self, swath_scene, grid_name, **kwargs):
        method = kwargs.pop("remap_method", "ewa")
        LOG.debug("Remap scene being run with method '%s'", method)
        if method not in self.methods:
            LOG.error("Unknown remapping method '%s'", method)
            raise ValueError("Unknown remapping method '%s'" % (method,))

        if method == "sensor":
            if grid_name != "sensor":
                raise ValueError("'sensor' resampling only supports the 'sensor' grid")
            else:
                # grid def isn't used by 'sensor' resampling
                grid_def = None
        else:
            grid_def = self.grid_manager.get_grid_definition(grid_name)
        func = self.methods[method]

        # FUTURE: Make this a keyword and add the logic to support it
        if kwargs.get("share_dynamic_grids", True) and method != "sensor":
            # Let's run ll2cr to fill in any parameters we need to and decide if the data fits in the grid
            best_swath_def = self.highest_resolution_swath_definition(swath_scene)
            LOG.debug("Running ll2cr on the highest resolution swath to determine if it fits")
            try:
                self.run_ll2cr(best_swath_def, grid_def, swath_usage=kwargs.get("swath_usage", SWATH_USAGE))
                grid_str = str(grid_def).replace("\n", "\n\t")
                LOG.info("Grid information:\n\t%s", grid_str)
            except StandardError:
                LOG.error("Remapping error")
                raise

        return func(swath_scene, grid_def, **kwargs)

    def run_ll2cr(self, swath_definition, grid_definition, swath_usage=SWATH_USAGE):
        geo_id = swath_definition["swath_name"]
        grid_name = grid_definition["grid_name"]
        if (geo_id, grid_name) in self.ll2cr_cache:
            return self.ll2cr_cache[(geo_id, grid_name)]
        LOG.debug("Swath '%s' -> Grid '%s'", geo_id, grid_name)

        rows_fn = "ll2cr_rows_%s_%s.dat" % (grid_name, geo_id)
        cols_fn = "ll2cr_cols_%s_%s.dat" % (grid_name, geo_id)
        # lon_arr = swath_definition.get_longitude_array()
        # lat_arr = swath_definition.get_latitude_array()

        if os.path.isfile(rows_fn):
            if not self.overwrite_existing:
                LOG.error("Intermediate remapping file already exists: %s" % (rows_fn,))
                raise RuntimeError("Intermediate remapping file already exists: %s" % (rows_fn,))
            else:
                LOG.warning("Intermediate remapping file already exists, will overwrite: %s", rows_fn)
        if os.path.isfile(cols_fn):
            if not self.overwrite_existing:
                LOG.error("Intermediate remapping file already exists: %s" % (cols_fn,))
                raise RuntimeError("Intermediate remapping file already exists: %s" % (cols_fn,))
            else:
                LOG.warning("Intermediate remapping file already exists, will overwrite: %s", cols_fn)
        try:
            rows_arr = swath_definition.copy_latitude_array(filename=rows_fn, read_only=False)
            cols_arr = swath_definition.copy_longitude_array(filename=cols_fn, read_only=False)
            points_in_grid, _, _ = ll2cr.ll2cr(cols_arr, rows_arr, grid_definition,
                                               fill_in=swath_definition["fill_value"])
            grid_str = str(grid_definition).replace("\n", "\n\t")
            LOG.debug("Grid information:\n\t%s", grid_str)
        except StandardError:
            LOG.error("Unexpected error encountered during ll2cr gridding for %s -> %s", geo_id, grid_name)
            LOG.debug("ll2cr error exception: ", exc_info=True)
            self._safe_remove(rows_fn, cols_fn)
            raise

        # if 5% of the grid will have data in it then it fits
        fraction_in = points_in_grid / float(rows_arr.size)
        swath_used = fraction_in > swath_usage
        if not swath_used:
            self._safe_remove(rows_fn, cols_fn)
            LOG.error("Data does not fit in grid %s because it only %f%% of the swath is used" % (grid_name, fraction_in * 100))
            raise RuntimeError("Data does not fit in grid %s" % (grid_name,))
        else:
            LOG.debug("Data fits in grid %s and uses %f%% of the swath", grid_name, fraction_in * 100)

        self.ll2cr_cache[(geo_id, grid_name)] = (cols_fn, rows_fn)
        return cols_fn, rows_fn

    def _add_prefix(self, prefix, *filepaths):
        return [os.path.join(os.path.dirname(x), prefix + os.path.basename(x)) for x in filepaths]

    def _safe_remove(self, *filepaths):
        if not self.keep_intermediate:
            for fp in filepaths:
                if os.path.isfile(fp):
                    try:
                        LOG.debug("Removing intermediate file '%s'...", fp)
                        os.remove(fp)
                    except OSError:
                        LOG.warning("Could not remove intermediate files that aren't needed anymore.")
                        LOG.debug("Intermediate output file remove exception:", exc_info=True)

    def _clear_ll2cr_cache(self):
        # Remove ll2cr files now that we are done with them
        for cols_fn, rows_fn in self.ll2cr_cache.values():
            self._safe_remove(rows_fn, cols_fn)
        self.ll2cr_cache = {}

    def _remap_scene_ewa(self, swath_scene, grid_def, share_dynamic_grids=True, **kwargs):
        # TODO: Make methods more flexible than just a function call
        gridded_scene = GriddedScene()
        grid_name = grid_def["grid_name"]

        # Group products together that shared the same geolocation
        product_groups = defaultdict(list)
        for product_name, swath_product in swath_scene.items():
            swath_def = swath_product["swath_definition"]
            geo_id = swath_def["swath_name"]
            product_groups[geo_id].append(product_name)

        # keep a copy of the original grid definition
        # if a shared grid definition isn't used then
        # we start from the original
        orig_grid_def = grid_def
        for geo_id, product_names in product_groups.items():
            try:
                LOG.debug("Running ll2cr on the geolocation data for the following products:\n\t%s", "\n\t".join(sorted(product_names)))
                swath_def = swath_scene[product_names[0]]["swath_definition"]
                if not share_dynamic_grids:
                    grid_def = orig_grid_def.copy()
                cols_fn, rows_fn = self.run_ll2cr(swath_def, grid_def,
                                                  swath_usage=kwargs.get("swath_usage", SWATH_USAGE))
            except StandardError:
                LOG.error("Remapping error")
                if self.exit_on_error:
                    raise
                continue

            # Run fornav for all of the products at once
            LOG.debug("Running fornav for the following products:\n\t%s", "\n\t".join(sorted(product_names)))
            # XXX: May have to do something smarter if there are float products and integer products together (is_category property on SwathProduct?)
            product_filepaths = list(swath_scene.get_data_filepaths(product_names))
            fornav_filepaths = self._add_prefix("grid_%s_" % (grid_name,), *product_filepaths)
            for fp in fornav_filepaths:
                if os.path.isfile(fp):
                    if not self.overwrite_existing:
                        LOG.error("Intermediate remapping file already exists: %s" % (fp,))
                        raise RuntimeError("Intermediate remapping file already exists: %s" % (fp,))
                    else:
                        LOG.warning("Intermediate remapping file already exists, will overwrite: %s", fp)

            rows_per_scan = swath_def.get("rows_per_scan", 0) or 2
            if rows_per_scan < 2:
                LOG.warning("Data has less than 2 rows per scan, this is not optimal for the EWA resampling algorithm. 2 rows per scan will be used instead")
                rows_per_scan = 2
            edge_res = swath_def.get("limb_resolution", None)
            fornav_D = kwargs.get("fornav_D", None)
            if fornav_D is None:
                if edge_res is not None:
                    if grid_def.is_latlong:
                        fornav_D = (edge_res / 2) / grid_def.cell_width_meters
                    else:
                        fornav_D = (edge_res / 2) / grid_def["cell_width"]
                    LOG.debug("Fornav 'D' option dynamically set to %f", fornav_D)
                else:
                    fornav_D = 10.0

            try:
                # fornav.ms2gt_fornav(
                #     len(product_filepaths),
                #     swath_def["swath_columns"],
                #     swath_def["swath_rows"]/rows_per_scan,
                #     rows_per_scan,
                #     cols_fn,
                #     rows_fn,
                #     product_filepaths,
                #     grid_def["width"],
                #     grid_def["height"],
                #     fornav_filepaths,
                #     swath_data_type_1="f4",
                #     swath_fill_1=swath_scene.get_fill_value(product_names),
                #     grid_fill_1=numpy.nan,
                #     weight_delta_max=fornav_D,
                #     weight_distance_max=kwargs.get("fornav_d", None),
                #     maximum_weight_mode=kwargs.get("maximum_weight_mode", None),
                #     start_scan=(0, 0),
                # )
                cols_array = numpy.memmap(cols_fn, dtype=numpy.float32, mode='r', shape=(swath_def["swath_rows"], swath_def["swath_columns"]))
                rows_array = numpy.memmap(rows_fn, dtype=numpy.float32, mode='r', shape=(swath_def["swath_rows"], swath_def["swath_columns"]))
                # Assumed that all share the same fill value and data type
                input_dtype = [swath_scene[pn]["data_type"] for pn in product_names]
                input_fill = [swath_scene[pn]["fill_value"] for pn in product_names]
                valid_list = fornav.fornav(cols_array,
                              rows_array,
                              rows_per_scan,
                              product_filepaths,
                              input_dtype=input_dtype,
                              input_fill=input_fill,
                              output_arrays=fornav_filepaths,
                              grid_cols=grid_def["width"],
                              grid_rows=grid_def["height"],
                              weight_delta_max=fornav_D,
                              weight_distance_max=kwargs.get("fornav_d", 1.0),
                              maximum_weight_mode=kwargs.get("maximum_weight_mode", False),
                              use_group_size=True
                )
            except StandardError:
                LOG.debug("Remapping exception: ", exc_info=True)
                LOG.error("Remapping error")
                self._safe_remove(*fornav_filepaths)
                if self.exit_on_error:
                    self._clear_ll2cr_cache()
                    raise
                continue

            # Give the gridded product ownership of the remapped data
            for product_name, fornav_fp, valid_points in zip(product_names, fornav_filepaths, valid_list):
                swath_product = swath_scene[product_name]
                gridded_product = GriddedProduct()
                gridded_product.from_swath_product(swath_product)
                gridded_product["grid_definition"] = grid_def
                gridded_product["fill_value"] = numpy.nan
                gridded_product["grid_data"] = fornav_fp

                grid_coverage = kwargs.get("grid_coverage", GRID_COVERAGE)
                grid_covered_ratio = valid_points / float(grid_def["width"] * grid_def["height"])
                grid_covered = grid_covered_ratio > grid_coverage
                if not grid_covered:
                    msg = "EWA resampling only found %f%% of the grid covered (need %f%%) for %s" % (grid_covered_ratio * 100, grid_coverage * 100, product_name)
                    LOG.warning(msg)
                    continue
                LOG.debug("EWA resampling found %f%% of the grid covered for %s" % (grid_covered_ratio * 100, product_name))
                gridded_scene[product_name] = gridded_product

        self._clear_ll2cr_cache()

        if not gridded_scene:
            self._safe_remove(*fornav_filepaths)
            raise RuntimeError("EWA resampling could not remap any of the data to grid '%s'" % (grid_name,))

        return gridded_scene

    def _remap_scene_nearest(self, swath_scene, grid_def, share_dynamic_grids=True, share_remap_mask=True, **kwargs):
        # TODO: Make methods more flexible than just a function call
        gridded_scene = GriddedScene()
        grid_name = grid_def["grid_name"]

        # Group products together that shared the same geolocation
        product_groups = defaultdict(list)
        for product_name, swath_product in swath_scene.items():
            swath_def = swath_product["swath_definition"]
            geo_id = swath_def["swath_name"]
            product_groups[geo_id].append(product_name)

        orig_grid_def = grid_def
        for geo_id, product_names in product_groups.items():
            pp_names = "\n\t".join(product_names)
            LOG.debug("Running ll2cr on the geolocation data for the following products:\n\t%s", pp_names)
            LOG.debug("Swath name: %s", geo_id)

            # TODO: Move into it's own function if this gets complicated
            # TODO: Add some multiprocessing
            try:
                swath_def = swath_scene[product_names[0]]["swath_definition"]
                if not share_dynamic_grids:
                    grid_def = orig_grid_def.copy()
                cols_fn, rows_fn = self.run_ll2cr(swath_def, grid_def)
            except StandardError:
                LOG.error("Remapping error")
                if self.exit_on_error:
                    raise
                continue

            LOG.debug("Running nearest neighbor for the following products:\n\t%s", "\n\t".join(product_names))
            edge_res = swath_def.get("limb_resolution", None)
            if kwargs.get("distance_upper_bound", None) is None:
                if edge_res is not None:
                    if grid_def.is_latlong:
                        distance_upper_bound = (edge_res / 2) / grid_def.cell_width_meters
                    else:
                        distance_upper_bound = (edge_res / 2) / grid_def["cell_width"]
                    LOG.debug("Distance upper bound dynamically set to %f", distance_upper_bound)
                else:
                    distance_upper_bound = 3.0
                kwargs["distance_upper_bound"] = distance_upper_bound

            try:
                grid_x, grid_y = numpy.mgrid[:grid_def["height"], :grid_def["width"]]
                # we need flattened versions of these
                shape = (swath_def["swath_rows"] * swath_def["swath_columns"],)
                cols_array = numpy.memmap(cols_fn, shape=shape, dtype=swath_def["data_type"])
                rows_array = numpy.memmap(rows_fn, shape=shape, dtype=swath_def["data_type"])
                good_mask = ~mask_helper(cols_array, swath_def["fill_value"])
                if share_remap_mask:
                    for product_name in product_names:
                        LOG.debug("Combining data masks before building KDTree for nearest neighbor: %s", product_name)
                        good_mask &= ~swath_scene[product_name].get_data_mask().ravel()
                x = _ndim_coords_from_arrays((cols_array[good_mask], rows_array[good_mask]))
                xi = _ndim_coords_from_arrays((grid_y, grid_x))
                dist, i = cKDTree(x).query(xi, distance_upper_bound=kwargs["distance_upper_bound"])
            except StandardError:
                LOG.debug("Remapping exception: ", exc_info=True)
                LOG.error("Remapping error")
                if self.exit_on_error:
                    self._clear_ll2cr_cache()
                    raise
                continue

            product_filepaths = swath_scene.get_data_filepaths(product_names)
            output_filepaths = self._add_prefix("grid_%s_" % (grid_name,), *product_filepaths)

            # Prepare the products
            fill_value = numpy.nan
            for product_name, output_fn in izip(product_names, output_filepaths):
                LOG.debug("Running nearest neighbor on '%s' with search distance %f", product_name, kwargs["distance_upper_bound"])
                if os.path.isfile(output_fn):
                    if not self.overwrite_existing:
                        LOG.error("Intermediate remapping file already exists: %s" % (output_fn,))
                        raise RuntimeError("Intermediate remapping file already exists: %s" % (output_fn,))
                    else:
                        LOG.warning("Intermediate remapping file already exists, will overwrite: %s", output_fn)

                try:
                    image_array = swath_scene[product_name].get_data_array().ravel()
                    values = numpy.append(image_array[good_mask], image_array.dtype.type(fill_value))
                    output_array = values[i]
                    output_array.tofile(output_fn)

                    # Give the gridded product ownership of the remapped data
                    swath_product = swath_scene[product_name]
                    gridded_product = GriddedProduct()
                    gridded_product.from_swath_product(swath_product)
                    gridded_product["grid_definition"] = grid_def
                    gridded_product["fill_value"] = fill_value
                    gridded_product["grid_data"] = output_fn
                    gridded_scene[product_name] = gridded_product

                    # hopefully force garbage collection
                    del output_array
                except StandardError:
                    LOG.debug("Remapping exception: ", exc_info=True)
                    LOG.error("Remapping error")
                    self._safe_remove(output_fn)
                    if self.exit_on_error:
                        self._clear_ll2cr_cache()
                        raise
                    continue

                LOG.debug("Done running nearest neighbor on '%s'", product_name)


        # Remove ll2cr files now that we are done with them
        self._clear_ll2cr_cache()

        if not gridded_scene:
            raise RuntimeError("Nearest neighbor resampling could not remap any of the data to grid '%s'" % (grid_name,))

        return gridded_scene

    def _remap_scene_sensor(self, swath_scene, grid_def, **kwargs):
        if not isinstance(swath_scene, Scene):
            raise ValueError("'sensor' resampling only supports SatPy scenes")

        new_scn = None
        for area_obj, ds_list in swath_scene.iter_by_area():
            _new_scn = swath_scene.resample(area_obj, datasets=ds_list)
            if new_scn is None:
                new_scn = _new_scn
            for ds in _new_scn:
                new_scn[ds.info["id"]] = ds

        return new_scn

    def remap_product(self, product, grid_name):
        raise NotImplementedError("Single product remapping is not implemented yet")


def add_remap_argument_groups(parser):
    # Let frontends and backends provide defaults, we must "SUPPRESS" the attribute being created
    from argparse import SUPPRESS
    # , default_grids=None, default_fornav_d=1, default_fornav_D=10):
    group = parser.add_argument_group(title="Remapping Initialization")
    group.add_argument('--grid-configs', dest='grid_configs', nargs="+", default=tuple(),
                       help="Specify additional grid configuration files ('grids.conf' for built-ins)")
    group = parser.add_argument_group(title="Remapping")
    group.add_argument('-g', '--grids', dest='forced_grids', nargs="+", default=SUPPRESS,
                       help="Force remapping to only some grids, defaults to 'wgs84_fit', use 'all' for determination")
    group.add_argument("--method", dest="remap_method", default=SUPPRESS, choices=["ewa", "nearest", "sensor"],
                       help="Remapping algorithm to use")
    group.add_argument('--swath-usage', dest="swath_usage", default=0, type=float,
                       help="Fraction of swath that must be used to continue remapping/processing (default 0)")
    group.add_argument('--grid-coverage', dest="grid_coverage", default=0.1, type=float,
                       help="Fraction of grid that must be covered with valid data to continue processing (default 0.1)")
    group.add_argument('--fornav-D', dest='fornav_D', default=SUPPRESS, type=float,
                       help="Specify the -D option for fornav")
    group.add_argument('--fornav-d', dest='fornav_d', default=SUPPRESS, type=float,
                       help="Specify the -d option for fornav")
    group.add_argument('--maximum-weight-mode', dest="maximum_weight_mode", default=SUPPRESS, action="store_true",
                       help="Use maximum weight mode in fornav (-m)")
    group.add_argument("--distance-upper-bound", dest="distance_upper_bound", type=float, default=None,
                       help="Nearest neighbor search distance upper bound in units of grid cell")
    group.add_argument("--no-share-mask", dest="share_remap_mask", action="store_false",
                       help="Don't share invalid masks between nearest neighbor resampling (slow)")
    group.add_argument("--no-share-grid", dest="share_dynamic_grids", action="store_false",
                       help="Calculate dynamic grid attributes for every grid (instead of sharing highest resolution)")
    return ["Remapping Initialization", "Remapping"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    from polar2grid.core.containers import SwathScene
    parser = create_basic_parser(description="Remap a SwathScene to the provided grids")
    subgroup_titles = add_remap_argument_groups(parser)
    parser.add_argument("--scene", required=True,
                        help="JSON SwathScene filename to be remapped")
    parser.add_argument('-o', dest="output_filename", default="gridded_scene_{grid_name}.json",
                        help="Output filename for JSON scene (default is to 'gridded_scene_{grid_name}.json')")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(subgroup_titles=subgroup_titles, global_keywords=global_keywords)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)
    LOG.debug("Starting script with arguments: %s", " ".join(sys.argv))

    if args.output_filename and args.output_filename != "-" and os.path.isfile(args.output_filename):
            LOG.error("JSON file '%s' already exists, will not overwrite." % (args.output_filename,))
            raise RuntimeError("JSON file '%s' already exists, will not overwrite." % (args.output_filename,))

    scene = SwathScene.load(args.scene)

    remapper = Remapper(**args.subgroup_args["Remapping Initialization"])
    remap_kwargs = args.subgroup_args["Remapping"]
    for grid_name in remap_kwargs.pop("forced_grids", ["wgs84_fit"]):
        gridded_scene = remapper.remap_scene(scene, grid_name, **remap_kwargs)
        if args.output_filename is None or args.output_filename == "-":
            print(gridded_scene.dumps(persist=True))
        else:
            fn = args.output_filename.format(grid_name=grid_name)
            LOG.info("Saving gridded scene to file: %s", fn)
            gridded_scene.save(fn)

if __name__ == "__main__":
    sys.exit(main())
