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
"""Base class for all filters."""

import logging

from xarray import DataArray
from satpy import Scene

logger = logging.getLogger(__name__)


class BaseFilter:
    """Base class for filtering products that don't match certain conditions.

    This class uses a series of metadata comparisons to check if a product
    should be checked for filtering. If any of the product metadata criteria
    match then filtering checks are continued. Otherwise, the product is
    ignored. If the criteria is not provided, then all products will be
    checked.

    By default, no extra filtering is performed and only the metadata criteria
    is used. This means that if no criteria is provided, this class will
    remove all provided DataArrays.

    """

    FILTER_MSG = "Unloading '{}' due to filtering."

    def __init__(self, product_filter_criteria: dict = None):
        """Initialize thresholds and default search criteria."""
        self._filter_criteria = product_filter_criteria or {}

    def _matches_criteria(self, data_arr: DataArray):
        attrs = data_arr.attrs
        if not self._filter_criteria:
            # if not criteria was provided then filtering should be performed
            return True

        for filter_key, filter_list in self._filter_criteria.items():
            if attrs.get(filter_key) in filter_list:
                return True
        return False

    def _filter_data_array(self, data_arr: DataArray, _cache: dict):
        """Check if this DataArray should be removed.

        Returns:
            True if it meets the condition and does not have enough
            day data and should therefore be removed. False otherwise
            meaning it should be kept.

        """
        if not self._matches_criteria(data_arr):
            return False
        # Subclasses should implement further logic here
        return True

    def filter_scene(self, scene: Scene):
        """Create a new Scene with filtered DataArrays removed."""
        _cache = {}
        remaining_ids = []
        filtered_ids = []
        for data_id in scene.keys():
            logger.debug("Analyzing '{}' for filtering...".format(data_id))
            if not self._filter_data_array(scene[data_id], _cache):
                remaining_ids.append(data_id)
            else:
                logger.debug(self.FILTER_MSG.format(data_id))
                filtered_ids.append(data_id)
        if not remaining_ids:
            return None
        new_scn = scene.copy(remaining_ids)
        new_scn._wishlist = scene.wishlist.copy()
        return new_scn
