#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2021 Space Science and Engineering Center (SSEC),
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
"""Helper functions for resampling Satpy Scenes."""

from __future__ import annotations

import logging
import os
from typing import List, Optional, Union

import numpy as np
from pyproj import Proj
from pyresample import parse_area_file
from pyresample.geometry import AreaDefinition, DynamicAreaDefinition
from satpy import Scene
from satpy.resample import get_area_def

from polar2grid.filters.resample_coverage import ResampleCoverageFilter
from polar2grid.grids import GridManager

from .resample_decisions import ResamplerDecisionTree

logger = logging.getLogger(__name__)

# TypeAlias
AreaSpecifier = Union[AreaDefinition, str, None]
ListOfAreas = List[Union[AreaDefinition, str, None]]

GRIDS_YAML_FILEPATH = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "grids", "grids.yaml"))


def _crs_equal(a, b):
    """Compare two projection dictionaries for "close enough" equality."""
    # pyproj 2.0+
    if hasattr(a, "crs") and hasattr(b, "crs"):
        return a.crs == b.crs

    # fallback
    from osgeo import osr

    a = dict(sorted(a.proj_dict.items()))
    b = dict(sorted(b.proj_dict.items()))
    p1 = Proj(a)
    p2 = Proj(b)
    s1 = osr.SpatialReference()
    s1.ImportFromProj4(p1.srs)
    s2 = osr.SpatialReference()
    s2.ImportFromProj4(p2.srs)
    return s1.IsSame(s2)


def _is_native_grid(grid, max_native_area):
    """Check if the current grid is in the native data projection."""
    if not isinstance(max_native_area, AreaDefinition):
        return False
    if not isinstance(grid, AreaDefinition):
        return False
    if not _crs_equal(max_native_area, grid):
        return False
    # if not np.allclose(np.array(max_native_area.area_extent), np.array(grid.area_extent), atol=grid.pixel_size_x):
    if not np.allclose(np.array(max_native_area.area_extent), np.array(grid.area_extent)):
        return False
    if max_native_area.width < grid.width:
        return (grid.width / max_native_area.width).is_integer()
    else:
        return (max_native_area.width / grid.width).is_integer()


def _get_preserve_resolution(preserve_resolution, resampler, areas_to_resample):
    """Determine if we should preserve native resolution products.

    Preserving native resolution should only happen if:

    1. The 'native' resampler is used
    2. At least one of the areas provided to resampling are 'MIN' or 'MAX'
    3. The user didn't ask to *not* preserve it.

    """
    # save original native resolution if possible
    any_minmax = any(x in ["MIN", "MAX"] for x in areas_to_resample)
    is_native = resampler == "native"
    is_default = resampler is None
    return any_minmax and (is_native or is_default) and preserve_resolution


def _get_legacy_and_yaml_areas(grid_configs: list[str, ...]) -> tuple[GridManager, dict[str, AreaDefinition]]:
    if "grids.conf" in grid_configs:
        logger.debug("Replacing 'grids.conf' with builtin YAML grid configuration file.")
        grid_configs[grid_configs.index("grids.conf")] = GRIDS_YAML_FILEPATH
    if not grid_configs:
        grid_configs = [GRIDS_YAML_FILEPATH]
    p2g_grid_configs = [x for x in grid_configs if x.endswith(".conf")]
    pyresample_area_configs = [x for x in grid_configs if not x.endswith(".conf")]
    if p2g_grid_configs:
        grid_manager = GridManager(*p2g_grid_configs)
    else:
        grid_manager = {}

    if pyresample_area_configs:
        yaml_areas = parse_area_file(pyresample_area_configs)
        yaml_areas = {x.area_id: x for x in yaml_areas}
    else:
        yaml_areas = {}

    return grid_manager, yaml_areas


def _get_area_def_from_name(area_name, input_scene, grid_manager, yaml_areas):
    if area_name is None:
        # no resampling
        area_def = None
    elif area_name == "MAX":
        area_def = input_scene.finest_area()
    elif area_name == "MIN":
        area_def = input_scene.coarsest_area()
    elif area_name in yaml_areas:
        area_def = yaml_areas[area_name]
    elif area_name in grid_manager:
        p2g_def = grid_manager[area_name]
        area_def = p2g_def.to_satpy_area()
    else:
        # get satpy builtin area
        area_def = get_area_def(area_name)

    if isinstance(area_def, DynamicAreaDefinition):
        logger.info("Computing dynamic grid parameters...")
        area_def = area_def.freeze(input_scene.max_area())
        logger.debug("Frozen dynamic area: %s", area_def)
    return area_def


def _get_default_resampler(resampler, area_name, area_def, input_scene):
    if resampler is None and area_def is not None:
        rs = "native" if area_name in ["MIN", "MAX"] or _is_native_grid(area_def, input_scene.max_area()) else "nearest"
        logger.debug("Setting default resampling to '{}' for grid '{}'".format(rs, area_name))
    else:
        rs = resampler
    return rs


class AreaDefResolver:
    def __init__(self, input_scene, grid_configs):
        grid_manager, yaml_areas = _get_legacy_and_yaml_areas(grid_configs)
        self.input_scene = input_scene
        self.grid_manager = grid_manager
        self.yaml_areas = yaml_areas

    def __getitem__(self, area_name):
        return _get_area_def_from_name(area_name, self.input_scene, self.grid_manager, self.yaml_areas)


