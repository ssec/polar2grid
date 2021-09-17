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
from pyresample.boundary import AreaDefBoundary, Boundary
from pyresample.spherical import SphPolygon
from pyresample.geometry import get_geostationary_bounding_box, SwathDefinition, AreaDefinition

logger = logging.getLogger(__name__)

PRGeometry = Union[SwathDefinition, AreaDefinition]


def boundary_for_area(area_def: PRGeometry) -> Boundary:
    """Create Boundary object representing the provided area."""
    if isinstance(area_def, SwathDefinition):
        # TODO: Persist lon/lats if requested
        lons, lats = area_def.get_bbox_lonlats()
        lons = da.concatenate(lons)
        lats = da.concatenate(lats)
        freq = int(lons.shape[0] * 0.05)
        lons, lats = da.compute(lons[::freq], lats[::freq])
        adp = Boundary(lons, lats)
    elif area_def.is_geostationary:
        adp = Boundary(*get_geostationary_bounding_box(area_def, nb_points=100))
    else:
        adp = AreaDefBoundary(area_def, frequency=int(area_def.shape[0] * 0.30))
    return adp


@cache
def polygon_for_area(area_def: PRGeometry) -> SphPolygon:
    boundary = boundary_for_area(area_def)
    return boundary.contour_poly
