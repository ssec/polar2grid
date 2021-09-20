#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2021 Space Science and Engineering Center (SSEC),
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
"""Convert legacy grids.conf files to grids.yaml format."""

from __future__ import annotations

import logging
import os
import sys
import warnings

import yaml
from pyproj import CRS, Proj
from polar2grid.grids import GridManager
from polar2grid.grids.manager import read_grids_config

logger = logging.getLogger(__name__)


def _conf_to_yaml_dict(grids_filename: str) -> str:
    overall_yaml_dict = {}
    gm = GridManager(grids_filename)
    grids_information = read_grids_config(grids_filename, convert_coords=False)
    for grid_name, grid_info in grids_information.items():
        area_dict = {}
        area_dict["description"] = ""

        crs = CRS.from_proj4(grid_info["proj4_str"])
        proj_dict = _crs_to_proj_dict(crs)
        area_dict["projection"] = proj_dict

        _add_shape(grid_info, area_dict)
        dx, dy = _add_resolution(grid_info, area_dict)
        try:
            _add_origin(grid_info, area_dict, crs, dx, dy)
        except ValueError:
            continue

        overall_yaml_dict[grid_name] = area_dict
    return overall_yaml_dict


def _crs_to_proj_dict(crs: CRS) -> dict:
    warnings.filterwarnings("ignore", module="pyproj", category=UserWarning)
    if crs.to_epsg() is not None:
        proj_dict = {"EPSG": crs.to_epsg()}
    else:
        proj_dict = crs.to_dict()
    _remove_unnecessary_proj_params(proj_dict)
    return proj_dict


def _remove_unnecessary_proj_params(proj_dict: dict) -> None:
    for param_name, exp_value in [("x_0", 0), ("y_0", 0), ("k_0", 1)]:
        if proj_dict.get(param_name) == exp_value:
            del proj_dict[param_name]


def _add_shape(grid_info: dict, area_dict: dict) -> None:
    width = grid_info["grid_width"]
    height = grid_info["grid_height"]
    if width is not None and height is not None:
        area_dict["shape"] = {"height": height, "width": width}


def _add_resolution(grid_info: dict, area_dict: dict) -> tuple[float, float]:
    dx = abs(grid_info["pixel_size_x"])
    dy = abs(grid_info["pixel_size_y"])
    if dx is not None and dy is not None:
        area_dict["resolution"] = {"dy": dy, "dx": dx}
    return dx, dy


def _add_origin(grid_info: dict, area_dict: dict, crs: CRS, dx: float, dy: float) -> None:
    ox = grid_info["grid_origin_x"]
    oy = grid_info["grid_origin_y"]
    if ox is not None and dx is None:
        logger.error("Can't convert grid with origin but no pixel resolution: %s", grid_name)
        raise ValueError("Can't convert grid with origin but no pixel resolution")
    if ox is not None and oy is not None:
        convert_to_meters = not crs.is_geographic and grid_info["grid_origin_units"] == "degrees"
        ox_m, oy_m = Proj(crs)(ox, oy) if convert_to_meters else (ox, oy)
        # convert center-pixel coordinates to outer edge extent
        ox_m = ox_m - dx / 2.0
        oy_m = oy_m + dy / 2.0
        ox, oy = Proj(crs)(ox_m, oy_m, inverse=True) if convert_to_meters else (ox_m, oy_m)
        area_dict["upper_left_extent"] = {"x": ox, "y": oy, "units": grid_info["grid_origin_units"]}


def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
    """Dump the data to YAML in ordered fashion."""

    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items(), flow_style=False)

    OrderedDumper.add_representer(dict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)


def get_parser():
    from argparse import ArgumentParser

    prog = os.getenv("PROG_NAME", sys.argv[0])
    parser = ArgumentParser(
        description="Convert legacy grids.conf format to Pyresample YAML format.",
        usage="""
To write to a file:
    %(prog)s input_file.conf > output_file.yaml
""",
    )
    parser.add_argument("grids_filename", help="Input grids.conf-style file to convert to YAML.")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    yaml_dict = _conf_to_yaml_dict(args.grids_filename)
    yml_str = ordered_dump(yaml_dict, default_flow_style=None)
    print(yml_str)


if __name__ == "__main__":
    sys.exit(main())