def _default_grid(resampler, is_polar2grid):
    if resampler in ["native"]:
        default_target = "MAX"
    else:
        default_target = "wgs84_fit" if is_polar2grid else "MAX"
    return default_target


def _hashable_kwargs(kwargs):
    return tuple(sorted(kwargs.items()))


def _redict_hashable_kwargs(kwargs_tuple):
    return dict(kwargs_tuple)


def _create_resampling_groups(input_scene, resampling_dtree, is_polar2grid):
    resampling_groups = {}
    for data_id in input_scene.keys():
        resampling_args = resampling_dtree.find_match(**input_scene[data_id].attrs)
        resampler = resampling_args["resampler"]
        resampler_kwargs = resampling_args.get("kwargs", {})
        default_target = resampling_args.get("default_target", None)
        if default_target is None:
            default_target = _default_grid(resampler, is_polar2grid)
        hashable_kwargs = _hashable_kwargs(resampler_kwargs)
        resampling_groups.setdefault((resampler, hashable_kwargs, default_target), []).append(data_id)
    return resampling_groups


def resample_scene(
    input_scene: Scene,
    areas_to_resample: ListOfAreas,
    grid_configs: list[str, ...],
    resampler: Optional[str],
    preserve_resolution: bool = True,
    grid_coverage: Optional[float] = None,
    is_polar2grid: bool = True,
    **resample_kwargs,
) -> list[tuple[Scene, set]]:
    """Resample a single Scene to multiple target areas."""
    area_resolver = AreaDefResolver(input_scene, grid_configs)
    resampling_dtree = ResamplerDecisionTree.from_configs()
    if resampler is None:
        resampling_groups = _create_resampling_groups(input_scene, resampling_dtree, is_polar2grid)
    else:
        default_target = _default_grid(resampler, is_polar2grid)
        rs_kwargs = _hashable_kwargs(resample_kwargs)
        resampling_groups = {(resampler, rs_kwargs, default_target): None}

    wishlist: set = input_scene.wishlist.copy()
    scenes_to_save = []
    for (resampler, _resample_kwargs, default_target), data_ids in resampling_groups.items():
        areas = _areas_to_resample(areas_to_resample, resampler, default_target)
        scene_to_resample: Scene = input_scene.copy(datasets=data_ids)
        preserve_resolution = _get_preserve_resolution(preserve_resolution, resampler, areas)
        preserved_products = _products_to_preserve_resolution(preserve_resolution, wishlist, scene_to_resample)
        if preserved_products:
            scenes_to_save.append((scene_to_resample, preserved_products))

        logger.debug("Products to preserve resolution for: {}".format(preserved_products))
        logger.debug("Products to use new resolution for: {}".format(set(wishlist) - preserved_products))
        # convert hashable tuple to dict
        _resample_kwargs = _redict_hashable_kwargs(_resample_kwargs)
        _grid_cov = _resample_kwargs.get("grid_coverage", grid_coverage)
        if _grid_cov is None:
            _grid_cov = 0.1
        for area_name in areas:
            area_def = area_resolver[area_name]
            rs = _get_default_resampler(resampler, area_name, area_def, input_scene)
            if area_def is not None:
                this_area_scene: Scene = scene_to_resample
                if resampler != "native" and _grid_cov > 0:
                    logger.info("Checking products for sufficient output grid coverage (grid: '%s')...", area_name)
                    filter = ResampleCoverageFilter(target_area=area_def, coverage_fraction=_grid_cov)
                    this_area_scene = filter.filter_scene(scene_to_resample)
                    if this_area_scene is None:
                        logger.warning("No products were found to overlap with '%s' grid.", area_name)
                        continue
                    if data_ids is not None:
                        data_ids = list(set(data_ids) & set(this_area_scene.keys()))
                logger.info("Resampling to '%s' using '%s' resampling...", area_name, rs)
                logger.debug("Resampling to '%s' using resampler '%s' with %s", area_name, rs, _resample_kwargs)
                new_scn = this_area_scene.resample(area_def, resampler=rs, datasets=data_ids, **_resample_kwargs)
            elif not preserve_resolution:
                # the user didn't want to resample to any areas
                # the user also requested that we don't preserve resolution
                # which means we have to save this Scene's datasets
                # because they won't be saved
                new_scn = scene_to_resample
            else:
                # No resampling and any preserved resolution datasets were saved earlier
                continue
            # we only want to try to save products that we asked for and that
            # we were actually able to generate. Composite generation may have
            # modified the original DataID so we can't use
            # 'resampled_products'.
            _resampled_products = (new_scn.wishlist & set(new_scn.keys())) - preserved_products
            if _resampled_products:
                scenes_to_save.append((new_scn, _resampled_products))

    # import ipdb; ipdb.set_trace()
    return scenes_to_save


def _areas_to_resample(
    areas_to_resample: Optional[ListOfAreas], resampler: Optional[str], default_target: Optional[AreaSpecifier]
) -> ListOfAreas:
    areas = areas_to_resample
    if areas is None:
        if resampler in ["native"]:
            logging.debug("Using default resampling target area 'MAX'.")
            areas = ["MAX"]
        elif default_target is None:
            raise ValueError("No destination grid/area specified and no default available (use -g flag).")
        else:
            logging.debug("Using default resampling target area '%s'.", default_target)
            areas = [default_target]
    elif not areas:
        areas = [None]

    return areas


def _products_to_preserve_resolution(preserve_resolution, wishlist, scene_to_resample):
    if preserve_resolution:
        return set(wishlist) & set(scene_to_resample.keys())
    return set()
