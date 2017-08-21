#!/usr/bin/env python
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

import os
import sys
import json
import shutil
import logging
from datetime import datetime

import numpy

from polar2grid.core.time_utils import iso8601
from polar2grid.core.dtype import str_to_dtype, dtype_to_str
from polar2grid.core.proj import Proj


LOG = logging.getLogger(__name__)


# FUTURE: Add a register function to register custom P2G objects so no imports and short __class__ names
# FUTURE: Handling duplicate sub-objects better (ex. geolocation)
class P2GJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super(P2GJSONDecoder, self).__init__(object_hook=self.dict_to_object, *args, **kwargs)

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
        else:
            cls = getattr(importlib.import_module(mod_name), cls_name)
        return cls

    def dict_to_object(self, obj):
        for k, v in obj.items():
            if isinstance(v, (str, unicode)):
                try:
                    obj[k] = iso8601(v)
                    continue
                except ValueError:
                    pass

                try:
                    obj[k] = str_to_dtype(v)
                    continue
                except StandardError:
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
        if self.encoding != 'utf-8':
            def _encoder(o, _orig_encoder=_encoder, _encoding=self.encoding):
                if isinstance(o, str):
                    o = o.decode(_encoding)
                return _orig_encoder(o)

        def floatstr(o, allow_nan=self.allow_nan,
                     _repr=json.encoder.FLOAT_REPR, _inf=json.encoder.INFINITY, _neginf=-json.encoder.INFINITY):
            if o != o:
                text = 'NaN'
            elif o == _inf:
                text = 'Infinity'
            elif o == _neginf:
                text = '-Infinity'
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text

        # Instead of forcing _one_shot to False, you can also just
        # remove the first part of this conditional statement and only
        # call _make_iterencode
        if (_one_shot and json.encoder.c_make_encoder is not None
                and self.indent is None and not self.sort_keys):
            _iterencode = json.encoder.c_make_encoder(
                markers, self.default, _encoder, self.indent,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, self.allow_nan)
        else:
            _iterencode = json.encoder._make_iterencode(
                markers, self.default, _encoder, self.indent, floatstr,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, _one_shot, isinstance=self.isinstance)
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
        elif numpy.issubclass_(obj, numpy.number):
            return dtype_to_str(obj)
        else:
            return super(P2GJSONEncoder, self).default(obj)


