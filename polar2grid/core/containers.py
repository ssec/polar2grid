#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
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
#
# Written by David Hoese    September 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Classes for metadata operations in polar2grid.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Sept 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import json
import logging
import os
import shutil
import sys
from datetime import datetime

import numpy
from pyproj import Proj

from polar2grid.core.dtype import dtype_to_str, str_to_dtype
from polar2grid.core.time_utils import iso8601

LOG = logging.getLogger(__name__)


# FUTURE: Add a register function to register custom P2G objects so no imports and short __class__ names
# FUTURE: Handling duplicate sub-objects better (ex. geolocation)
class P2GJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super(P2GJSONDecoder, self).__init__(object_hook=self.dict_to_object, **kwargs)

    @staticmethod
    def _jsonclass_to_pyclass(json_class_name):
        import importlib

        cls_name = json_class_name.split(".")[-1]
        mod_name = ".".join(json_class_name.split(".")[:-1])
        if not mod_name:
            try:
                cls = globals()[cls_name]
            except KeyError:
                LOG.error("Unknown class in JSON file: %s", json_class_name)
                raise
        else:
            cls = getattr(importlib.import_module(mod_name), cls_name)
        return cls

    def dict_to_object(self, obj):
        for k, v in obj.items():
            if isinstance(v, str):
                try:
                    obj[k] = iso8601(v)
                    continue
                except ValueError:
                    pass

                try:
                    obj[k] = str_to_dtype(v)
                    continue
                except ValueError:
                    pass

        if "__class__" not in obj:
            LOG.warning("No '__class__' element in JSON file. Using BaseP2GObject by default for now.")
            obj["__class__"] = "BaseP2GObject"
            return BaseP2GObject(**obj)

        cls = self._jsonclass_to_pyclass(obj["__class__"])
        inst = cls(**obj)
        return inst


class P2GJSONEncoder(json.JSONEncoder):
    def iterencode(self, o, _one_shot=False):
        """Taken from:
        http://stackoverflow.com/questions/16405969/how-to-change-json-encoding-behaviour-for-serializable-python-object

        Most of the original method has been left untouched.

        _one_shot is forced to False to prevent c_make_encoder from
        being used. c_make_encoder is a funcion defined in C, so it's easier
        to avoid using it than overriding/redefining it.

        The keyword argument isinstance for _make_iterencode has been set
        to self.isinstance. This allows for a custom isinstance function
        to be defined, which can be used to defer the serialization of custom
        objects to the default method.
        """
        # Force the use of _make_iterencode instead of c_make_encoder
        _one_shot = False

        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = json.encoder.encode_basestring_ascii
        else:
            _encoder = json.encoder.encode_basestring
        # if self.encoding != 'utf-8':
        #     def _encoder(obj, _orig_encoder=_encoder, _encoding=self.encoding):
        #         if isinstance(obj, str):
        #             obj = obj.decode(_encoding)
        #         return _orig_encoder(obj)

        def floatstr(
            obj,
            allow_nan=self.allow_nan,
            _repr=float.__repr__,
            _inf=json.encoder.INFINITY,
            _neginf=-json.encoder.INFINITY,
        ):
            if obj != obj:
                text = "NaN"
            elif obj == _inf:
                text = "Infinity"
            elif obj == _neginf:
                text = "-Infinity"
            else:
                return _repr(obj)

            if not allow_nan:
                raise ValueError("Out of range float values are not JSON compliant: " + repr(obj))

            return text

        # Instead of forcing _one_shot to False, you can also just
        # remove the first part of this conditional statement and only
        # call _make_iterencode
        if _one_shot and json.encoder.c_make_encoder is not None and self.indent is None and not self.sort_keys:
            _iterencode = json.encoder.c_make_encoder(
                markers,
                self.default,
                _encoder,
                self.indent,
                self.key_separator,
                self.item_separator,
                self.sort_keys,
                self.skipkeys,
                self.allow_nan,
            )
        else:
            _iterencode = json.encoder._make_iterencode(
                markers,
                self.default,
                _encoder,
                self.indent,
                floatstr,
                self.key_separator,
                self.item_separator,
                self.sort_keys,
                self.skipkeys,
                _one_shot,
                isinstance=self.isinstance,
            )
        return _iterencode(o, 0)

    def isinstance(self, obj, cls):
        if isinstance(obj, BaseP2GObject):
            return False
        return isinstance(obj, cls)

    def default(self, obj):
        if isinstance(obj, BaseP2GObject):
            mod_str = str(obj.__class__.__module__)
            mod_str = mod_str + "." if mod_str != __name__ else ""
            cls_str = str(obj.__class__.__name__)
            obj = obj.copy(as_dict=True)
            # object should now be a builtin dict
            obj["__class__"] = mod_str + cls_str
            return obj
            # return super(P2GJSONEncoder, self).encode(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif numpy.issubclass_(obj, numpy.number) or isinstance(obj, numpy.dtype):
            return dtype_to_str(obj)
        elif hasattr(obj, "dtype"):
            if obj.size > 1:
                return obj.tolist()
            return int(obj) if numpy.issubdtype(obj, numpy.integer) else float(obj)
        else:
            try:
                return super(P2GJSONEncoder, self).default(obj)
            except TypeError as e:
                print("TypeError:", str(e), type(obj))
                print(obj)
                raise


