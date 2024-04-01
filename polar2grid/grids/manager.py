#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2013-2015 Space Science and Engineering Center (SSEC),
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
# Written by David Hoese    March 2015
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Utilities and accessor functions to grids and projections used in polar2grid."""

from __future__ import annotations

import logging
import os

from pyproj import CRS, Proj

from polar2grid.core.containers import GridDefinition

LOG = logging.getLogger(__name__)


def _parse_meter_degree_param(param) -> tuple[float, bool]:
    """Parse a configuration parameter that could be meters or degrees.

    Degrees are denoted with a suffix of 'deg'. Meters are denoted with a suffix of either 'm' or no suffix at all.

    :returns: (float param, True if degrees/False if meters)
    """
    is_deg = False
    if param.endswith("deg"):
        # Parameter is in degrees
        is_deg = True
        param = param[:-3]
    elif param.endswith("m"):
        # Parameter is in meters
        param = param[:-1]
    return float(param), is_deg


def get_proj4_info(proj4_str):
    parts = [x.replace("+", "") for x in proj4_str.split(" ")]
    if "no_defs" in parts:
        parts.remove("no_defs")

    proj4_dict = dict(p.split("=") if "=" in p else (p, True) for p in parts)
    _convert_numeric_parameters_to_floats(proj4_dict)
    return proj4_dict


def _convert_numeric_parameters_to_floats(proj4_dict):
    for k in ["lat_0", "lat_1", "lat_2", "lat_ts", "lat_b", "lat_t", "lon_0", "lon_1", "lon_2", "lonc", "a", "b", "es"]:
        if k in proj4_dict:
            proj4_dict[k] = float(proj4_dict[k])


def _parse_proj4_str(proj4_str, grid_name):
    # Test to make sure the proj4_str is valid in pyproj's eyes
    try:
        crs = CRS.from_proj4(proj4_str)
    except ValueError:
        LOG.error("Invalid proj4 string in '%s' : '%s'" % (grid_name, proj4_str))
        raise
    return proj4_str, crs


def parse_proj4_config_line(grid_name, parts):
    proj4_str, crs = _parse_proj4_str(parts[2], grid_name)
    parts = [None if part in ("None", "") else part for part in parts]
    is_static = any(part is None for part in parts[3:9])

    try:
        grid_width, grid_height = _parse_grid_width_and_height(grid_name, parts[3], parts[4])
        pixel_size_x, pixel_size_y = _parse_pixel_size_x_y(grid_name, parts[5], parts[6])
        grid_origin_x, grid_origin_y, grid_units = _parse_origin_x_y(grid_name, parts[7], parts[8], crs)
    except ValueError:
        LOG.error("Could not parse proj4 grid configuration: '%s'" % (grid_name,))
        raise

    if grid_width is None and pixel_size_x is None:
        LOG.error("Either grid size or pixel size must be specified for '%s'" % grid_name)
        raise ValueError("Either grid size or pixel size must be specified for '%s'" % grid_name)

    info = {}
    info["grid_kind"] = "proj4"
    info["static"] = is_static
    info["proj4_str"] = proj4_str
    info["pixel_size_x"] = pixel_size_x
    info["pixel_size_y"] = pixel_size_y
    info["grid_origin_x"] = grid_origin_x
    info["grid_origin_y"] = grid_origin_y
    info["grid_width"] = grid_width
    info["grid_height"] = grid_height
    info["grid_origin_units"] = grid_units
    return info


def _parse_grid_width_and_height(grid_name, width_part, height_part):
    grid_width = _parse_optional_config_param(width_part, int)
    grid_height = _parse_optional_config_param(height_part, int)
    if _only_one_specified(grid_width, grid_height):
        LOG.error("Both or neither grid sizes must be specified for '%s'" % grid_name)
        raise ValueError("Both or neither grid sizes must be specified for '%s'" % grid_name)
    return grid_width, grid_height


def _parse_pixel_size_x_y(grid_name, x_part, y_part):
    pixel_size_x = _parse_optional_config_param(x_part, float, (grid_name, "pixel_size"))
    pixel_size_y = _parse_optional_config_param(y_part, float, (grid_name, "pixel size"))
    if _only_one_specified(pixel_size_y, pixel_size_y):
        LOG.error("Both or neither pixel sizes must be specified for '%s'" % grid_name)
        raise ValueError("Both or neither pixel sizes must be specified for '%s'" % grid_name)
    return pixel_size_x, pixel_size_y


def _parse_origin_x_y(grid_name, x_part, y_part, crs):
    xorigin_res = _parse_optional_config_param(x_part, _parse_meter_degree_param)
    grid_origin_x, xorigin_is_deg = xorigin_res if xorigin_res is not None else (None, False)
    yorigin_res = _parse_optional_config_param(y_part, _parse_meter_degree_param)
    grid_origin_y, yorigin_is_deg = yorigin_res if yorigin_res is not None else (None, False)
    if _only_one_specified(grid_origin_x, grid_origin_x):
        LOG.error("Both or neither grid origins must be specified for '%s'" % grid_name)
        raise ValueError("Both or neither grid origins must be specified for '%s'" % grid_name)
    if xorigin_is_deg != yorigin_is_deg:
        LOG.error("Grid origin parameters must be in the same units (meters vs degrees)")
        raise ValueError("Grid origin parameters must be in the same units (meters vs degrees)")
    grid_units = "degrees" if xorigin_is_deg or crs.is_geographic else "meters"
    return grid_origin_x, grid_origin_y, grid_units


def _only_one_specified(a, b):
    only_a_specified = a is not None and b is None
    only_b_specified = a is None and b is not None
    return only_a_specified or only_b_specified


def _parse_optional_config_param(str_part, convert_func, unspecified_info=None):
    if str_part is not None:
        return convert_func(str_part)
    if unspecified_info is not None:
        grid_name, param_name = unspecified_info
        LOG.warning(f"Grid {grid_name!r} may not process properly due to unspecified {param_name}")
    return None


def parse_and_convert_proj4_config_line(grid_name, parts):
    """Return a dictionary of information for a specific PROJ.4 grid from a grid configuration line.

    ``parts`` should be every comma-separated part of the line including the ``grid_name``.
    """
    info = parse_proj4_config_line(grid_name, parts)
    _convert_origin_degrees_to_meters_if_needed(grid_name, info)
    proj4_dict = get_proj4_info(info["proj4_str"])
    info.update(**proj4_dict)
    return info


def _convert_origin_degrees_to_meters_if_needed(grid_name, info):
    p = Proj(info["proj4_str"])
    if info["grid_origin_units"] == "degrees" and not p.crs.is_geographic:
        meters_x, meters_y = p(info["grid_origin_x"], info["grid_origin_y"])
        LOG.debug(
            "Converted grid '%s' origin from (lon: %f, lat: %f) to (x: %f, y: %f)",
            grid_name,
            info["grid_origin_x"],
            info["grid_origin_y"],
            meters_x,
            meters_y,
        )
        info["grid_origin_x"] = meters_x
        info["grid_origin_y"] = meters_y
    elif info["grid_origin_units"] != "degrees" and info["grid_origin_x"] is not None and p.crs.is_geographic:
        LOG.error("Lat/Lon grid '%s' must have its origin in degrees", grid_name)
        raise ValueError("Lat/Lon grid '%s' must have its origin in degrees" % (grid_name,))


def read_grids_config_str(config_str, convert_coords=True):
    grid_information = {}
    this_configs_grids = []

    for parts in _generate_valid_parts_in_config_str(config_str):
        grid_name = parts[0]
        # Help the user out by checking if they are adding a grid more than once
        if grid_name not in this_configs_grids:
            this_configs_grids.append(grid_name)
        else:
            LOG.warning("Grid '%s' is in grid config more than once" % (grid_name,))

        grid_type = parts[1].lower()
        if grid_type != "proj4":
            LOG.error("Unknown grid type '%s' for grid '%s' in grid config" % (grid_type, grid_name))
            raise ValueError("Unknown grid type '%s' for grid '%s' in grid config" % (grid_type, grid_name))
        if convert_coords:
            grid_information[grid_name] = parse_and_convert_proj4_config_line(grid_name, parts)
        else:
            grid_information[grid_name] = parse_proj4_config_line(grid_name, parts)

    return grid_information


def _generate_valid_parts_in_config_str(config_str: str):
    for line in config_str.split("\n"):
        # Skip comments and empty lines
        if not line or line.startswith("#") or line.startswith("\n"):
            continue

        # Clean up the configuration line
        line = line.strip("\n,")
        parts = [part.strip() for part in line.split(",")]

        if len(parts) != 11 and len(parts) != 9:
            LOG.error("Grid configuration line '%s' in grid config does not have the correct format" % (line,))
            raise ValueError("Grid configuration line '%s' in grid config does not have the correct format" % (line,))
        yield parts


def read_grids_config(config_filepath, convert_coords=True):
    """Read the "grids.conf" file and create dictionaries mapping the grid name to the necessary information.

    There are two dictionaries created, one for gpd file grids and one for proj4 grids.

    Format for proj4 grids:
    grid_name,proj4,proj4_str,pixel_size_x,pixel_size_y,origin_x,origin_y,width,height

    where 'proj4' is the actual text 'proj4' to define the grid as a proj4 grid.

    """
    full_config_filepath = os.path.realpath(os.path.expanduser(config_filepath))
    with open(full_config_filepath, "r") as config_file:
        config_str = config_file.read()
        return read_grids_config_str(config_str, convert_coords=convert_coords)


class GridManager:
    """Object that holds grid information about the grids added to it."""

    grid_information: dict[str, dict] = {}

    def __init__(self, *grid_configs):
        for grid_config in grid_configs:
            LOG.debug("Loading grid configuration '%s'" % (grid_config,))
            self.add_grid_config(grid_config)

    def __contains__(self, item):
        return item in self.grid_information

    def __getitem__(self, item):
        return self.get_grid_definition(item)

    def add_grid_config(self, grid_config_filename):
        """Load a grid configuration file.

        If a ``grid_name`` was already added its information is overwritten.
        """
        grid_information = read_grids_config(grid_config_filename)
        self.grid_information.update(**grid_information)

    def add_grid_config_str(self, grid_config_line):
        grid_information = read_grids_config_str(grid_config_line)
        self.grid_information.update(**grid_information)

    def add_proj4_grid_info(self, grid_name, proj4_str, width, height, cell_width, cell_height, origin_x, origin_y):
        # Trick the parse function to think this came from a config line
        parts = (grid_name, "proj4", proj4_str, width, height, cell_width, cell_height, origin_x, origin_y)
        self.grid_information[grid_name] = parse_and_convert_proj4_config_line(grid_name, parts)

    def get_grid_definition(self, grid_name: str) -> GridDefinition:
        """Return a standard `GridDefinition` object for the specified grid.

        :returns: `GridDefinition` object, updates to this object do not affect information
                  internal to the `Cartographer`.

        """
        grid_info = self.get_grid_info(grid_name)
        return GridDefinition(
            grid_name=grid_name,
            proj4_definition=grid_info["proj4_str"],
            height=grid_info["grid_height"],
            width=grid_info["grid_width"],
            cell_width=grid_info["pixel_size_x"],
            cell_height=grid_info["pixel_size_y"],
            origin_x=grid_info["grid_origin_x"],
            origin_y=grid_info["grid_origin_y"],
        )

    def get_grid_info(self, grid_name):
        """Return a grid information dictionary about the ``grid_name`` specified.

        The information returned will always be a copy of the information
        stored internally in this object. So a change to the dictionary
        returned does NOT affect the internal information.

        :raises ValueError: if ``grid_name`` does not exist

        """
        if grid_name in self.grid_information:
            return self.grid_information[grid_name].copy()
        else:
            LOG.error("Unknown grid '%s'" % (grid_name,))
            raise ValueError("Unknown grid '%s'" % (grid_name,))
