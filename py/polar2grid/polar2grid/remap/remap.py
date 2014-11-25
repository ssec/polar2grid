#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
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
"""Interface to remapping polar2grid data.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Oct 2014
:license:      GNU GPLv3

"""
from polar2grid.remap import ms2gt

__docformat__ = "restructuredtext en"

from polar2grid.core.meta import GriddedProduct, GriddedScene, SwathScene
from polar2grid.remap import ll2cr as gator  # gridinator
from polar2grid.grids.grids import Cartographer

import os
import sys
import logging
import signal
from collections import defaultdict
import multiprocessing
from itertools import izip

import numpy
from scipy.interpolate.interpnd import LinearNDInterpolator, NDInterpolatorBase, CloughTocher2DInterpolator, _ndim_coords_from_arrays
from scipy.spatial import cKDTree

LOG = logging.getLogger(__name__)


def init_worker():
    """Used in multiprocessing to initialize pool workers.

    If this isn't done then the listening process will hang forever and
    will have to be killed with the "kill" command even after the outer-most
    process is Ctrl+C'd out of existence.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def run_fornav_c(*args, **kwargs):
    proc_pool = kwargs.pop("pool", None)
    if proc_pool is None:
        result = ms2gt.fornav(*args, **kwargs)
    else:
        result = proc_pool.apply_async(ms2gt.fornav, args=args, kwds=kwargs)
    return result


class NearestNDInterpolator(NDInterpolatorBase):
    def __init__(self, x, y):
        x = _ndim_coords_from_arrays(x)
        self._check_init_shape(x, y)
        self.tree = cKDTree(x)
        self.points = x
        self.values = y

    def __call__(self, *args, **kwargs):
        """
        Evaluate interpolator at given points.

        Parameters
        ----------
        xi : ndarray of float, shape (..., ndim)
            Points where to interpolate data at.

        """
        # DJH: Added kwargs and passed them to self.tree.query
        fill_value = kwargs.pop("fill_value", numpy.nan)
        xi = _ndim_coords_from_arrays(args)
        xi = self._check_call_shape(xi)
        dist, i = self.tree.query(xi, **kwargs)
        values = numpy.append(self.values, self.values.dtype.type(fill_value))
        return values[i]


def griddata(points, values, xi, method='linear', fill_value=numpy.nan, distance_upper_bound=3.0):
    # DJH: Added distance_upper_bound keyword
    # FIXME: The distance_upper_bound keyword should default to what the KDTree defaults to (inf) and this functionality should probably be put in scipy itself
    points = _ndim_coords_from_arrays(points)

    if points.ndim < 2:
        ndim = points.ndim
    else:
        ndim = points.shape[-1]

    if ndim == 1 and method in ('nearest', 'linear', 'cubic'):
        from scipy.interpolate import interp1d
        points = points.ravel()
        if isinstance(xi, tuple):
            if len(xi) != 1:
                raise ValueError("invalid number of dimensions in xi")
            xi, = xi
        # Sort points/values together, necessary as input for interp1d
        idx = numpy.argsort(points)
        points = points[idx]
        values = values[idx]
        ip = interp1d(points, values, kind=method, axis=0, bounds_error=False,
                      fill_value=fill_value)
        return ip(xi)
    elif method == 'nearest':
        ip = NearestNDInterpolator(points, values)
        return ip(xi, distance_upper_bound=distance_upper_bound, fill_value=fill_value)
    elif method == 'linear':
        ip = LinearNDInterpolator(points, values, fill_value=fill_value)
        return ip(xi)
    elif method == 'cubic' and ndim == 2:
        ip = CloughTocher2DInterpolator(points, values, fill_value=fill_value)
        return ip(xi)
    else:
        raise ValueError("Unknown interpolation method %r for "
                         "%d dimensional data" % (method, ndim))


class Remapper(object):
    def __init__(self, grid_configs=[],
                 overwrite_existing=False, keep_intermediate=False, exit_on_error=True, **kwargs):
        self.cart = Cartographer(*grid_configs)
        self.overwrite_existing = overwrite_existing
        self.keep_intermediate = keep_intermediate
        self.exit_on_error = exit_on_error
        self.methods = {
            "ewa": self._remap_scene_ewa,
            "nearest": self._remap_scene_nearest,
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

        grid_def = self.cart.get_grid_definition(grid_name)
        func = self.methods[method]

        # FUTURE: Make this a keyword and add the logic to support it
        if kwargs.get("share_dynamic_grids", True):
            # Let's run ll2cr to fill in any parameters we need to and decide if the data fits in the grid
            best_swath_def = self.highest_resolution_swath_definition(swath_scene)
            LOG.debug("Running ll2cr on the highest resolution swath to determine if it fits")
            try:
                self.ll2cr(best_swath_def, grid_def)
            except StandardError:
                LOG.error("Remapping error")
                raise

        return func(swath_scene, grid_def, **kwargs)

    def ll2cr(self, swath_definition, grid_definition):
        geo_id = swath_definition["swath_name"]
        grid_name = grid_definition["grid_name"]
        if (geo_id, grid_name) in self.ll2cr_cache:
            return self.ll2cr_cache[(geo_id, grid_name)]
        LOG.debug("Swath '%s' -> Grid '%s'", geo_id, grid_name)

        rows_fn = "ll2cr_rows_%s_%s.dat" % (grid_name, geo_id)
        cols_fn = "ll2cr_cols_%s_%s.dat" % (grid_name, geo_id)
        lon_arr = swath_definition.get_longitude_array()
        lat_arr = swath_definition.get_latitude_array()

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
            rows_arr = numpy.memmap(rows_fn, dtype=lat_arr.dtype, mode="w+", shape=lat_arr.shape)
            cols_arr = numpy.memmap(cols_fn, dtype=lat_arr.dtype, mode="w+", shape=lat_arr.shape)
            points_in_grid, _, _ = gator.ll2cr(lon_arr, lat_arr, grid_definition,
                                               fill_in=swath_definition["fill_value"],
                                               cols_out=cols_arr, rows_out=rows_arr)
        except StandardError:
            LOG.error("Unexpected error encountered during ll2cr gridding for %s -> %s", geo_id, grid_name)
            LOG.debug("ll2cr error exception: ", exc_info=True)
            self._safe_remove(rows_fn, cols_fn)
            raise

        # if 5% of the grid will have data in it then it fits
        fraction_in = points_in_grid / float(grid_definition["width"] * grid_definition["height"])
        fits_grid = fraction_in >= 0.05
        if not fits_grid:
            self._safe_remove(rows_fn, cols_fn)
            LOG.error("Data does not fit in grid %s because it only covered %f%%" % (grid_name, fraction_in * 100))
            raise RuntimeError("Data does not fit in grid %s" % (grid_name,))
        else:
            LOG.debug("Data fits in grid %s and covers %f%% of the grid", grid_name, fraction_in * 100)

        self.ll2cr_cache[(geo_id, grid_name)] = (cols_fn, rows_fn)
        return cols_fn, rows_fn

    def _add_prefix(self, prefix, *filepaths):
        return [os.path.join(os.path.dirname(x), prefix + os.path.basename(x)) for x in filepaths]

    def _safe_remove(self, *filepaths):
        if not self.keep_intermediate:
            for fp in filepaths:
                if os.path.isfile(fp):
                    try:
                        LOG.info("Removing intermediate file '%s'...", fp)
                        os.remove(fp)
                    except OSError:
                        LOG.warning("Could not remove intermediate files that aren't needed anymore.")
                        LOG.debug("Intermediate output file remove exception:", exc_info=True)

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

        for geo_id, product_names in product_groups.items():
            # TODO: Move into it's own function if this gets complicated
            # TODO: Add some multiprocessing
            try:
                LOG.info("Running ll2cr on the geolocation data for the following products:\n\t%s", "\n\t".join(product_names))
                swath_def = swath_scene[product_names[0]]["swath_definition"]
                if not share_dynamic_grids:
                    cols_fn, rows_fn = self.ll2cr(swath_def, grid_def.copy())
                else:
                    cols_fn, rows_fn = self.ll2cr(swath_def, grid_def)
            except StandardError:
                LOG.error("Remapping error")
                if self.exit_on_error:
                    raise
                continue

            # Run fornav for all of the products at once
            LOG.info("Running fornav for the following products:\n\t%s", "\n\t".join(product_names))
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
            edge_res = swath_def.get("limb_resolution", None)
            fornav_D = kwargs.get("fornav_D", None)
            if fornav_D is None:
                if edge_res is not None:
                    if grid_def.is_latlong:
                        fornav_D = (edge_res / 2) / grid_def.cell_width_meters
                    else:
                        fornav_D = (edge_res / 2) / grid_def["cell_width"]
                    LOG.debug("Fornav 'D' option dynamically set to %f", fornav_D)

            try:
                run_fornav_c(
                    len(product_filepaths),
                    swath_def["swath_columns"],
                    swath_def["swath_rows"]/rows_per_scan,
                    rows_per_scan,
                    cols_fn,
                    rows_fn,
                    product_filepaths,
                    grid_def["width"],
                    grid_def["height"],
                    fornav_filepaths,
                    swath_data_type_1="f4",
                    swath_fill_1=swath_scene.get_fill_value(product_names),
                    grid_fill_1=numpy.nan,
                    weight_delta_max=fornav_D,
                    weight_distance_max=kwargs.get("fornav_d", None),
                    maximum_weight_mode=kwargs.get("maximum_weight_mode", None),
                    # We only specify start_scan for the 'image'/channel
                    # data because ll2cr is not 'forced' so it only writes
                    # useful data to the output cols/rows files
                    start_scan=(0, 0),
                )
            except StandardError:
                LOG.error("Remapping error")
                self._safe_remove(rows_fn, cols_fn, *fornav_filepaths)
                if self.exit_on_error:
                    raise
                continue

            # Give the gridded product ownership of the remapped data
            for product_name, fornav_fp in zip(product_names, fornav_filepaths):
                swath_product = swath_scene[product_name]
                gridded_product = GriddedProduct()
                gridded_product.from_swath_product(swath_product)
                gridded_product["grid_definition"] = grid_def
                gridded_product["fill_value"] = numpy.nan
                gridded_product["grid_data"] = fornav_fp
                gridded_scene[product_name] = gridded_product

            # Remove ll2cr files now that we are done with them
            self._safe_remove(rows_fn, cols_fn)

        return gridded_scene

    def _remap_scene_nearest(self, swath_scene, grid_def, share_dynamic_grids=True, **kwargs):
        # TODO: Make methods more flexible than just a function call
        gridded_scene = GriddedScene()
        grid_name = grid_def["grid_name"]

        # Group products together that shared the same geolocation
        product_groups = defaultdict(list)
        for product_name, swath_product in swath_scene.items():
            swath_def = swath_product["swath_definition"]
            geo_id = swath_def["swath_name"]
            product_groups[geo_id].append(product_name)

        for geo_id, product_names in product_groups.items():
            pp_names = "\n\t".join(product_names)
            LOG.info("Running ll2cr on the geolocation data for the following products:\n\t%s", pp_names)
            LOG.debug("Swath name: %s", geo_id)

            # TODO: Move into it's own function if this gets complicated
            # TODO: Add some multiprocessing
            try:
                swath_def = swath_scene[product_names[0]]["swath_definition"]
                if not share_dynamic_grids:
                    cols_fn, rows_fn = self.ll2cr(swath_def, grid_def.copy())
                else:
                    cols_fn, rows_fn = self.ll2cr(swath_def, grid_def)
            except StandardError:
                LOG.error("Remapping error")
                if self.exit_on_error:
                    raise
                continue

            LOG.info("Running nearest neighbor for the following products:\n\t%s", "\n\t".join(product_names))
            grid_x, grid_y = numpy.mgrid[:grid_def["height"], :grid_def["width"]]
            # we need flattened versions of these
            shape = (swath_def["swath_rows"] * swath_def["swath_columns"],)
            cols_array = numpy.memmap(cols_fn, shape=shape, dtype=swath_def["data_type"])
            rows_array = numpy.memmap(rows_fn, shape=shape, dtype=swath_def["data_type"])
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

            product_filepaths = swath_scene.get_data_filepaths(product_names)
            output_filepaths = self._add_prefix("grid_%s_" % (grid_name,), *product_filepaths)

            # Prepare the products
            for product_name, output_fn in izip(product_names, output_filepaths):
                LOG.debug("Running nearest neighbor on '%s'", product_name)
                if os.path.isfile(output_fn):
                    if not self.overwrite_existing:
                        LOG.error("Intermediate remapping file already exists: %s" % (output_fn,))
                        raise RuntimeError("Intermediate remapping file already exists: %s" % (output_fn,))
                    else:
                        LOG.warning("Intermediate remapping file already exists, will overwrite: %s", output_fn)

                try:
                    # XXX: May have to do something smarter if there are float products and integer products together
                    image_array = swath_scene[product_name].get_data_array()
                    output_array = griddata((cols_array, rows_array), image_array.flatten(), (grid_y, grid_x),
                                            method='nearest', fill_value=numpy.nan,
                                            distance_upper_bound=kwargs["distance_upper_bound"])
                    output_array.tofile(output_fn)

                    # Give the gridded product ownership of the remapped data
                    swath_product = swath_scene[product_name]
                    gridded_product = GriddedProduct()
                    gridded_product.from_swath_product(swath_product)
                    gridded_product["grid_definition"] = grid_def
                    gridded_product["fill_value"] = numpy.nan
                    gridded_product["grid_data"] = output_fn
                    gridded_scene[product_name] = gridded_product

                    # hopefully force garbage collection
                    del output_array
                except StandardError:
                    LOG.error("Remapping error")
                    self._safe_remove(rows_fn, cols_fn, output_fn)
                    if not self.keep_intermediate and os.path.isfile(output_fn):
                        os.remove(output_fn)
                    if self.exit_on_error:
                        raise
                    continue

                LOG.debug("Done running nearest neighbor on '%s'", product_name)

            # Remove ll2cr files now that we are done with them
            self._safe_remove(rows_fn, cols_fn)

        return gridded_scene

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
    group.add_argument("--method", dest="remap_method", default="ewa", choices=["ewa", "nearest"],
                       help="Remapping algorithm to use")
    group.add_argument('--fornav-D', dest='fornav_D', default=SUPPRESS, type=float,
                       help="Specify the -D option for fornav")
    group.add_argument('--fornav-d', dest='fornav_d', default=SUPPRESS, type=float,
                       help="Specify the -d option for fornav")
    group.add_argument('--maximum-weight-mode', dest="maximum_weight_mode", default=SUPPRESS, action="store_true",
                       help="Use maximum weight mode in fornav (-m)")
    group.add_argument("--distance-upper-bound", dest="distance_upper_bound",)
    group.add_argument("--no-share-grid", dest="share_dynamic_grid", action="store_false",
                       help="Calculate dynamic grid attributes for every grid (instead of sharing highest resolution)")
    return ["Remapping Initialization", "Remapping"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    from polar2grid.core.meta import SwathScene
    parser = create_basic_parser(description="Remap a SwathScene to the provided grids")
    subgroup_titles = add_remap_argument_groups(parser)
    parser.add_argument("--scene", required=True,
                        help="JSON SwathScene filename to be remapped")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(subgroup_titles=subgroup_titles, global_keywords=global_keywords)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)
    LOG.debug("Starting script with arguments: %s", " ".join(sys.argv))

    scene = SwathScene.load(args.scene)

    remapper = Remapper(**args.subgroup_args["Remapping Initialization"])
    remap_kwargs = args.subgroup_args["Remapping"]
    for grid_name in remap_kwargs.pop("forced_grids"):
        gridded_scene = remapper.remap_scene(scene, grid_name, **remap_kwargs)
        # FIXME: Either allow only 1 grid or find a nice way to output multiple gridded scenes as JSON to stdout
        fn = "gridded_scene_%s.json" % (grid_name,)
        gridded_scene.save(fn)

if __name__ == "__main__":
    sys.exit(main())