class BaseP2GObject(dict):
    """Base object for all Polar2Grid dictionary-like objects.

    :var required_kwargs: Keys that must exist when loading an object from a JSON file
    :var loadable_kwargs: Keys that may be P2G objects saved on disk and should be loaded on creation.
    :var cleanup_kwargs: Keys that may be saved files on disk (*not* P2G dict-like objects) and should be removed

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
        """Delete any files associated with this object.
        """
        for kw in self.cleanup_kwargs:
            if kw in self and isinstance(self[kw], (str, unicode)):
                # Do we not want to delete this file because someone tried to save the state of this object
                if hasattr(self, "persist") and not self.persist:
                    try:
                        LOG.debug("Removing associated file that is no longer needed: '%s'", self[kw])
                        os.remove(self[kw])
                    except StandardError as e:
                        if hasattr(e, "errno") and e.errno == 2:
                            LOG.debug("Unable to remove file because it doesn't exist: '%s'", self[kw])
                        else:
                            LOG.warning("Unable to remove file: '%s'", self[kw])
                            LOG.debug("Unable to remove file traceback:", exc_info=True)

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
            if kw in self and isinstance(self[kw], (str, unicode)):
                LOG.debug("Loading associated JSON file from key {}: '{}'".format(kw, self[kw]))
                self[kw] = BaseP2GObject.load(self[kw])

    @classmethod
    def load(cls, filename, object_class=None):
        """Open a JSON file representing a Polar2Grid object.
        """
        # Allow the caller to specify the preferred object class if one is not specified in the JSON
        if object_class is None:
            object_class = cls
        if isinstance(filename, (str, unicode)):
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
        """Write the JSON representation of this class to a file.
        """
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


class GeographicDefinition(BaseP2GObject):
    """Base class for objects that define a geographic area.
    """
    pass


class BaseProduct(BaseP2GObject):
    """Base product class for storing metadata.
    """
    def _memmap(self, fn, dtype, rows, cols, mode):
        # load FBF data from a file if needed
        data = numpy.memmap(fn, dtype=dtype, mode=mode).reshape((-1, rows, cols))
        # the negative 1 in the above reshape makes it expand to the proper dimensions for the data without
        # copying. The below if statement checks if we have a regular 2D array. If so, just return that 2D array.
        if data.shape[0] == 1:
            data = data.reshape((rows, cols))
        return data

    def get_data_array(self, item, rows, cols, dtype, mode="r"):
        """Get FBF item as a numpy array.

        File is loaded from disk as a memory mapped file if needed.
        """
        data = self[item]
        if isinstance(data, (str, unicode)):
            data = self._memmap(data, dtype, rows, cols, mode)

        return data

    def get_data_mask(self, item, fill=numpy.nan, fill_key=None):
        """Return a boolean mask where the data for `item` is invalid/bad.
        """
        data = self.get_data_array(item)

        if fill_key is not None:
            fill = self[fill_key]

        if numpy.isnan(fill):
            return numpy.isnan(data)
        else:
            return data == fill

    def copy_array(self, item, rows, cols, dtype, filename=None, read_only=True):
        """Copy the array item of this swath.

        If the `filename` keyword is passed the data will be written to that file. The copy returned
        will be a memory map. If `read_only` is False, the memory map will be opened with mode "r+".

        The 'read_only' keyword is ignored if `filename` is None.
        """
        mode = "r" if read_only else "r+"
        data = self[item]

        if isinstance(data, (str, unicode)):
            # we have a binary filename
            if filename:
                # the user wants to copy the FBF
                shutil.copyfile(data, filename)
                data = filename
                return self._memmap(data, dtype, rows, cols, mode)
            if mode == "r":
                return self._memmap(data, dtype, rows, cols, "r")
            else:
                return self._memmap(data, dtype, rows, cols, "r").copy()
        else:
            if filename:
                data.tofile(filename)
                return self._memmap(data, dtype, rows, cols, mode)
            return data.copy()


class BaseScene(BaseP2GObject):
    """Base scene class mapping product name to product metadata object.
    """
    # special value when every key is loadable
    loadable_kwargs = None

    def get_fill_value(self, products=None):
        """Get the fill value shared by the products specified (all products by default).
        """
        products = products or self.keys()
        fills = [self[product].get("fill_value", numpy.nan) for product in products]
        if numpy.isnan(fills[0]):
            fills_same = numpy.isnan(fills).all()
        else:
            fills_same = all(f == fills[0] for f in fills)
        if not fills_same:
            raise RuntimeError("Scene's products don't all share the same fill value")
        return fills[0]

    def get_begin_time(self):
        """Get the begin time shared by all products in the scene.
        """
        products = self.keys()
        return self[products[0]]["begin_time"]

    def get_end_time(self):
        """Get the end time shared by all products in the scene.
        """
        products = self.keys()
        return self[products[0]]["end_time"]


class SwathDefinition(GeographicDefinition, BaseProduct):
    """Geographic area defined by longitude and latitude points.

    Required Information:
        - swath_name: Give a descriptive name to the swath definition (used for filenaming if needed)
        - longitude (array): Binary filename or numpy array for the main data array
        - latitude (array): Binary filename or numpy array for the main data array
        - data_type (numpy.dtype): Data type of image data or if on disk on of (real4, int1, uint1, etc)
        - swath_rows (int): Number of rows in the main 2D data array
        - swath_columns (int): Number of columns in the main 2D data array

    Optional Information:
        - nadir_resolution (float): Size in meters of instrument's nadir footprint/pixel
        - limb_resolution (float): Size in meters of instrument's edge footprint/pixel
        - rows_per_scan (int): Number of swath rows making up one scan of the sensor (0 if not applicable or not specified)
        - description (string): Basic description of the product (empty string by default)
        - source_filenames (list of strings): Unordered list of source files that made up this product ([] by default)
        - fill_value: Missing data value in 'swath_data' (defaults to `numpy.nan` if not present)
    """
    # Validate required keys when loaded from disk
    required_kwargs = (
        "swath_name",
        "longitude",
        "latitude",
        "data_type",
        "swath_rows",
        "swath_columns",
    )

    loadable_kwargs = (
    )

    cleanup_kwargs = (
        "longitude",
        "latitude",
    )

    def get_data_array(self, item, mode="r"):
        # Need this because otherwise get_data_mask won't work properly
        dtype = self["data_type"]
        rows = self["swath_rows"]
        cols = self["swath_columns"]
        return super(SwathDefinition, self).get_data_array(item, rows, cols, dtype)

    def get_longitude_array(self):
        return self.get_data_array("longitude")

    def get_latitude_array(self):
        return self.get_data_array("latitude")

    def copy_longitude_array(self, filename=None, read_only=True):
        dtype = self["data_type"]
        rows = self["swath_rows"]
        cols = self["swath_columns"]
        return super(SwathDefinition, self).copy_array("longitude", rows, cols, dtype, filename, read_only)

    def copy_latitude_array(self, filename=None, read_only=True):
        dtype = self["data_type"]
        rows = self["swath_rows"]
        cols = self["swath_columns"]
        return super(SwathDefinition, self).copy_array("latitude", rows, cols, dtype, filename, read_only)

    def get_longitude_mask(self, item="longitude"):
        return self.get_data_mask(item)

    def get_latitude_mask(self, item="latitude"):
        return self.get_data_mask(item)


class GridDefinition(GeographicDefinition):
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
        return all([self[x] is not None for x in [
            "height", "width", "cell_height", "cell_width", "origin_x", "origin_y"
        ]])

    @property
    def is_latlong(self):
        return self.proj.is_latlong()

    @property
    def cell_width_meters(self):
        """Estimation of what a latlong cell width would be in meters.
        """
        proj4_dict = self.proj4_dict
        lon0 = proj4_dict.get("lon0", 0.0)
        lat0 = proj4_dict.get("lat0", 0.0)
        p = Proj("+proj=eqc +lon0=%f +lat0=%f" % (lon0, lat0))
        x0, y0 = p(lon0, lat0)
        x1, y1 = p(lon0+self["cell_width"], lat0)
        return abs(x1 - x0)

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
        y_ll = self["origin_y"] + self["cell_height"] * self["height"]
        x_ll = self["origin_x"] + self["cell_width"] * self["width"]
        return x_ll, y_ll

    @property
    def xy_lowerleft(self):
        y_ll = self["origin_y"] + self["cell_height"] * self["height"]
        return self["origin_x"], y_ll

    @property
    def xy_upperright(self):
        x_ll = self["origin_x"] + self["cell_width"] * self["width"]
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
        for k in ["lat_0", "lat_1", "lat_2", "lat_ts", "lat_b", "lat_t", "lon_0", "lon_1", "lon_2", "lonc", "a", "b", "f", "es", "h"]:
            if k in proj4_dict:
                proj4_dict[k] = float(proj4_dict[k])

        # load information from PROJ.4 about the ellipsis if possible
        if "ellps" in proj4_dict and "a" not in proj4_dict or "b" not in proj4_dict:
            import pyproj
            ellps = pyproj.pj_ellps[proj4_dict["ellps"]]
            proj4_dict["a"] = ellps["a"]
            if "b" not in ellps and "rf" in ellps:
                proj4_dict["f"] = 1. / ellps["rf"]
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
        half_pixel_x = self['cell_width'] / 2.
        half_pixel_y = self['cell_height'] / 2.
        # cell_height is negative so we need to substract instead of add
        return self["origin_x"] - half_pixel_x, self["cell_width"], 0, self["origin_y"] - half_pixel_y, 0, self["cell_height"]

    def get_xy_arrays(self):
        # the [None] indexing adds a dimension to the array
        x = self["origin_x"] + numpy.repeat(numpy.arange(self["width"])[None] * self["cell_width"], self["height"], axis=0)
        y = self["origin_y"] + numpy.repeat(numpy.arange(self["height"])[:, None] * self["cell_height"], self["width"], axis=1)
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
        return xy_ll[0] - self["cell_width"]/2., xy_ll[1] + self["cell_height"]/2.

    @property
    def ll_extent_lonlat(self):
        return self.proj(*self.ll_extent, inverse=True)

    @property
    def ur_extent(self):
        xy_ur = self.xy_upperright
        return xy_ur[0] + self["cell_width"]/2., xy_ur[1] - self["cell_height"]/2.

    @property
    def ur_extent_lonlat(self):
        return self.proj(*self.ur_extent, inverse=True)

    def to_satpy_area(self):
        from pyresample.geometry import AreaDefinition
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


class SwathProduct(BaseProduct):
    """Swath product class for image products geolocated using longitude and latitude points.

    Required Information:
        - product_name (string): Name of the product this swath represents
        - satellite (string): Name of the satellite the data came from
        - instrument (string): Name of the instrument on the satellite from which the data was observed
        - begin_time (datetime): Datetime object representing the best known start of observation for this product's data
        - end_time (datetime): Datetime object representing the best known end of observation for this product's data
        - swath_definition (`SwathDefinition` object): definition of the geographic area covered by this swath (None is not applicable)
        - data_type (numpy.dtype): Data type of image data or if on disk on of (real4, int1, uint1, etc)
        - swath_rows (int): Number of rows in the main 2D data array
        - swath_columns (int): Number of columns in the main 2D data array
        - swath_data (array): Binary filename or numpy array for the main data array

    Optional Information:
        - description (string): Basic description of the product (empty string by default)
        - source_filenames (list of strings): Unordered list of source files that made up this product ([] by default)
        - data_kind (string): Name for the type of the measurement (ex. btemp, reflectance, radiance, etc.)
        - rows_per_scan (int): Number of swath rows making up one scan of the sensor (0 if not applicable or not specified)
        - units (string): Image data units (empty string by default)
        - fill_value: Missing data value in 'swath_data' (defaults to `numpy.nan` if not present)

    .. note::

        When datetime objects are written to disk as JSON they are converted to ISO8601 strings.

    .. seealso::

        `GriddedProduct`: Product object for gridded products.

    """
    # Validate required keys when loaded from disk
    required_kwargs = (
        "product_name",
        "satellite",
        "instrument",
        "begin_time",
        "end_time",
        "data_type",
        "swath_data",
        "swath_definition",
    )

    loadable_kwargs = (
        "swath_definition",
    )

    cleanup_kwargs = (
        "swath_data",
    )

    child_object_types = {
        "swath_definition": SwathDefinition,
        }

    def __init__(self, *args, **kwargs):
        super(SwathProduct, self).__init__(*args, **kwargs)

    @property
    def shape(self):
        return (self["swath_rows"], self["swath_columns"])

    def get_data_array(self, item="swath_data", mode="r"):
        dtype = self["data_type"]
        rows = self["swath_definition"]["swath_rows"]
        cols = self["swath_definition"]["swath_columns"]
        return super(SwathProduct, self).get_data_array(item, rows, cols, dtype, mode=mode)

    def get_data_mask(self, item="swath_data"):
        return super(SwathProduct, self).get_data_mask(item, fill_key="fill_value")

    def copy_array(self, item="swath_data", filename=None, read_only=True):
        dtype = self["data_type"]
        rows = self["swath_rows"]
        cols = self["swath_columns"]
        return super(SwathProduct, self).copy_array(item, rows, cols, dtype, filename, read_only)


class GriddedProduct(BaseProduct):
    """Gridded product class for image products on a uniform, projected grid.

    Required Information:
        - product_name: Name of the product this swath represents
        - satellite: Name of the satellite the data came from
        - instrument: Name of the instrument on the satellite from which the data was observed
        - begin_time: Datetime object representing the best known start of observation for this product's data
        - end_time: Datetime object represnting the best known end of observation for this product's data
        - data_type (string): Data type of image data (real4, uint1, int1, etc)
        - grid_data: Binary filename or numpy array for the main data array

    Optional Information:
        - description (string): Basic description of the product (empty string by default)
        - source_filenames (list of strings): Unordered list of source files that made up this product ([] by default)
        - data_kind (string): Name for the type of the measurement (ex. btemp, reflectance, radiance, etc.)
        - fill_value: Missing data value in 'swath_data' (defaults to `numpy.nan` if not present)

    .. seealso::

        `SwathProduct`: Product object for products using longitude and latitude for geolocation.

    """
    # Validate required keys when loaded from disk
    required_kwargs = (
        "product_name",
        "satellite",
        "instrument",
        "begin_time",
        "end_time",
        "data_type",
        "grid_data",
        "grid_definition",
    )

    loadable_kwargs = (
        "grid_definition",
    )

    cleanup_kwargs = (
        "grid_data",
    )

    child_object_types = {
        "grid_definition": GridDefinition,
        }

    @property
    def shape(self):
        return (self["grid_definition"]["height"], self["grid_definition"]["width"])

    def from_swath_product(self, swath_product):
        # for k in ["product_name", "satellite", "instrument",
        #           "begin_time", "end_time", "data_type", "data_kind",
        #           "description", "source_filenames", "units"]:
        #     if k in swath_product:
        #         self[k] = swath_product[k]
        info = swath_product.copy(as_dict=True)
        for k in ["swath_rows", "swath_cols", "swath_data", "swath_definition"]:
            info.pop(k, None)
        self.update(**swath_product)

    def get_data_array(self, item="grid_data", mode="r"):
        """Get FBF item as a numpy array.

        File is loaded from disk as a memory mapped file if needed.
        """
        dtype = self["data_type"]
        rows = self["grid_definition"]["height"]
        cols = self["grid_definition"]["width"]
        return super(GriddedProduct, self).get_data_array(item, rows, cols, dtype, mode=mode)

    def get_data_mask(self, item="grid_data"):
        return super(GriddedProduct, self).get_data_mask(item, fill_key="fill_value")

    def copy_array(self, item="grid_data", filename=None, read_only=True):
        """Copy the array item of this swath.

        If the `filename` keyword is passed the data will be written to that file. The copy returned
        will be a memory map. If `read_only` is False, the memory map will be opened with mode "r+".

        The 'read_only' keyword is ignored if `filename` is None.
        """
        dtype = self["data_type"]
        rows = self["grid_definition"]["height"]
        cols = self["grid_definition"]["width"]
        return super(GriddedProduct, self).copy_array(item, rows, cols, dtype, filename, read_only)


class SwathScene(BaseScene):
    """Container for `SwathProduct` objects.

    Products in a `SwathScene` use latitude and longitude coordinates to define their pixel locations. These pixels
    are typically not on a uniform grid. Products in a `SwathScene` are observed at the same times and over the
    same geographic area, but may be measured or displayed at varying resolutions. The common use case for a
    `SwathScene` is for swaths extracted from satellite imagery files.

    .. note::

        When stored on disk as a JSON file, a `SwathScene's` values may be filenames of a saved `SwathProduct` object.

    .. seealso::

        `GriddedScene`: Scene object for gridded products.

    """
    child_object_types = {
        None: SwathProduct,
    }

    def get_data_filepaths(self, product_names=None, data_key=None):
        """Generator of filepaths for each product provided or all products by default.
        """
        product_names = product_names if product_names is not None else self.keys()
        data_key = data_key if data_key is not None else self.values()[0].cleanup_kwargs[0]
        for pname in product_names:
            fp = self[pname][data_key]
            if not isinstance(fp, (str, unicode)):
                LOG.warning("Non-string filepath being provided from product")
            yield fp


class GriddedScene(BaseScene):
    """Container for `GriddedProduct` objects.

    Products in a `GriddedScene` are mapped to a uniform grid specified by a projection, grid size, grid origin,
    and pixel size. All products in a `GriddedScene` should use the same grid.

    .. note::

        When stored on disk as a JSON file, a `GriddedScene's` values may be filenames of a saved `GriddedProduct`
        object.

    .. seealso::

        `SwathScene`: Scene object for geographic longitude/latitude products.

    """
    child_object_types = {
        None: GriddedProduct,
    }



def remove_json(json_filename, binary_only=False):
    obj = BaseP2GObject.load(json_filename)
    if not binary_only:
        for json_key in obj.loadable_kwargs:
            if isinstance(obj[json_key], (str, unicode)):
                remove_json(obj[json_key], binary_only=False)
        LOG.info("Deleting JSON file '%s'", json_filename)
        os.remove(json_filename)

    obj.set_persist(False)
    del obj
    return


def info_json(json_filename):
    obj = BaseP2GObject.load(json_filename)
    if isinstance(obj, BaseScene):
        print("Polar2Grid %s Scene" % ("Gridded" if isinstance(obj, GriddedScene) else "Swath",))
        print("Contains the following products:\n\t" + "\n\t".join(obj.keys()))
    elif isinstance(obj, BaseProduct):
        print("Polar2Grid %s Product: %s" % ("Gridded" if isinstance(obj, GriddedProduct) else "Swath", obj["product_name"]))
    elif isinstance(obj, GridDefinition):
        print("%s Grid Definition" % (obj["grid_name"],))
        print("PROJ.4 Definition: %s" % (obj["proj4_definition"],))
        print("Width: %d" % (obj["width"],))
        print("Height: %d" % (obj["height"],))
        print("Cell Width: %f" % (obj["cell_width"],))
        print("Cell Height: %f" % (obj["cell_eight"],))
        print("Origin X: %f" % (obj["origin_x"],))
        print("Origin Y: %f" % (obj["origin_y"],))
    elif isinstance(obj, SwathDefinition):
        print("Swath Definition (%s)" % (obj["swath_name"],))
        print("Number of Rows: %f" % (obj["swath_rows"],))
        print("Number of Columns: %f" % (obj["swath_columns"],))
    else:
        print("ERROR: Unknown object from file '%s'" % (json_filename,))


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Utility for working with Polar2Grid metadata objects on disk")
    subparsers = parser.add_subparsers()
    sp_remove = subparsers.add_parser("remove", help="Remove a P2G JSON file and associate files")
    sp_remove.set_defaults(func=remove_json)
    sp_remove.add_argument("-b", dest="binary_only", action="store_true",
                           help="Only remove binary files associated with the JSON files")
    sp_remove.add_argument("json_filename", help="JSON file to recursively remove")

    sp_info = subparsers.add_parser("info", help="List information about the provided P2G JSON file")
    sp_info.set_defaults(func=info_json)
    sp_info.add_argument("json_filename", help="JSON file to recursively remove")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    kwargs = vars(args)
    func = kwargs.pop("func")
    func(**kwargs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
