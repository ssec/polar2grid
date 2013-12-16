#!/usr/bin/env python
# encoding: utf-8
"""
Read one or more contiguous in-order HDF5 VIIRS imager granules in any aggregation
Write out Swath binary files used by ms2gt tools.

:author:       David Hoese (davidh)
:author:       Ray Garcia (rayg)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3

Copyright (C) 2013 Space Science and Engineering Center (SSEC),
 University of Wisconsin-Madison.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

This file is part of the polar2grid software package. Polar2grid takes
satellite observation data, remaps it, and writes it to a file format for
input into another program.
Documentation: http://www.ssec.wisc.edu/software/polar2grid/

    Written by David Hoese    January 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

from .guidebook import *
from .io import VIIRSSDRMultiReader, VIIRSSDRGeoMultiReader
from polar2grid.core.time_utils import iso8601
from .prescale import run_dnb_scale
from .pseudo import create_fog_band
from polar2grid.core import roles
import numpy

import os
import sys
import logging
import re
import json
import importlib
from datetime import datetime
from collections import namedtuple

log = logging.getLogger(__name__)

FILL_VALUE = -999.0

# XXX: For now anything having to do directly with products is kept in the swath module
# XXX: Stuff about the actual files and what keys are what are kept in the guidebook
### PRODUCT KEYS ###
#   basic SDRs
PRODUCT_I01 = "i01"
PRODUCT_I02 = "i02"
PRODUCT_I03 = "i03"
PRODUCT_I04 = "i04"
PRODUCT_I05 = "i05"
PRODUCT_M01 = "m01"
PRODUCT_M02 = "m02"
PRODUCT_M03 = "m03"
PRODUCT_M04 = "m04"
PRODUCT_M05 = "m05"
PRODUCT_M06 = "m06"
PRODUCT_M07 = "m07"
PRODUCT_M08 = "m08"
PRODUCT_M09 = "m09"
PRODUCT_M10 = "m10"
PRODUCT_M11 = "m11"
PRODUCT_M12 = "m12"
PRODUCT_M13 = "m13"
PRODUCT_M14 = "m14"
PRODUCT_M15 = "m15"
PRODUCT_M16 = "m16"
PRODUCT_DNB = "dnb"
PRODUCT_IFOG = "ifog"
PRODUCT_DNB_SZA = "dnb_sza"
PRODUCT_HISTOGRAM_DNB = "histogram_dnb"
PRODUCT_ADAPTIVE_DNB = "adaptive_dnb"
#   adaptive IR
PRODUCT_ADAPTIVE_I04 = "adaptive_i04"
PRODUCT_ADAPTIVE_I05 = "adaptive_i05"
PRODUCT_ADAPTIVE_M12 = "adaptive_m12"
PRODUCT_ADAPTIVE_M13 = "adaptive_m13"
PRODUCT_ADAPTIVE_M14 = "adaptive_m14"
PRODUCT_ADAPTIVE_M15 = "adaptive_m15"
PRODUCT_ADAPTIVE_M16 = "adaptive_m16"
# if the below were their own products
#PRODUCT_CORRECTED_DNB = "corrected_dnb"
#PRODUCT_CORRECTED_ADAPTIVE_DNB = "corrected_adaptive_dnb"

# Geolocation "Products"
# These products aren't really products at the moment and should only be used as navigation for the above products
# XXX: These may need to be set as possible products for the CREFL frontend so that it can ask the frontend for
#      geolocation files.
PRODUCT_I_LAT = "i_latitude"
PRODUCT_I_LON = "i_longitude"
PRODUCT_M_LAT = "m_latitude"
PRODUCT_M_LON = "m_longitude"
PRODUCT_DNB_LAT = "dnb_latitude"
PRODUCT_DNB_LON = "dnb_longitude"

# All configuration information for a product goes in this named tuple
#NavigationTuple = namedtuple("NavigationTuple",
                             #['tc_file_pattern', 'nontc_file_pattern', 'longitude_product', 'latitude_product'])
NavigationTuple = namedtuple("NavigationTuple", ['scene_name', 'longitude_product', 'latitude_product'])
# XXX: Does 'cols_per_row' needed to be included?
ProductInfo = namedtuple("ProductInfo", ['dependencies', 'geolocation', 'rows_per_scan', 'data_kind', 'description'])

# dependencies: Product keys mapped to product dependencies
#   (the products needed to produce the specified product)
# geolocation: Products that define the navigation of the product
#   For VIIRS that means Longitude and Latitude
#   If navigation file pattern is None the h5 file will be searched for navigation
# shortcuts:
i_nav_tuple = NavigationTuple("i_nav", PRODUCT_I_LON, PRODUCT_I_LAT)
#i_nav_tuple = NavigationTuple(I_GEO_TC_REGEX, I_GEO_REGEX, PRODUCT_I_LON, PRODUCT_I_LAT)
m_nav_tuple = NavigationTuple("m_nav", PRODUCT_M_LON, PRODUCT_M_LAT)
#m_nav_tuple = NavigationTuple(M_GEO_TC_REGEX, M_GEO_REGEX, PRODUCT_M_LON, PRODUCT_M_LAT)
dnb_nav_tuple = NavigationTuple("dnb_nav", PRODUCT_DNB_LON, PRODUCT_DNB_LAT)
#dnb_nav_tuple = NavigationTuple(DNB_GEO_TC_REGEX, DNB_GEO_REGEX, PRODUCT_DNB_LON, PRODUCT_DNB_LAT)
PRODUCT_INFO = {
    PRODUCT_I01: ProductInfo(tuple(), i_nav_tuple, 32, "reflectance", ""),
    PRODUCT_I02: ProductInfo(tuple(), i_nav_tuple, 32, "reflectance", ""),
    PRODUCT_I03: ProductInfo(tuple(), i_nav_tuple, 32, "reflectance", ""),
    PRODUCT_I04: ProductInfo(tuple(), i_nav_tuple, 32, "btemp", ""),
    PRODUCT_I05: ProductInfo(tuple(), i_nav_tuple, 32, "btemp", ""),
    PRODUCT_M01: ProductInfo(tuple(), m_nav_tuple, 16, "reflectance", ""),
    PRODUCT_M02: ProductInfo(tuple(), m_nav_tuple, 16, "reflectance", ""),
    PRODUCT_M03: ProductInfo(tuple(), m_nav_tuple, 16, "reflectance", ""),
    PRODUCT_M04: ProductInfo(tuple(), m_nav_tuple, 16, "reflectance", ""),
    PRODUCT_M05: ProductInfo(tuple(), m_nav_tuple, 16, "reflectance", ""),
    PRODUCT_M06: ProductInfo(tuple(), m_nav_tuple, 16, "reflectance", ""),
    PRODUCT_M07: ProductInfo(tuple(), m_nav_tuple, 16, "reflectance", ""),
    PRODUCT_M08: ProductInfo(tuple(), m_nav_tuple, 16, "reflectance", ""),
    PRODUCT_M09: ProductInfo(tuple(), m_nav_tuple, 16, "reflectance", ""),
    PRODUCT_M10: ProductInfo(tuple(), m_nav_tuple, 16, "reflectance", ""),
    PRODUCT_M11: ProductInfo(tuple(), m_nav_tuple, 16, "reflectance", ""),
    PRODUCT_M12: ProductInfo(tuple(), m_nav_tuple, 16, "btemp", ""),
    PRODUCT_M13: ProductInfo(tuple(), m_nav_tuple, 16, "btemp", ""),
    PRODUCT_M14: ProductInfo(tuple(), m_nav_tuple, 16, "btemp", ""),
    PRODUCT_M15: ProductInfo(tuple(), m_nav_tuple, 16, "btemp", ""),
    PRODUCT_M16: ProductInfo(tuple(), m_nav_tuple, 16, "btemp", ""),
    PRODUCT_DNB: ProductInfo(tuple(), dnb_nav_tuple, 16, "radiance", ""),
    PRODUCT_IFOG: ProductInfo((PRODUCT_I05, PRODUCT_I04), i_nav_tuple, 32, "temperature_difference", ""),
    PRODUCT_HISTOGRAM_DNB: ProductInfo((PRODUCT_DNB,), i_nav_tuple, 32, "equalized_radiance", ""),
    PRODUCT_ADAPTIVE_DNB: ProductInfo((PRODUCT_DNB,), dnb_nav_tuple, 16, "equalized_radiance", ""),
    # adaptive IR
    PRODUCT_ADAPTIVE_I04: ProductInfo((PRODUCT_I04,), i_nav_tuple, 32, "equalized_btemp", ""),
    PRODUCT_ADAPTIVE_I05: ProductInfo((PRODUCT_I05,), i_nav_tuple, 32, "equalized_btemp", ""),
    PRODUCT_ADAPTIVE_M12: ProductInfo((PRODUCT_M12,), m_nav_tuple, 16, "equalized_btemp", ""),
    PRODUCT_ADAPTIVE_M13: ProductInfo((PRODUCT_M13,), m_nav_tuple, 16, "equalized_btemp", ""),
    PRODUCT_ADAPTIVE_M14: ProductInfo((PRODUCT_M14,), m_nav_tuple, 16, "equalized_btemp", ""),
    PRODUCT_ADAPTIVE_M15: ProductInfo((PRODUCT_M15,), m_nav_tuple, 16, "equalized_btemp", ""),
    PRODUCT_ADAPTIVE_M16: ProductInfo((PRODUCT_M16,), m_nav_tuple, 16, "equalized_btemp", ""),
    # Navigation (doing this here we can mimic normal products if people want them remapped for some reason)
    PRODUCT_I_LON: ProductInfo(tuple(), i_nav_tuple, 32, "longitude", ""),
    PRODUCT_I_LAT: ProductInfo(tuple(), i_nav_tuple, 32, "latitude", ""),
    PRODUCT_M_LON: ProductInfo(tuple(), m_nav_tuple, 16, "longitude", ""),
    PRODUCT_M_LAT: ProductInfo(tuple(), m_nav_tuple, 16, "latitude", ""),
    PRODUCT_DNB_LON: ProductInfo(tuple(), dnb_nav_tuple, 16, "longitude", ""),
    PRODUCT_DNB_LAT: ProductInfo(tuple(), dnb_nav_tuple, 16, "latitude", ""),
}

# What file regex do I need to get the 'raw' products
# We can generalize getting raw products from files, secondary/derived products have to be special cased
RawProductFileInfo = namedtuple("RawProductFileInfo", ["file_pattern", "variable"])
PRODUCT_FILE_REGEXES = {
    PRODUCT_I01: RawProductFileInfo(I01_REGEX, K_REFLECTANCE),
    PRODUCT_I02: RawProductFileInfo(I02_REGEX, K_REFLECTANCE),
    PRODUCT_I03: RawProductFileInfo(I03_REGEX, K_REFLECTANCE),
    PRODUCT_I04: RawProductFileInfo(I04_REGEX, K_BTEMP),
    PRODUCT_I05: RawProductFileInfo(I05_REGEX, K_BTEMP),
    PRODUCT_M01: RawProductFileInfo(M01_REGEX, K_REFLECTANCE),
    PRODUCT_M02: RawProductFileInfo(M02_REGEX, K_REFLECTANCE),
    PRODUCT_M03: RawProductFileInfo(M03_REGEX, K_REFLECTANCE),
    PRODUCT_M04: RawProductFileInfo(M04_REGEX, K_REFLECTANCE),
    PRODUCT_M05: RawProductFileInfo(M05_REGEX, K_REFLECTANCE),
    PRODUCT_M06: RawProductFileInfo(M06_REGEX, K_REFLECTANCE),
    PRODUCT_M07: RawProductFileInfo(M07_REGEX, K_REFLECTANCE),
    PRODUCT_M08: RawProductFileInfo(M08_REGEX, K_REFLECTANCE),
    PRODUCT_M09: RawProductFileInfo(M09_REGEX, K_REFLECTANCE),
    PRODUCT_M10: RawProductFileInfo(M10_REGEX, K_REFLECTANCE),
    PRODUCT_M11: RawProductFileInfo(M11_REGEX, K_REFLECTANCE),
    PRODUCT_M12: RawProductFileInfo(M12_REGEX, K_BTEMP),
    PRODUCT_M13: RawProductFileInfo(M13_REGEX, K_BTEMP),
    PRODUCT_M14: RawProductFileInfo(M14_REGEX, K_BTEMP),
    PRODUCT_M15: RawProductFileInfo(M15_REGEX, K_BTEMP),
    PRODUCT_M16: RawProductFileInfo(M16_REGEX, K_BTEMP),
    PRODUCT_DNB: RawProductFileInfo(DNB_REGEX, K_RADIANCE),
    # FIXME: How do I handle TC vs non-TC here:
    # FIXME: Major flaw is that the latitude and longitude are treated as separate products in the product_info when really they should be forced to be a pair
    # Geolocation products (products from a geolocation file) must be None for the VIIRS frontend because we could have
    # TC or non-TC
    PRODUCT_I_LON: RawProductFileInfo((I_GEO_TC_REGEX, I_GEO_REGEX), K_LONGITUDE),
    PRODUCT_I_LAT: RawProductFileInfo((I_GEO_TC_REGEX, I_GEO_REGEX), K_LATITUDE),
    PRODUCT_M_LON: RawProductFileInfo((M_GEO_TC_REGEX, M_GEO_REGEX), K_LONGITUDE),
    PRODUCT_M_LAT: RawProductFileInfo((M_GEO_TC_REGEX, M_GEO_REGEX), K_LATITUDE),
    PRODUCT_DNB_LON: RawProductFileInfo((DNB_GEO_TC_REGEX, DNB_GEO_REGEX), K_LONGITUDE),
    PRODUCT_DNB_LAT: RawProductFileInfo((DNB_GEO_TC_REGEX, DNB_GEO_REGEX), K_LATITUDE),
}


def get_product_dependencies(product_name):
    """Recursive function to get all dependencies to create a single product.

    :param product_name: Valid product name for this frontend

    >>> for k in PRODUCT_INFO.keys():
    ...     assert(isinstance(get_product_dependencies(k), set))
    >>> get_product_dependencies("blahdkjlwkjdoisdlfkjlk2j3lk4j")
    Traceback (most recent call last):
    ...
    ValueError: Unknown product was requested from frontend: 'blahdkjlwkjdoisdlfkjlk2j3lk4j'
    >>> PRODUCT_INFO["fake_dnb"] = ProductInfo((PRODUCT_ADAPTIVE_DNB, PRODUCT_DNB), dnb_nav_tuple)
    >>> assert(get_product_dependencies("fake_dnb") == set((PRODUCT_ADAPTIVE_DNB, PRODUCT_DNB)))
    """
    _dependencies = set()

    if product_name not in PRODUCT_INFO:
        log.error("Unknown product was requested from frontend: '%s'" % (product_name,))
        raise ValueError("Unknown product was requested from frontend: '%s'" % (product_name,))

    for dependency_product in PRODUCT_INFO[product_name].dependencies:
        log.info("Product Dependency: To create '%s', '%s' must be created first", product_name, dependency_product)
        _dependencies.update(get_product_dependencies(dependency_product))
        _dependencies.add(dependency_product)

    # Check if the product_name is already in the set, if it is then we have a circular dependency
    if product_name in _dependencies:
        log.error("Circular dependency found in frontend, '%s' requires itself", product_name)
        raise RuntimeError("Circular dependency found in frontend, '%s' requires itself", product_name)

    return _dependencies


### Secondary Product Functions
def create_adaptive_dnb():
    pass


def create_ifog(meta_data, files_loaded, nav_files_loaded, products_created, nav_products_created):
    pass


def _jsonclass_to_pyclass(json_class_name):
    cls_name = json_class_name.split(".")[-1]
    mod_name = ".".join(json_class_name.split(".")[:-1])
    cls = getattr(importlib.import_module(mod_name), cls_name)
    return cls


def open_p2g_object(json_obj):
    """Open a Polar2Grid object either from a filename or an already loaded dict.
    """
    if isinstance(json_obj, (str, unicode)):
        d = json.load(open(json_obj, "r"))
    else:
        d = json_obj

    if "__class__" not in d:
        log.error("Missing '__class__' key in JSON file")
        raise ValueError("Missing '__class__' key in JSON file")

    cls = _jsonclass_to_pyclass(d["__class__"])
    return cls.create_from_dict(d)


def remove_p2g_object(obj):
    """Recursively remove a Polar2Grid object from disk.

    By default objects persist once saved to disk. This function should be used to
    recursively remove them by filename or dict. Currently P2G objects can not be deleted via this function.
    """
    if isinstance(obj, (str, unicode)):
        json_dict = json.load(open(obj, "r"))
        fn = obj
    else:
        json_dict = obj
        fn = None

    # XXX: Would this look cleaner if we loaded the object and forced persist to 'False'?
    for k, v in json_dict.items():
        if k == "swath_data":
            try:
                log.info("Removing flat binary file: '%s'", v)
                os.remove(v)
            except StandardError:
                log.error("Could not remove: '%s'", v, exc_info=True)
        elif isinstance(v, dict):
            remove_p2g_object(v)

    if fn:
        try:
            log.info("Removing JSON on-disk file: '%s'", fn)
            os.remove(fn)
        except StandardError:
            log.error("Could not remove JSON file: '%s'", v, exc_info=True)


class BaseP2GObject(dict):
    def __init__(self, *args, **kwargs):
        super(BaseP2GObject, self).__init__(*args, **kwargs)
        self.persist = False

    @classmethod
    def create_from_dict(cls, d):
        # Remove the class name if it's still in the dict
        d.pop("__class__", None)
        # Can be overridden in subclasses if arguments are needed
        inst = cls()
        # If we are being created from a dictionary then we don't have the "right" to delete on-disk content
        inst.persist = True
        # Load extra data (including sub-elements) from the dictionary
        inst.load_from_dict(d)
        return inst

    def load_from_dict(self, d):
        for k, v in d.items():
            # Handle any special keys that need converting
            if isinstance(v, dict) and "__class__" in v:
                d[k] = open_p2g_object(v)
            elif isinstance(v, datetime):
                d[k] = iso8601(v)

        self.update(**d)

    @classmethod
    def _json_class_name(cls):
        """Get the polar2grid string name for this class.
        """
        return str(cls.__module__) + "." + str(cls.__name__)

    @classmethod
    def open(cls, filename):
        """Open a JSON file representing a Polar2Grid object.
        """
        d = json.load(open(filename, "r"))
        if "__class__" not in d:
            log.error("Missing '__class__' key in JSON file")
            raise ValueError("Missing '__class__' key in JSON file")

        json_class_name = d.pop("__class__")
        if json_class_name != cls._json_class_name():
            log.error("Incorrect class in JSON file. Got %s, expected %s" % (json_class_name, cls._json_class_name()))
            raise ValueError("Incorrect class in JSON file. Got %s, expected %s" % (json_class_name, cls._json_class_name()))

        inst = cls.create_from_dict(d)
        return inst

    def jsonify(self):
        """Create a JSON-serializable python dictionary.
        """
        # Make sure none of the on-disk information gets deleted on garbage collection
        self.persist = True

        d = self.copy()
        for k, v in d.items():
            # Handle any special keys that need converting
            if isinstance(v, dict) and hasattr(v, "jsonify"):
                d[k] = v.jsonify()
            elif isinstance(v, datetime):
                d[k] = v.isoformat()

        d["__class__"] = self._json_class_name()
        return d

    def save(self, filename):
        """Write the JSON representation of this class to a file.
        """
        # Get the JSON-able representation
        json_dict = self.jsonify()

        f = open(filename, "w")
        try:
            json.dump(json_dict, f, indent=4, sort_keys=True)
        except TypeError:
            log.error("Could not write P2G object to JSON file: '%s'", filename, exc_info=True)
            f.close()
            os.remove(filename)
            raise


class BaseMetaData(BaseP2GObject):
    pass


class BaseScene(BaseP2GObject):
    def __init__(self, geo_swath, **kwargs):
        super(BaseScene, self).__init__(**kwargs)
        self.geolocation = geo_swath

    def jsonify(self):
        self["geolocation"] = self.geolocation
        json_dict = super(BaseScene, self).jsonify()
        del self["geolocation"]
        return json_dict

    @classmethod
    def create_from_dict(cls, d):
        # Remove the class name if it's still in the dict
        d.pop("__class__", None)
        # Can be overridden in subclasses if arguments are needed
        geoloc_inst = open_p2g_object(d.pop("geolocation"))
        inst = cls(geoloc_inst)
        # If we are being created from a dictionary then we don't have the "right" to delete on-disk content
        inst.persist = True
        # Load extra data (including sub-elements) from the dictionary
        inst.load_from_dict(d)
        return inst


class BaseSwath(BaseP2GObject):
    def __del__(self):
        # Do we have swath data that is in an flat binary file
        if "swath_data" in self and isinstance(self["swath_data"], (str, unicode)):
            # Do we not want to delete this file because someone tried to save the state of this object
            if hasattr(self, "persist") and not self.persist:
                try:
                    log.info("Removing FBF that is no longer needed: '%s'", self["swath_data"])
                    os.remove(self["swath_data"])
                except StandardError:
                    log.warning("Unable to remove FBF: '%s'", self["swath_data"])
                    log.debug("Unable to remove FBF traceback:", exc_info=True)


class BaseGeoSwath(BaseSwath):
    def __init__(self, scene_name, longitude_swath, latitude_swath, **kwargs):
        """Base swath class for navigation products.

        :param scene_name: Scene name for the longitude and latitude swaths
        :param longitude_swath: Swath object for the longitude data
        :param latitude_swath: Swath object for the latitude data
        """
        super(BaseGeoSwath, self).__init__(**kwargs)
        self["scene_name"] = scene_name
        self["longitude"] = longitude_swath
        self["latitude"] = latitude_swath

    @classmethod
    def create_from_dict(cls, d):
        # Remove the class name if it's still in the dict
        d.pop("__class__", None)
        # Can be overridden in subclasses if arguments are needed
        lon_inst = open_p2g_object(d.pop("longitude"))
        lat_inst = open_p2g_object(d.pop("latitude"))
        inst = cls(d.pop("scene_name"), lon_inst, lat_inst)
        # If we are being created from a dictionary then we don't have the "right" to delete on-disk content
        inst.persist = True
        # Load extra data (including sub-elements) from the dictionary
        inst.load_from_dict(d)
        return inst


class VIIRSScene(BaseScene):
    """Collection of VIIRS Swaths.

    A Scene is defined as having one defining set of navigation and zero or more data swaths mapped to that navigation.
    """
    pass


class VIIRSDataSwath(BaseSwath):
    """Swath Data Class for VIIRS Data.

    Required Information:
        - product_name: Publically known name of the product this swath represents
        - filenames: Unordered list of source files that made up this product
        - satellite: Name of the satellite the data came from
        - instrument: Name of the instrument on the satellite from which the data was observed
        - data_kind (optional): Name for the type of the measurement (ex. btemp, reflectance, radiance, etc.)
        - scene_name: Name of the navigation "set" or scene to which this swath belongs.
        - swath_rows: Number of rows in the main 2D data array
        - swath_cols: Number of columns in the main 2D data array
        - start_time: Datetime object representing the best known start of observation for this product's data
        - end_time: Datetime object represnting the best known end of observation for this product's data
        - description (optional): Basic description of the product
        - rows_per_scan: Number of swath rows making up one scan of the sensor (1 if not applicable)
        - swath_scans: Number of scans in the main 2D data array (swath_rows / rows_per_scan)
        - swath_data: Flat binary filename or numpy array for the main data array

    This information should be set via the bracket/setitem dictionary method (ex. swath["product_name"] = "p1").
    It is up to the creator to fill in these fields at the most convenient time based on the source file structure.
    """
    pass


class VIIRSGeoSwath(BaseGeoSwath):
    """Swath data for VIIRS Geolocation Data.

    VIIRS Geolocation is defined as being a minimum of a longitude and latitude array.
    """
    pass


#class Frontend(roles.FrontendRole):
class Frontend(object):
    SECONDARY_PRODUCT_FUNCTIONS = {
        PRODUCT_ADAPTIVE_DNB: create_adaptive_dnb,
        PRODUCT_IFOG: create_ifog,
    }

    def __init__(self, search_paths=['.']):
        """Initialize the frontend.

        For each search path, check if it exists and that it is
        a directory. If it is not a valid search path it will be removed
        and a warning will be raised.

        The order of the search paths does not matter. Any duplicate
        directories in the search path will be removed. This frontend
        does *not* recursively search directories.

        :param search_paths: A list of paths to search for usable files
        """
        search_paths_set = set()
        for sp in search_paths:
            # Take the realpath because we don't want duplicates
            #   (two links that point to the same directory)
            sp_real = os.path.realpath(sp)
            if not os.path.isdir(sp_real):
                log.warning("Search path '%s' does not exist or is not a directory" % (sp_real,))
                continue
            search_paths_set.add(sp_real)

        # Check if we have any valid directories to look through
        if not search_paths_set:
            log.error("No valid paths were found to search for data files")
            raise ValueError("No valid paths were found to search for data files")

        self.search_paths = tuple(search_paths_set)
        file_paths = self.find_all_files(self.search_paths)

        # Find all files for each path
        self.recognized_files = self.filter_filenames(file_paths)

    def find_all_files(self, search_paths):
        for sp in search_paths:
            log.info("Searching '%s' for useful files...", sp)
            for fn in os.listdir(sp):
                full_path = os.path.join(sp, fn)
                if os.path.isfile(full_path):
                    # XXX: Is this check really worth the separation we end up having to do in `filter_filenames`
                    yield full_path

    def filter_filenames(self, filepaths):
        """Filter out unrecognized file patterns from a list of filepaths.

        Returns a dictionary mapping regular expressions to an
        unsorted list of absolute filepaths that were matched.

        Files are assumed to exist and be unique (path + filename). If the
        same filename is found in 2 different directories, both will be processed and
        will likely produce unexpected results in future processing.
        """
        matched_files = {}
        for filepath in filepaths:
            #log.debug("Checking file '%s' for usefulness...", filepath)
            fn = os.path.split(filepath)[1]
            for fn_regex in ALL_FILE_REGEXES:
                #log.debug("Checking '%s' '%s'", fn, fn_regex)
                # FIXME: There has to be a faster way to do this
                # FIXME: Besides filling in the dictionary and then looking for duplicates
                if re.match(fn_regex, fn) is not None:
                    # we found a match
                    log.debug("Found useful file: '%s'", fn)
                    if fn_regex not in matched_files:
                        # Add the regular expression to the dictionary
                        matched_files[fn_regex] = set()
                    matched_files[fn_regex].add(filepath)
                    break

        # Sort the filenames
        for fn_regex in matched_files.keys():
            matched_files[fn_regex] = sorted(matched_files[fn_regex], key=lambda f: os.path.split(f)[-1])

        return matched_files

    @classmethod
    def parse_datetimes_from_filepaths(cls, filepaths):
        """Return a list of datetimes for each filepath provided.

        This logic is duplicated from the guidebook because it has less
        overhead.
        """
        filenames = [os.path.split(fp)[-1] for fp in filepaths]

        # Clear out files we don't understand
        filenames = [fn for fn in filenames if fn.startswith("SV") and fn.endswith(".h5")]

        # SVI01_npp_d20120225_t1801245_e1802487_b01708_c20120226002130255476_noaa_ops.h5
        dt_list = [datetime.strptime(fn[10:27], "d%Y%m%d_t%H%M%S") for
                   fn in filenames]
        return dt_list

    @classmethod
    def sort_files_by_nav_uid(cls, filepaths):
        # Call the guidebook function
        return sort_files_by_nav_uid(filepaths)

    def _get_file_pattern(self, product_name):
        """Get the file pattern to load the specifed raw products data.
        """
        product_file_info = PRODUCT_FILE_REGEXES[product_name]
        file_pattern = product_file_info.file_pattern
        # Load the file objects
        if not isinstance(file_pattern, str):
            # There is more than one possible pattern
            for fp_tmp in file_pattern:
                if fp_tmp in self.recognized_files:
                    file_pattern = fp_tmp
                    break

        if file_pattern not in self.recognized_files:
            log.error("Could not find any files to create product '%s', looked through the following patterns: %r", product_name, file_pattern)
            log.debug("Recognized file patterns:\n%s", "\n\t".join(self.recognized_files.keys()))
            raise ValueError("Could not find any files to create product '%s', looked through the following patterns: %r" % (product_name, file_pattern))

        return file_pattern

    def _create_raw_swath_object(self, product_name, variable_key, reader):
        product_info = PRODUCT_INFO[product_name]
        one_swath = VIIRSDataSwath()
        log.info("Writing product data to FBF for '%s'", product_name)
        fbf_filename, fbf_shape = reader.write_var_to_flat_binary(variable_key, stem=product_name)
        one_swath["product_name"] = product_name
        one_swath["filenames"] = reader.get_filenames()
        one_swath["start_time"] = reader.start_time
        one_swath["end_time"] = reader.end_time
        one_swath["satellite"] = reader.get_satellite()
        one_swath["instrument"] = reader.get_instrument()
        one_swath["swath_data"] = fbf_filename
        one_swath["swath_rows"] = fbf_shape[0]
        one_swath["swath_cols"] = fbf_shape[1]
        one_swath["data_kind"] = product_info.data_kind
        one_swath["description"] = product_info.description
        one_swath["scene_name"] = product_info.geolocation.scene_name
        one_swath["rows_per_scan"] = product_info.rows_per_scan
        one_swath["swath_scans"] = one_swath["swath_rows"] / one_swath["rows_per_scan"]

        return one_swath

    def create_scenes(self, products=None, use_terrain_corrected=True):
        log.info("Loading scene data...")
        # FUTURE: products will be a keyword and when None the frontend will figure out what products it can create
        meta_data = BaseMetaData()
        # List of all products we will be creating (what was asked for and what's needed to create them)
        products_needed = set()
        raw_products_needed = set()
        secondary_products_needed = set()
        nav_products_needed = set()
        # Hold on to all of the file sets we've loaded
        files_loaded = {}
        # Hold on to all of the navigation files we've loaded
        nav_files_loaded = {}
        # Dictionary of all products created so far
        products_created = {}
        # Navigation products created
        nav_products_created = {}

        # Check what products they asked for and see what we need to be able to create them
        for product_name in products:
            log.debug("Searching for dependencies for '%s'", product_name)
            products_needed.update(get_product_dependencies(product_name))
            products_needed.add(product_name)

        # Go through each product we are going to have to create and figure out which raw ones need to be loaded
        for product_name in products_needed:
            product_info = PRODUCT_INFO[product_name]
            # Looked up the raw products we need
            if not product_info.dependencies:
                # if there are no dependencies then it's a raw product
                raw_products_needed.add(product_name)
            else:
                secondary_products_needed.add(product_name)

            # For each product look what navigation product it connects with
            nav_products_needed.add(product_info.geolocation.longitude_product)
            nav_products_needed.add(product_info.geolocation.latitude_product)

        # Load geolocation files
        for nav_product_name in nav_products_needed:
            product_file_info = PRODUCT_FILE_REGEXES[nav_product_name]
            nav_file_pattern = self._get_file_pattern(nav_product_name)
            log.debug("Using navigation file pattern '%s' for product '%s'", nav_file_pattern, nav_product_name)

            # Load navigation files
            if nav_file_pattern not in nav_files_loaded:
                reader = nav_files_loaded[nav_file_pattern] = VIIRSSDRGeoMultiReader(self.recognized_files[nav_file_pattern])
            else:
                reader = nav_files_loaded[nav_file_pattern]

            # Write the geolocation information to a file
            log.info("Writing navigation product data to FBF for '%s'", product_name)
            products_created[nav_product_name] = self._create_raw_swath_object(nav_product_name, product_file_info.variable, reader)

            # TODO Need to add nav products to the scene as normal products if they were requested that way

        # Load each of the raw products (products that are loaded directly from the file)
        for product_name in raw_products_needed:
            log.info("Opening data files to process: %s", product_name)
            product_info = PRODUCT_INFO[product_name]
            product_file_info = PRODUCT_FILE_REGEXES[product_name]

            file_pattern = self._get_file_pattern(product_name)
            log.debug("Using file pattern '%s' for product '%s'", file_pattern, file_pattern)

            if file_pattern not in files_loaded:
                reader = files_loaded[file_pattern] = VIIRSSDRMultiReader(self.recognized_files[file_pattern])
            else:
                reader = files_loaded[file_pattern]

            one_swath = products_created[product_name] = self._create_raw_swath_object(product_name, product_file_info.variable, reader)

            # Create a scene (if needed) and add the product to it
            if one_swath["scene_name"] not in meta_data:
                scene_name = one_swath["scene_name"]
                longitude_swath = products_created[product_info.geolocation.longitude_product]
                latitude_swath = products_created[product_info.geolocation.latitude_product]
                one_scene = meta_data[scene_name] = VIIRSScene(VIIRSGeoSwath(scene_name, longitude_swath, latitude_swath))
            else:
                one_scene = meta_data[scene_name]

            one_scene[product_name] = one_swath

        # Special cases (i.e. non-raw products that need further processing)
        # FUTURE: Move each of these into their own function
        # FIXME: Need to do these in a way that secondary products that depend on other secondary products
        #self.create_secondary_products(meta_data, files_loaded, nav_files_loaded, products_created, nav_products_created)
        # Create the IFOG product (I5 - I4)
        #i5_data
        # Get the other products we need
        # Do the math
        # Save this to a new FBF
        # TODO

        return meta_data


def main():
    from argparse import ArgumentParser

    description = """Parse VIIRS hdf5 files, extracting swath data and meta data"""
    parser = ArgumentParser(description=description)
    parser.add_argument('-t', '--test', dest="self_test",
                        action="store_true", default=False, help="run self-tests")
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
                        help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_argument('--show', dest="show_products", action="store_true",
                        help="List available products")
    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(3, args.verbosity)])

    if args.self_test:
        import doctest

        doctest.testmod()
        sys.exit(0)

    if args.show_products:
        print "VIIRS Frontend has the following possible products:"
        for k in sorted(PRODUCT_INFO.keys()):
            print "\t%s" % (k,)
        sys.exit(0)

    return 0


if __name__ == '__main__':
    sys.exit(main())
