#!/usr/bin/env python3
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
"""Helper functions for filtering certain products."""

import importlib
from typing import Union, Optional, List, Dict
import logging

from satpy import Scene
from .day_night import DayCoverageFilter, NightCoverageFilter

logger = logging.getLogger(__name__)


def _merge_filter_critera(*readers_criteria: Dict[str, Union[List[str], None]]):
    result = {}
    for reader_criteria in readers_criteria:
        for criteria_key, criteria_value in reader_criteria.items():
            if criteria_value is not None:
                result.setdefault(criteria_key, []).extend(criteria_value)
    return result


def _get_single_reader_filter_criteria(reader: str, filter_name: str):
    reader_mod = importlib.import_module('polar2grid.readers.' + reader)
    filter_criteria = getattr(reader_mod, 'FILTERS', {})
    return filter_criteria[filter_name]


def get_reader_filter_criteria(reader_names: List[str], filter_name: str):
    """Get reader configured filter information."""
    readers_criteria = [_get_single_reader_filter_criteria(reader, filter_name)
                        for reader in reader_names]
    criteria = _merge_filter_critera(*readers_criteria)
    return criteria


def _filter_scene_day_only_products(input_scene: Scene, filter_criteria: dict,
                                    sza_threshold: float = 100.0,
                                    day_fraction: Optional[float] = None):
    """Run filtering for products that need a certain amount of day data."""
    if day_fraction is None:
        day_fraction = 0.1
    logger.info("Running day coverage filtering...")
    day_filter = DayCoverageFilter(filter_criteria,
                                   sza_threshold=sza_threshold,
                                   day_fraction=day_fraction)
    return day_filter.filter_scene(input_scene)


def _filter_scene_night_only_products(input_scene: Scene, filter_criteria: dict,
                                      sza_threshold: float = 100.0,
                                      night_fraction: Optional[float] = None):
    """Run filtering for products that need a certain amount of day data."""
    if night_fraction is None:
        night_fraction = 0.1
    logger.info("Running night coverage filtering...")
    night_filter = NightCoverageFilter(filter_criteria,
                                       sza_threshold=sza_threshold,
                                       night_fraction=night_fraction)
    return night_filter.filter_scene(input_scene)


def filter_scene(input_scene: Scene,
                 reader_names: List[str],
                 sza_threshold: float = 100.0,
                 day_fraction: Optional[float] = None,
                 night_fraction: Optional[float] = None,
                 ):
    if day_fraction is not False:
        criteria = get_reader_filter_criteria(reader_names, 'day_only')
        input_scene = _filter_scene_day_only_products(
            input_scene,
            criteria,
            sza_threshold=sza_threshold,
            day_fraction=day_fraction,
        )
    if night_fraction is not False:
        criteria = get_reader_filter_criteria(reader_names, 'night_only')
        input_scene = _filter_scene_night_only_products(
            input_scene,
            criteria,
            sza_threshold=sza_threshold,
            night_fraction=night_fraction,
        )
    return input_scene