class BaseP2GObject(dict):
    """Base object for all Polar2Grid dictionary-like objects.

    - required_kwargs: Keys that must exist when loading an object from a JSON file
    - loadable_kwargs: Keys that may be P2G objects saved on disk and should be loaded on creation.
    - cleanup_kwargs: Keys that may be saved files on disk (*not* P2G dict-like objects) and should be removed

    """

    required_kwargs = tuple()
    loadable_kwargs = tuple()
    cleanup_kwargs = tuple()
    child_object_types = {}

    def __init__(self, *args, **kwargs):
        cls = kwargs.pop("__class__", None)
        super(BaseP2GObject, self).__init__(*args, **kwargs)
        self.load_loadable_kwargs()
        self._initialize_children()

        self.persist = False
        if cls:
            # this is being loaded from a serialized/JSON copy
            # we don't have the 'right' to delete any binary files associated with it
            self.set_persist(True)
            self.validate_keys(kwargs)
        else:
            self.set_persist(False)

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        """Delete any files associated with this object."""
        for kw in self.cleanup_kwargs:
            if kw in self and isinstance(self[kw], str):
                # Do we not want to delete this file because someone tried to save the state of this object
                if hasattr(self, "persist") and not self.persist:
                    try:
                        # LOG.debug("Removing associated file that is no longer needed: '%s'", self[kw])
                        os.remove(self[kw])
                    except OSError as e:
                        # if hasattr(e, "errno") and e.errno == 2:
                        #     LOG.debug("Unable to remove file because it doesn't exist: '%s'", self[kw])
                        # else:
                        #     LOG.warning("Unable to remove file: '%s'", self[kw])
                        #     LOG.debug("Unable to remove file traceback:", exc_info=True)
                        pass

    def set_persist(self, persist=True):
        """Set the object to keep associated files on disk even after it has been garbage collected.

        :param persist: Whether to persist or not (True by default)

        """
        self.persist = persist
        for child_key, child in self.items():
            if isinstance(child, BaseP2GObject):
                LOG.debug("Setting persist to %s for child '%s'", str(persist), child_key)
                child.set_persist(persist=persist)

    def validate_keys(self, kwargs):
        # sanity check, does this dictionary have everything the class expects it to
        for k in self.required_kwargs:
            if k not in kwargs:
                raise ValueError("Missing required keyword '%s'" % (k,))

    def load_loadable_kwargs(self):
        if self.loadable_kwargs is None:
            # when every key is loadable
            self.loadable_kwargs = self.keys()

        for kw in self.loadable_kwargs:
            if kw in self and isinstance(self[kw], str):
                LOG.debug("Loading associated JSON file from key {}: '{}'".format(kw, self[kw]))
                self[kw] = BaseP2GObject.load(self[kw])

    @classmethod
    def load(cls, filename, object_class=None):
        """Open a JSON file representing a Polar2Grid object."""
        # Allow the caller to specify the preferred object class if one is not specified in the JSON
        if object_class is None:
            object_class = cls
        if isinstance(filename, str):
            # we are dealing with a string filename
            file_obj = open(filename, "r")
        else:
            # we are dealing with a file-like object
            file_obj = filename

        inst = json.load(file_obj, cls=P2GJSONDecoder)

        if not isinstance(inst, object_class):
            # Need to tell the class that we are loading something from a file so it can take care of persist and such
            inst["__class__"] = object_class.__name__
            return object_class(**inst)
        return inst

    def _initialize_children(self):
        # LOG.debug("Initializing children for {}".format(self.__class__.__name__))
        for child_key, child_type in self.child_object_types.items():
            if child_key is None:
                # Child key being None, means that all children should be of this type
                for ck in self.keys():
                    if self.get(ck, None) and not isinstance(self[ck], child_type):
                        LOG.debug("Reinitializing child {} to {}".format(ck, child_type.__name__))
                        self[ck] = child_type(**self[ck])
                continue

            if self.get(child_key, None) and not isinstance(self[child_key], child_type):
                LOG.debug("Reinitializing child {} to {}".format(child_key, child_type.__name__))
                self[child_key] = child_type(**self[child_key])

    def save(self, filename):
        """Write the JSON representation of this class to a file."""
        f = open(filename, "w")
        try:
            json.dump(self, f, cls=P2GJSONEncoder, indent=4, sort_keys=True)
            self.set_persist()
        except TypeError:
            LOG.error("Could not write P2G object to JSON file: '%s'", filename, exc_info=True)
            f.close()
            os.remove(filename)
            raise

    def dumps(self, persist=False):
        """Return a JSON string version of the object.

        :param persist: If True, change 'persist' attribute of object so files already on disk don't get deleted
        """
        if persist:
            self.set_persist()
        return json.dumps(self, cls=P2GJSONEncoder, indent=4, sort_keys=True)

    def copy(self, as_dict=False):
        """Copy this object in to a separate object.

        .. note::

            Any on-disk files or external references must be handled separately.

        """
        if as_dict:
            return dict.copy(self)
        else:
            return self.__class__(dict.copy(self))


class GridDefinition(BaseP2GObject):
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
