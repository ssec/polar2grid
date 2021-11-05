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
"""Utilities related to filtering."""

import logging

try:
    # Python 3.9+
    from functools import cache
except ImportError:
    from functools import lru_cache as cache

from typing import Union

import dask.array as da
import numpy as np
import pyresample
from packaging.version import Version, parse
from pyresample.boundary import AreaBoundary, AreaDefBoundary, Boundary
from pyresample.geometry import (
    AreaDefinition,
    SwathDefinition,
    get_geostationary_bounding_box,
)
from pyresample.spherical import SphPolygon

logger = logging.getLogger(__name__)
FIXED_PR = parse(pyresample.__version__) >= Version("1.22.1")

PRGeometry = Union[SwathDefinition, AreaDefinition]


def boundary_for_area(area_def: PRGeometry) -> Boundary:
    """Create Boundary object representing the provided area."""
    if not FIXED_PR and isinstance(area_def, SwathDefinition):
        # TODO: Persist lon/lats if requested
        lons, lats = area_def.get_bbox_lonlats()
        freq = int(area_def.shape[0] * 0.05)
        if hasattr(lons[0], "compute") and da is not None:
            lons, lats = da.compute(lons, lats)
        lons = [lon_side.astype(np.float64) for lon_side in lons]
        lats = [lat_side.astype(np.float64) for lat_side in lats]
        # compare the first two pixels in the right column
        lat_is_increasing = lats[1][0] < lats[1][1]
        # compare the first two pixels in the "top" column
        lon_is_increasing = lons[0][0] < lons[0][1]
        is_ccw = (lon_is_increasing and lat_is_increasing) or (not lon_is_increasing and not lat_is_increasing)
        if is_ccw:
            # going counter-clockwise
            # swap the side order and the order of the values in each side
            # to make it clockwise
            lons = [lon[::-1] for lon in lons[::-1]]
            lats = [lat[::-1] for lat in lats[::-1]]
        adp = AreaBoundary(*zip(lons, lats))
        adp.decimate(freq)
    elif getattr(area_def, "is_geostationary", False):
        adp = Boundary(*get_geostationary_bounding_box(area_def, nb_points=100))
    else:
        freq_fraction = 0.05 if isinstance(area_def, SwathDefinition) else 0.30
        adp = AreaDefBoundary(area_def, frequency=int(area_def.shape[0] * freq_fraction))
    return adp


@cache
def polygon_for_area(area_def: PRGeometry) -> SphPolygon:
    boundary = boundary_for_area(area_def)
    return boundary.contour_poly
