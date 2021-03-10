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
"""Filter classes dealing with resampling output coverage."""

import logging

try:
    # Python 3.9+
    from functools import cache
except ImportError:
    from functools import lru_cache as cache

from ._base import BaseFilter
from ._utils import PRGeometry

from xarray import DataArray
from ._utils import polygon_for_area
from pyresample.spherical import SphPolygon

logger = logging.getLogger(__name__)

@cache
def _get_intersection_coverage(source_polygon: SphPolygon, target_polygon: SphPolygon) -> float:
    """Get fraction of output grid that will be filled with input data."""
    intersect_polygon = source_polygon.intersection(target_polygon)
    if intersect_polygon is None:
        return 0.0
    return intersect_polygon.area() / target_polygon.area()


class ResampleCoverageFilter(BaseFilter):
    """Remove any DataArrays that would not """

    def __init__(self,
                 product_filter_criteria: dict = None,
                 target_area: PRGeometry = None,
                 coverage_fraction: float = None,
                 ):
        """Initialize thresholds and default search criteria."""
        super().__init__(product_filter_criteria)
        if target_area is None:
            raise ValueError("'target_area' is required.")
        if coverage_fraction is None:
            raise ValueError("'coverage_fraction' is required.")
        self._target_area = target_area
        self._target_polygon = polygon_for_area(self._target_area)
        self._coverage_fraction = coverage_fraction

    def _filter_data_array(self, data_arr: DataArray, _cache: dict):
        """Check if this DataArray should be removed.

        Returns:
            True if it meets the condition and does not have enough
            day data and should therefore be removed. False otherwise
            meaning it should be kept.

        """
        if not self._matches_criteria(data_arr):
            return False

        source_area = data_arr.attrs.get('area')
        if source_area is None:
            return False

        source_polygon = polygon_for_area(source_area)
        coverage_fraction = _get_intersection_coverage(source_polygon, self._target_polygon)
        if coverage_fraction >= self._coverage_fraction:
            logger.debug("Resampling found %f%% coverage.", coverage_fraction * 100)
            return False
        logger.warning("Resampling found %f%% of the output grid covered. "
                       "Will skip producing this product: %s",
                       coverage_fraction * 100, data_arr.attrs['name'])
        return True
