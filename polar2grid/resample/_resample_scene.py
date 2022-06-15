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

from ..filters._utils import PRGeometry
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


def _get_area_def_from_name(
    area_name: Optional[str], input_scene: Scene, grid_manager: GridManager, yaml_areas: list
) -> Optional[PRGeometry]:
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
    return area_def


class AreaDefResolver:
    def __init__(self, input_scene, grid_configs):
        grid_manager, yaml_areas = _get_legacy_and_yaml_areas(grid_configs)
        self.input_scene = input_scene
        self.grid_manager = grid_manager
        self.yaml_areas = yaml_areas

    def has_dynamic_extents(self, area_name: Optional[str]) -> bool:
        area_def = self[area_name]
        is_dynamic = isinstance(area_def, DynamicAreaDefinition)
        return is_dynamic and area_def.area_extent is None

    def __getitem__(self, area_name: Optional[str]) -> Optional[PRGeometry]:
        area_def = _get_area_def_from_name(area_name, self.input_scene, self.grid_manager, self.yaml_areas)
        return area_def

    def get_frozen_area(self, area_name: Optional[str]) -> Optional[PRGeometry]:
        area_def = self[area_name]
        return self._freeze_area_if_dynamic(area_def)

    def _freeze_area_if_dynamic(self, area_def: PRGeometry) -> PRGeometry:
        if isinstance(area_def, DynamicAreaDefinition):
            logger.info("Computing dynamic grid parameters...")
            area_def = area_def.freeze(self.input_scene.max_area())
            logger.debug("Frozen dynamic area: %s", area_def)
        return area_def


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
    resampling_groups = _get_groups_to_resample(resampler, input_scene, is_polar2grid, resample_kwargs)
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
            area_def = area_resolver.get_frozen_area(area_name)
            has_dynamic_extents = area_resolver.has_dynamic_extents(area_name)
            rs = _get_default_resampler(resampler, area_name, area_def, input_scene)
            new_scn = _filter_and_resample_scene_to_single_area(
                area_name,
                area_def,
                _grid_cov,
                has_dynamic_extents,
                scene_to_resample,
                data_ids,
                rs,
                _resample_kwargs,
                preserve_resolution,
            )
            if new_scn is None:
                continue

            # we only want to try to save products that we asked for and that
            # we were actually able to generate. Composite generation may have
            # modified the original DataID so we can't use
            # 'resampled_products'.
            _resampled_products = (new_scn.wishlist & set(new_scn.keys())) - preserved_products
            if _resampled_products:
                scenes_to_save.append((new_scn, _resampled_products))

    return scenes_to_save


def _get_groups_to_resample(
    resampler: str,
    input_scene: Scene,
    is_polar2grid: bool,
    user_resample_kwargs: dict,
) -> dict:
    resampling_dtree = ResamplerDecisionTree.from_configs()
    resampling_groups = {}
    for data_id in input_scene.keys():
        resampling_args = resampling_dtree.find_match(**input_scene[data_id].attrs)
        default_resampler = resampling_args.get("resampler")
        resampler_kwargs = resampling_args.get("kwargs", {}).copy()
        resampler_kwargs.update(user_resample_kwargs)
        default_target = resampling_args.get("default_target", None)
        resampler = resampler if resampler is not None else default_resampler
        if default_target is None:
            default_target = _default_grid(resampler, is_polar2grid)
        hashable_kwargs = _hashable_kwargs(resampler_kwargs)
        resampling_groups.setdefault((resampler, hashable_kwargs, default_target), []).append(data_id)
    return resampling_groups


def _default_grid(resampler, is_polar2grid):
    if resampler in [None, "native"]:
        default_target = "MAX"
    else:
        default_target = "wgs84_fit" if is_polar2grid else "MAX"
    return default_target


def _hashable_kwargs(kwargs):
    return tuple(sorted(kwargs.items()))


def _redict_hashable_kwargs(kwargs_tuple):
    return dict(kwargs_tuple)


def _get_default_resampler(resampler, area_name, area_def, input_scene):
    if resampler is None and area_def is not None:
        rs = "native" if area_name in ["MIN", "MAX"] or _is_native_grid(area_def, input_scene.max_area()) else "nearest"
        logger.debug("Setting default resampling to '{}' for grid '{}'".format(rs, area_name))
    else:
        rs = resampler
    return rs


def _filter_and_resample_scene_to_single_area(
    area_name: str,
    area_def: Optional[PRGeometry],
    grid_coverage: float,
    has_dynamic_extents: bool,
    input_scene: Scene,
    data_ids_to_resample: list,
    rs: str,
    resample_kwargs: dict,
    preserve_resolution: bool,
) -> Optional[Scene]:
    filtered_data_ids, filtered_scn = _filter_scene_with_grid_coverage(
        area_name,
        area_def,
        rs,
        grid_coverage,
        has_dynamic_extents,
        input_scene,
        data_ids_to_resample,
    )
    if filtered_scn is None:
        return
    new_scn = _resample_scene_to_single_area(
        filtered_scn,
        area_name,
        area_def,
        rs,
        filtered_data_ids,
        resample_kwargs,
        preserve_resolution,
    )
    return new_scn


def _is_native_grid(grid, max_native_area):
    """Check if the current grid is in the native data projection."""
    if not isinstance(max_native_area, AreaDefinition):
        return False
    if not isinstance(grid, AreaDefinition):
        return False
    if not _crs_equal(max_native_area, grid):
        return False
    if not np.allclose(np.array(max_native_area.area_extent), np.array(grid.area_extent)):
        return False
    if max_native_area.width < grid.width:
        return (grid.width / max_native_area.width).is_integer()
    else:
        return (max_native_area.width / grid.width).is_integer()


def _filter_scene_with_grid_coverage(
    area_name: str,
    area_def: PRGeometry,
    resampler: str,
    coverage_threshold: float,
    has_dynamic_extents: bool,
    scene_to_resample: Scene,
    data_ids: list,
):
    if area_def is not None and resampler != "native" and coverage_threshold > 0.0 and not has_dynamic_extents:
        logger.info("Checking products for sufficient output grid coverage (grid: '%s')...", area_name)
        filter = ResampleCoverageFilter(target_area=area_def, coverage_fraction=coverage_threshold)
        scene_to_resample = filter.filter_scene(scene_to_resample)
        if scene_to_resample is None:
            logger.warning("No products were found to overlap with '%s' grid.", area_name)
            return None, None
        if data_ids is not None:
            data_ids = list(set(data_ids) & set(scene_to_resample.keys()))
    return data_ids, scene_to_resample


def _resample_scene_to_single_area(
    scene_to_resample: Scene,
    area_name: str,
    area_def: PRGeometry,
    rs: str,
    data_ids: list,
    resample_kwargs: dict,
    preserve_resolution: bool,
) -> Optional[Scene]:
    if area_def is not None:
        logger.info("Resampling to '%s' using '%s' resampling...", area_name, rs)
        logger.debug("Resampling to '%s' using resampler '%s' with %s", area_name, rs, resample_kwargs)
        new_scn = scene_to_resample.resample(area_def, resampler=rs, datasets=data_ids, **resample_kwargs)
    elif not preserve_resolution:
        # the user didn't want to resample to any areas
        # the user also requested that we don't preserve resolution
        # which means we have to save this Scene's datasets
        # because they won't be saved
        new_scn = scene_to_resample
    else:
        # No resampling and any preserved resolution datasets were saved earlier
        return
    return new_scn


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
