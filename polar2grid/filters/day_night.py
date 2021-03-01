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
"""Filter classes for making decisions based on day or night percentages."""

import logging

try:
    # Python 3.9+
    from functools import cache
except ImportError:
    from functools import lru_cache as cache

import numpy as np
from xarray import DataArray
from satpy import Scene
import dask.array as da
from pyorbital.astronomy import sun_zenith_angle
from pyresample.boundary import AreaDefBoundary, Boundary
from pyresample.spherical import SphPolygon
from pyresample.geometry import get_geostationary_bounding_box, SwathDefinition

logger = logging.getLogger(__name__)


@cache
def _get_sunlight_coverage(area_def, start_time, sza_threshold=90, overpass=None):
    """Get the sunlight coverage of *area_def* at *start_time* as a value between 0 and 1."""
    if isinstance(area_def, SwathDefinition):
        lons, lats = area_def.get_lonlats()
        freq = int(lons.shape[-1] * 0.10)
        lons, lats = da.compute(lons[::freq, ::freq], lats[::freq, ::freq])
        adp = Boundary(lons.ravel(), lats.ravel()).contour_poly
    elif area_def.is_geostationary:
        adp = Boundary(
            *get_geostationary_bounding_box(area_def,
                                            nb_points=100)).contour_poly
    else:
        adp = AreaDefBoundary(area_def, frequency=100).contour_poly
    poly = get_twilight_poly(start_time)
    if overpass is not None:
        ovp = overpass.boundary.contour_poly
        cut_area_poly = adp.intersection(ovp)
    else:
        cut_area_poly = adp

    if cut_area_poly is None:
        if not adp._is_inside(ovp):
            return 0.0
        else:
            # Should already have been taken care of in pyresample.spherical.intersection
            cut_area_poly = adp

    daylight = cut_area_poly.intersection(poly)
    if daylight is None:
        if sun_zenith_angle(start_time, *area_def.get_lonlat(0, 0)) < sza_threshold:
            return 1.0
        else:
            return 0.0
    else:
        daylight_area = daylight.area()
        total_area = adp.area()
        return daylight_area / total_area


def modpi(val, mod=np.pi):
    """Puts *val* between -*mod* and *mod*."""
    return (val + mod) % (2 * mod) - mod


def get_twilight_poly(utctime):
    """Return a polygon enclosing the sunlit part of the globe at *utctime*."""
    from pyorbital import astronomy
    ra, dec = astronomy.sun_ra_dec(utctime)
    lon = modpi(ra - astronomy.gmst(utctime))
    lat = dec

    vertices = np.zeros((4, 2))

    vertices[0, :] = modpi(lon - np.pi / 2), 0
    if lat <= 0:
        vertices[1, :] = lon, np.pi / 2 + lat
        vertices[3, :] = modpi(lon + np.pi), -(np.pi / 2 + lat)
    else:
        vertices[1, :] = modpi(lon + np.pi), np.pi / 2 - lat
        vertices[3, :] = lon, -(np.pi / 2 - lat)

    vertices[2, :] = modpi(lon + np.pi / 2), 0

    return SphPolygon(vertices)


class CoverageFilter:
    """Base class for filtering based on day/night coverage."""

    FILTER_MSG = "Unloading '{}' because there is not enough day/night coverage."

    def __init__(self,
                 product_filter_criteria: dict = None,
                 sza_threshold: float = 100.0,
                 fraction: float = 0.1):
        """Initialize thresholds and default search criteria."""
        self._filter_criteria = product_filter_criteria or {}
        self._sza_threshold = sza_threshold
        self._fraction = fraction

    def _matches_criteria(self, data_arr: DataArray):
        attrs = data_arr.attrs
        for filter_key, filter_list in self._filter_criteria.items():
            if attrs.get(filter_key) in filter_list:
                return True
        return False

    def _should_be_filtered(self, sunlight_coverage):
        raise NotImplementedError("Subclass must implement the filter decision")

    def _filter_data_array(self, data_arr: DataArray, _cache: dict):
        """Check if this DataArray should be removed.

        Returns:
            True if it meets the condition and does not have enough
            day data and should therefore be removed. False otherwise
            meaning it should be kept.

        """
        if not self._matches_criteria(data_arr):
            return False

        area = data_arr.attrs['area']
        start_time = data_arr.attrs['start_time']
        end_time = data_arr.attrs['end_time']
        mid_time = start_time + (end_time - start_time) / 2
        sza_threshold = self._sza_threshold
        if area not in _cache:
            slc = _get_sunlight_coverage(area, mid_time, sza_threshold)
            logger.debug("Sunlight is estimated to cover %0.2f%% of the scene.", slc * 100)
            _cache[area] = self._should_be_filtered(slc)
        return _cache[area]

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


class DayCoverageFilter(CoverageFilter):
    """Remove certain products when there is not enough day data."""

    FILTER_MSG = "Unloading '{}' because there is not enough day data."

    def __init__(self,
                 product_filter_criteria: dict = None,
                 sza_threshold: float = 100.0,
                 day_fraction: float = 0.1):
        """Initialize thresholds and default search criteria."""
        product_filter_criteria = product_filter_criteria or {}
        matching_standard_names = ['toa_bidirectional_reflectance', 'true_color', 'natural_color', 'false_color']
        product_filter_criteria.setdefault('standard_name', matching_standard_names)

        super().__init__(product_filter_criteria,
                         sza_threshold=sza_threshold,
                         fraction=day_fraction)

    def _should_be_filtered(self, sunlight_coverage):
        return sunlight_coverage < self._fraction


class NightCoverageFilter(CoverageFilter):
    """Remove certain products when there is not enough day data."""

    FILTER_MSG = "Unloading '{}' because there is not enough night data."

    def __init__(self,
                 product_filter_criteria: dict = None,
                 sza_threshold: float = 100.0,
                 night_fraction: float = 0.1):
        """Initialize thresholds and default search criteria."""
        product_filter_criteria = product_filter_criteria or {}
        matching_standard_names = ['temperature_difference']
        product_filter_criteria.setdefault('standard_name', matching_standard_names)

        super().__init__(product_filter_criteria,
                         sza_threshold=sza_threshold,
                         fraction=night_fraction)

    def _should_be_filtered(self, sunlight_coverage):
        return (1 - sunlight_coverage) < self._fraction