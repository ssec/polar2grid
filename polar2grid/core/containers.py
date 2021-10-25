#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2014-2021 Space Science and Engineering Center (SSEC),
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
"""Classes for metadata operations in polar2grid."""

import logging

import numpy
from pyproj import Proj

LOG = logging.getLogger(__name__)


class GridDefinition(dict):
    """Projected grid defined by a PROJ.4 projection string and other grid parameters.

    Required Information:
        - grid_name: Identifying name for the grid
        - proj4_definition (string): PROJ.4 projection definition
        - height: Height of the grid in number of pixels
        - width: Width of the grid in number of pixels
        - cell_height: Grid cell height in the projection domain (usually in meters or degrees)
        - cell_width: Grid cell width in the projection domain (usually in meters or degrees)
        - origin_x: X-coordinate of the upper-left corner of the grid in the projection domain
        - origin_y: Y-coordinate of the upper-left corner of the grid in the projection domain
    """

    required_kwargs = (
        "grid_name",
        "proj4_definition",
        "height",
        "width",
        "cell_height",
        "cell_width",
        "origin_x",
        "origin_y",
    )

    def __init__(self, *args, **kwargs):
        # pyproj.Proj object if needed
        self.p = None
        if "proj4_definition" in kwargs:
            # pyproj doesn't like unicode
            kwargs["proj4_definition"] = str(kwargs["proj4_definition"])
        super(GridDefinition, self).__init__(*args, **kwargs)
        self.validate_keys()

    def validate_keys(self):
        # sanity check, does this dictionary have everything the class expects it to
        for k in self.required_kwargs:
            if k not in self:
                raise ValueError("Missing required keyword '%s'" % (k,))

    def __str__(self):
        keys = sorted(self.keys())
        keys.insert(0, keys.pop(keys.index("height")))
        keys.insert(0, keys.pop(keys.index("width")))
        keys.insert(0, keys.pop(keys.index("cell_height")))
        keys.insert(0, keys.pop(keys.index("cell_width")))
        keys.insert(0, keys.pop(keys.index("proj4_definition")))
        keys.insert(0, keys.pop(keys.index("grid_name")))
        return "\n".join("%s: %s" % (k, self[k]) for k in keys)

    @property
    def proj(self):
        if self.p is None:
            self.p = Proj(self["proj4_definition"])
        return self.p

    @property
    def is_static(self):
        return all(
            [self[x] is not None for x in ["height", "width", "cell_height", "cell_width", "origin_x", "origin_y"]]
        )

    @property
    def lonlat_lowerleft(self):
        x_ll, y_ll = self.xy_lowerleft
        return self.proj(x_ll, y_ll, inverse=True)

    @property
    def lonlat_lowerright(self):
        x_ll, y_ll = self.xy_lowerright
        return self.proj(x_ll, y_ll, inverse=True)

    @property
    def lonlat_upperright(self):
        x_ur, y_ur = self.xy_upperright
        return self.proj(x_ur, y_ur, inverse=True)

    @property
    def lonlat_upperleft(self):
        x_ur, y_ur = self["origin_x"], self["origin_y"]
        return self.proj(x_ur, y_ur, inverse=True)

    @property
    def lonlat_center(self):
        x_pixel = self["width"] / 2
        y_pixel = self["height"] / 2
        return self.get_lonlat(x_pixel, y_pixel)

    def get_lonlat(self, x_pixel, y_pixel):
        x = self["origin_x"] + x_pixel * self["cell_width"]
        y = self["origin_y"] + y_pixel * self["cell_height"]
        return self.proj(x, y, inverse=True)

    @property
    def xy_lowerright(self):
        y_ll = self["origin_y"] + self["cell_height"] * (self["height"] - 1)
        x_ll = self["origin_x"] + self["cell_width"] * (self["width"] - 1)
        return x_ll, y_ll

    @property
    def xy_lowerleft(self):
        y_ll = self["origin_y"] + self["cell_height"] * (self["height"] - 1)
        return self["origin_x"], y_ll

    @property
    def xy_upperright(self):
        x_ll = self["origin_x"] + self["cell_width"] * (self["width"] - 1)
        return x_ll, self["origin_y"]

    @property
    def proj4_dict(self):
        parts = [x.replace("+", "") for x in self["proj4_definition"].split(" ")]
        no_defs = False
        if "no_defs" in parts:
            parts.remove("no_defs")
            no_defs = True
        over = False
        if "over" in parts:
            parts.remove("over")
            over = True

        proj4_dict = dict(p.split("=") for p in parts)
        # Convert numeric parameters to floats
        for k in [
            "lat_0",
            "lat_1",
            "lat_2",
            "lat_ts",
            "lat_b",
            "lat_t",
            "lon_0",
            "lon_1",
            "lon_2",
            "lonc",
            "a",
            "b",
            "f",
            "es",
            "h",
        ]:
            if k in proj4_dict:
                proj4_dict[k] = float(proj4_dict[k])

        # load information from PROJ.4 about the ellipsis if possible
        if "ellps" in proj4_dict and ("a" not in proj4_dict or "b" not in proj4_dict):
            import pyproj

            ellps = pyproj.pj_ellps[proj4_dict["ellps"]]
            proj4_dict["a"] = ellps["a"]
            if "b" not in ellps and "rf" in ellps:
                proj4_dict["f"] = 1.0 / ellps["rf"]
            else:
                proj4_dict["b"] = ellps["b"]

        if "a" in proj4_dict and "f" in proj4_dict and "b" not in proj4_dict:
            # add a "b" attribute back in if they used "f" instead
            proj4_dict["b"] = proj4_dict["a"] * (1 - proj4_dict["f"])

        # Add removed keywords back in
        if no_defs:
            proj4_dict["no_defs"] = True
        if over:
            proj4_dict["over"] = True

        return proj4_dict

    @property
    def gdal_geotransform(self):
        # GDAL PixelIsArea (default) geotiffs expects coordinates for the
        # upper-left corner of the pixel
        # Polar2Grid and satellite imagery formats assume coordinates for
        # center of the pixel
        half_pixel_x = self["cell_width"] / 2.0
        half_pixel_y = self["cell_height"] / 2.0
        # cell_height is negative so we need to substract instead of add
        return (
            self["origin_x"] - half_pixel_x,
            self["cell_width"],
            0,
            self["origin_y"] - half_pixel_y,
            0,
            self["cell_height"],
        )

    def get_xy_arrays(self):
        # the [None] indexing adds a dimension to the array
        x = self["origin_x"] + numpy.repeat(
            numpy.arange(self["width"])[None] * self["cell_width"], self["height"], axis=0
        )
        y = self["origin_y"] + numpy.repeat(
            numpy.arange(self["height"])[:, None] * self["cell_height"], self["width"], axis=1
        )
        return x, y

    def get_geolocation_arrays(self):
        """Calculate longitude and latitude arrays for the grid.

        :returns: (longitude array, latitude array)
        """
        x, y = self.get_xy_arrays()
        return self.proj(x, y, inverse=True)

    def to_basemap_object(self):
        from mpl_toolkits.basemap import Basemap

        proj4_dict = self.proj4_dict
        proj4_dict.pop("no_defs", None)
        proj4_dict.pop("units", None)
        proj4_dict["projection"] = proj4_dict.pop("proj")

        if "a" in proj4_dict and "b" in proj4_dict:
            a = proj4_dict.pop("a")
            b = proj4_dict.pop("b")
            proj4_dict["rsphere"] = (a, b)
        elif "a" in proj4_dict:
            proj4_dict["rsphere"] = proj4_dict.pop("a")
        elif "b" in proj4_dict:
            proj4_dict["rsphere"] = proj4_dict.pop("b")

        lon_ll, lat_ll = self.lonlat_lowerleft
        lon_ur, lat_ur = self.lonlat_upperright
        LOG.debug("Passing basemap the following keywords from PROJ.4: %r", proj4_dict)
        LOG.debug("Lower-left corner: (%f, %f); Upper-right corner: (%f, %f)", lon_ll, lat_ll, lon_ur, lat_ur)
        return Basemap(llcrnrlon=lon_ll, llcrnrlat=lat_ll, urcrnrlon=lon_ur, urcrnrlat=lat_ur, **proj4_dict)

    @property
    def ll_extent(self):
        xy_ll = self.xy_lowerleft
        # NOTE: cell_height is negative
        return xy_ll[0] - self["cell_width"] / 2.0, xy_ll[1] + self["cell_height"] / 2.0

    @property
    def ll_extent_lonlat(self):
        return self.proj(*self.ll_extent, inverse=True)

    @property
    def ur_extent(self):
        xy_ur = self.xy_upperright
        # NOTE: cell_height is negative
        return xy_ur[0] + self["cell_width"] / 2.0, xy_ur[1] - self["cell_height"] / 2.0

    @property
    def ur_extent_lonlat(self):
        return self.proj(*self.ur_extent, inverse=True)

    def to_satpy_area(self):
        from pyresample.geometry import AreaDefinition, DynamicAreaDefinition

        if self.is_static:
            xy_ll = self.ll_extent
            xy_ur = self.ur_extent
            return AreaDefinition(
                self["grid_name"],
                self["grid_name"],
                self["grid_name"],
                self.proj4_dict,
                self["width"],
                self["height"],
                area_extent=xy_ll + xy_ur,
            )
        kwargs = {}
        if self["cell_width"] is not None:
            kwargs["resolution"] = (self["cell_width"], self["cell_height"])
        return DynamicAreaDefinition(
            self["grid_name"], self["grid_name"], self.proj4_dict, self["width"], self["height"], **kwargs
        )
