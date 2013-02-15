#!/usr/bin/env python
# encoding: utf-8
"""Utilities and accessor functions to grids and projections used in
polar2grid.

Note: The term 'fit grid' corresponds to any grid that doesn't have all of
its parameters specified in the grid configuration.  Meaning it is likely used
to make a grid that "fits" the data.

:author:       David Hoese (davidh)
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

from polar2grid.core.constants import GRIDS_ANY,GRIDS_ANY_GPD,GRIDS_ANY_PROJ4,GRID_KIND_PROJ4,GRID_KIND_GPD
from polar2grid.core import Workspace,roles
from shapely import geometry
import pyproj
import numpy

import os
import sys
import logging

try:
    # try getting setuptools/distribute's version of resource retrieval first
    import pkg_resources
    get_resource_string = pkg_resources.resource_string
except ImportError:
    import pkgutil
    get_resource_string = pkgutil.get_data

log = logging.getLogger(__name__)

script_dir = os.path.split(os.path.realpath(__file__))[0]
GRIDS_DIR = script_dir #os.path.split(script_dir)[0] # grids directory is in root pkg dir
GRIDS_CONFIG_FILEPATH   = os.environ.get("POLAR2GRID_GRIDS_CONFIG", "grids.conf")
GRID_COVERAGE_THRESHOLD = float(os.environ.get("POLAR2GRID_GRID_COVERAGE", "0.1")) # 10%

### GPD Reading Functions ###
def clean_string(s):
    s = s.replace("-", "")
    s = s.replace("(", "")
    s = s.replace(")", "")
    s = s.replace(" ", "")
    s = s.upper()
    return s

def remove_comments(s, comment=";"):
    s = s.strip()
    c_idx = s.find(comment)
    if c_idx != -1:
        return s[:c_idx].strip()
    return s

gpd_conv_funcs = {
        # gpd file stuff:
        "GRIDWIDTH" : int,
        "GRIDHEIGHT" : int,
        "GRIDMAPUNITSPERCELL" : float,
        "GRIDCELLSPERMAPUNIT" : float,
        # mpp file stuff:
        "MAPPROJECTION" : clean_string,
        "MAPREFERENCELATITUDE" : float,
        "MAPSECONDREFERENCELATITUDE" : float,
        "MAPREFERENCELONGITUDE" : float,
        "MAPEQUATORIALRADIUS" : float,
        "MAPPOLARRADIUS" : float,
        "MAPORIGINLATITUDE" : float,
        "MAPORIGINLONGITUDE" : float,
        "MAPECCENTRICITY" : float,
        "MAPECCENTRICITYSQUARED" : float,
        "MAPFALSEEASTING" : float,
        "MAPSCALE" : float
        }

gpd_key_alias = {
        "GRIDWIDTH"     : "grid_width",
        "GRIDHEIGHT"    : "grid_height",
        }

def parse_gpd_str(gpd_file_str):
    gpd_dict = {}
    lines = gpd_file_str.split("\n")
    for line in lines:
        if not line: continue

        line_parts = line.split(":")
        if len(line_parts) != 2:
            log.error("Incorrect gpd syntax: more than one ':' ('%s')" % line)
            continue

        key = clean_string(line_parts[0])
        val = remove_comments(line_parts[1])

        if key not in gpd_conv_funcs:
            log.error("Can't parse gpd file, don't know how to handle key '%s'" % key)
            raise ValueError("Can't parse gpd file, don't know how to handle key '%s'" % key)
        conv_func = gpd_conv_funcs[key]
        val = conv_func(val)

        if key in gpd_key_alias:
            gpd_dict[gpd_key_alias[key]] = val
        else:
            gpd_dict[key] = val
    return gpd_dict

def parse_gpd_file(gpd_filepath):
    full_gpd_filepath = os.path.realpath(os.path.expanduser(gpd_filepath))
    if not os.path.exists(full_gpd_filepath):
        try:
            gpd_str = get_resource_string(__name__, gpd_filepath)
        except StandardError:
            log.error("GPD file '%s' does not exist" % (gpd_filepath,))
            raise ValueError("GPD file '%s' does not exist" % (gpd_filepath,))
    else:
        gpd_str = open(full_gpd_filepath, 'r').read()

    try:
        gpd_dict = parse_gpd_str(gpd_str)
    except StandardError:
        log.error("GPD file '%s' could not be parsed." % (gpd_filepath,))
        raise

    return gpd_dict

### End of GPD Reading Functions ###

### Configuration file functions ###

def _load_proj_string(proj_str):
    """Wrapper to accept epsg strings or proj4 strings
    """
    if proj_str[:4].lower() == "epsg":
        return pyproj.Proj(init=proj_str)
    else:
        return pyproj.Proj(proj_str)

def parse_gpd_config_line(grid_name, parts):
    """Return a dictionary of information for a specific GPD grid from
    a grid configuration line. ``parts`` should be every comma-separated
    part of the line including the ``grid_name``.
    """
    info = {}

    gpd_filepath = parts[2]
    if not os.path.isabs(gpd_filepath):
        # Its not an absolute path so it must be in the grids dir
        gpd_filepath = os.path.join(GRIDS_DIR, gpd_filepath)
    info["grid_kind"] = GRID_KIND_GPD
    info["static"]    = True
    info["gpd_filepath"] = gpd_filepath

    # Get corners
    corner_order = ["ul_corner", "ur_corner", "lr_corner", "ll_corner"]
    for corner,(lon,lat) in zip(corner_order, zip(parts[3::2], parts[4::2])):
        lon = float(lon)
        lat = float(lat)
        if lon > 180 or lon < -180:
            msg = "Corner longitudes must be between -180 and 180, not '%f'" % (lon,)
            log.error(msg)
            raise ValueError(msg)
        if lat > 90 or lat < -90:
            msg = "Corner latitude must be between -90 and 90, not '%f'" % (lat,)
            log.error(msg)
            raise ValueError(msg)

        info[corner] = (lon,lat)

    # Read the file and get information about the grid
    gpd_dict = parse_gpd_file(gpd_filepath)
    info.update(**gpd_dict)

    return info

def parse_proj4_config_line(grid_name, parts):
    """Return a dictionary of information for a specific PROJ.4 grid from
    a grid configuration line. ``parts`` should be every comma-separated
    part of the line including the ``grid_name``.
    """
    info = {}

    proj4_str = parts[2]
    # Test to make sure the proj4_str is valid in pyproj's eyes
    try:
        p = _load_proj_string(proj4_str)
        del p
    except StandardError:
        log.error("Invalid proj4 string in '%s' : '%s'" % (grid_name,proj4_str))
        raise

    # Some parts can be None, but not all
    try:
        static = True
        if parts[3] == "None" or parts[3] == '':
            static        = False
            grid_width    = None
        else:
            grid_width    = int(parts[3])

        if parts[4] == "None" or parts[4] == '':
            static        = False
            grid_height   = None
        else:
            grid_height   = int(parts[4])

        if parts[5] == "None" or parts[5] == '':
            static        = False
            pixel_size_x  = None
        else:
            pixel_size_x  = float(parts[5])

        if parts[6] == "None" or parts[6] == '':
            static        = False
            pixel_size_y  = None
        else:
            pixel_size_y  = float(parts[6])

        if parts[7] == "None" or parts[7] == '':
            static        = False
            grid_origin_x = None
        else:
            grid_origin_x = float(parts[7])

        if parts[8] == "None" or parts[8] == '':
            static        = False
            grid_origin_y = None
        else:
            grid_origin_y = float(parts[8])
    except StandardError:
        log.error("Could not parse proj4 grid configuration: '%s'" % (grid_name,))
        raise

    if (pixel_size_x is None and pixel_size_y is not None) or \
            (pixel_size_x is not None and pixel_size_y is None):
        log.error("Both or neither pixel sizes must be specified for '%s'" % grid_name)
        raise ValueError("Both or neither pixel sizes must be specified for '%s'" % grid_name)
    if (grid_width is None and grid_height is not None) or \
            (grid_width is not None and grid_height is None):
        log.error("Both or neither grid sizes must be specified for '%s'" % grid_name)
        raise ValueError("Both or neither grid sizes must be specified for '%s'" % grid_name)
    if (grid_origin_x is None and grid_origin_y is not None) or \
            (grid_origin_x is not None and grid_origin_y is None):
        log.error("Both or neither grid origins must be specified for '%s'" % grid_name)
        raise ValueError("Both or neither grid origins must be specified for '%s'" % grid_name)
    if grid_width is None and pixel_size_x is None:
        log.error("Either grid size or pixel size must be specified for '%s'" % grid_name)
        raise ValueError("Either grid size or pixel size must be specified for '%s'" % grid_name)

    info["grid_kind"]         = GRID_KIND_PROJ4
    info["static"]            = static
    info["proj4_str"]         = proj4_str
    info["pixel_size_x"]      = pixel_size_x
    info["pixel_size_y"]      = pixel_size_y
    info["grid_origin_x"]     = grid_origin_x
    info["grid_origin_y"]     = grid_origin_y
    info["grid_width"]        = grid_width
    info["grid_height"]       = grid_height

    return info

def read_grids_config_str(config_str):
    grid_information = {}

    for line in config_str.split("\n"):
        # Skip comments and empty lines
        if not line or line.startswith("#") or line.startswith("\n"): continue

        # Clean up the configuration line
        line = line.strip("\n,")
        parts = [ part.strip() for part in line.split(",") ]

        if len(parts) != 11 and len(parts) != 9:
            log.error("Grid configuration line '%s' in grid config does not have the correct format" % (line,))
            raise ValueError("Grid configuration line '%s' in grid config does not have the correct format" % (line,))

        grid_name = parts[0]
        if grid_name in grid_information:
            log.error("Grid '%s' is in grid config more than once" % (grid_name,))
            raise ValueError("Grid '%s' is in grid config more than once" % (grid_name,))

        grid_type = parts[1].lower()
        if grid_type == "gpd":
            grid_information[grid_name] = parse_gpd_config_line(grid_name, parts)
        elif grid_type == "proj4":
            grid_information[grid_name] = parse_proj4_config_line(grid_name, parts)
        else:
            log.error("Unknown grid type '%s' for grid '%s' in grid config" % (grid_type,grid_name))
            raise ValueError("Unknown grid type '%s' for grid '%s' in grid config" % (grid_type,grid_name))

    return grid_information

def determine_grid_coverage(g_ring, grids, cart, coverage_percent_threshold=GRID_COVERAGE_THRESHOLD):
    """Take a g_ring (polygon vertices of the data) and a list of grids and
    determine if the data covers any of those grids enough to be "useful".

    The percentage considered useful and the grids shape is contained in
    "grid_shapes.conf".

    `grids` can either be a list of grid names held in the "grids.conf" file,
    that must also be in the "grid_shapes.conf" file, or it can be one of a
    set of constants `GRIDS_ANY`, `GRIDS_ANY_GPD`, `GRIDS_ANY_PROJ4`.

    .. warning::

        This will not work with grids or data covering the poles.

    """
    # Interpret constants
    # Make sure to remove the constant from the list of valid grids
    if grids == GRIDS_ANY or GRIDS_ANY in grids:
        grids = list(set(grids + cart.get_all_grid_names(static=True)))
        grids.remove(GRIDS_ANY)
    if grids == GRIDS_ANY_PROJ4 or GRIDS_ANY_PROJ4 in grids:
        grids = list(set(grids + cart.get_kind_grid_names(GRID_KIND_PROJ4, static=True)))
        grids.remove(GRIDS_ANY_PROJ4)
    if grids == GRIDS_ANY_GPD or GRIDS_ANY_GPD in grids:
        grids = list(set(grids + cart.get_kind_grid_names(GRID_KIND_GPD, static=True)))
        grids.remove(GRIDS_ANY_GPD)

    def _correct_g_ring(g_ring, correct_dateline=False):
        # FUTURE: Use PROJ4 grid space to get the bounding box/polygon ring
        # FIXME: This probably doesn't work for polar cases
        # We need to correct for if the polygon cross the dateline
        ring_array = numpy.array(g_ring)
        lat_array  = ring_array[:,1]
        lon_array  = ring_array[:,0]
        # we crossed the dateline if the difference is huge
        # if the dateline we are comparing this with crossed the dateline
        # then we need to go on the 0-360 range too
        # BUT don't correct if we cross the origin even if the previous
        # polygon did cross the dateline
        crosses_dateline = (lon_array.max() - lon_array.min() >= 180)
        crosses_origin   = ( ( -90 <= lon_array.min() < 0 ) and \
                ( 0 <= lon_array.max() < 90 ))
        if ( correct_dateline and not crosses_origin ) or crosses_dateline:
            # force this to true, so the caller knows it was corrected
            crosses_dateline = True
            lon_array[lon_array < 0] += 360.0

        return zip(lon_array, lat_array),crosses_dateline

    # Look through each grid to see the data coverage
    useful_grids = []
    g_ring,crosses_dateline = _correct_g_ring(g_ring)
    data_poly = geometry.Polygon(g_ring)
    for grid_name in grids:
        grid_info = cart.get_grid_info(grid_name, with_corners=True)
        # We don't include dynamic grids this way
        if not grid_info["static"]: continue

        grid_g_ring,grid_crosses_dateline = _correct_g_ring( (
            grid_info["ul_corner"],
            grid_info["ur_corner"],
            grid_info["lr_corner"],
            grid_info["ll_corner"],
            grid_info["ul_corner"]
            ), correct_dateline=crosses_dateline )
        grid_poly = geometry.Polygon( grid_g_ring )

        if grid_crosses_dateline and not crosses_dateline:
            # We need to do the data polygon again because
            # it is in the -180-180 domain instead of 0-360
            # like the grid
            tmp_data_poly = geometry.Polygon( _correct_g_ring(g_ring, correct_dateline=True)[0] )
            intersect_poly = grid_poly.intersection(tmp_data_poly)
        else:
            intersect_poly = grid_poly.intersection(data_poly)
        percent_of_grid_covered = intersect_poly.area / grid_poly.area
        log.debug("Data had a %f%% coverage in grid %s" % (percent_of_grid_covered * 100, grid_name))
        if percent_of_grid_covered >= coverage_percent_threshold:
            useful_grids.append(grid_name)
    return useful_grids

def determine_grid_coverage_bbox(bbox, grids, cart):
    # We were given a bounding box so turn it into polygon coordinates
    g_ring = ( bbox[:2], (bbox[2],bbox[1]), bbox[2:], (bbox[0],bbox[3]), bbox[:2] )
    all_useful_grids = determine_grid_coverage(g_ring, grids, cart)
    return all_useful_grids

def determine_grid_coverage_fbf(fbf_lon, fbf_lat, grids, cart):
    lon_workspace,fbf_lon = os.path.split(os.path.realpath(fbf_lon))
    lat_workspace,fbf_lat = os.path.split(os.path.realpath(fbf_lat))
    W = Workspace(lon_workspace)
    lon_data = getattr(W, fbf_lon.split(".")[0])
    W = Workspace(lat_workspace)
    lat_data = getattr(W, fbf_lat.split(".")[0])
    del W

    south_lat,north_lat = lat_data.min(),lat_data.max()
    west_lon,east_lon   = lon_data.min(),lon_data.max()
    # Correct for dateline, if the difference is less than 1 degree we
    # know that we crossed the dateline
    if west_lon <= -179.0 and east_lon >= 179.0:
        west_lon,east_lon = lon_data[ lon_data > 0 ].min(),lon_data[ lon_data < 0 ].max()

    bbox = (west_lon, north_lat, east_lon, south_lat)
    return determine_grid_coverage_bbox(bbox, grids, cart)

def create_grid_jobs(sat, instrument, bands, backend, cart,
        forced_grids=None, fbf_lat=None, fbf_lon=None,
        bbox=None, g_ring=None):
    """Create a dictionary known as `grid_jobs` to be passed to remapping.
    """

    # Check what grids the backend can handle
    all_possible_grids = set()
    for band_kind, band_id in bands.keys():
        this_band_can_handle = backend.can_handle_inputs(sat, instrument, band_kind, band_id, bands[(band_kind, band_id)]["data_kind"])
        bands[(band_kind, band_id)]["grids"] = this_band_can_handle
        if isinstance(this_band_can_handle, str):
            all_possible_grids.update([this_band_can_handle])
        else:
            all_possible_grids.update(this_band_can_handle)
        log.debug("Kind %s Band %s can handle these grids: '%r'" % (band_kind, band_id, this_band_can_handle))

    # Get the set of grids we will use
    do_grid_deter = False
    grids = []
    all_useful_grids = []
    if None in forced_grids or forced_grids is None:
        # The user wants grid determination
        do_grid_deter = True
        if None in forced_grids: forced_grids.remove(None)

    if forced_grids is not None:
        if isinstance(forced_grids, list): grids = forced_grids
        else: grids = [forced_grids]
    if do_grid_deter:
        # Check if the data fits in the grids
        if g_ring is not None:
            all_useful_grids = determine_grid_coverage(g_ring, list(all_possible_grids), cart)
        elif bbox is not None:
            all_useful_grids = determine_grid_coverage_bbox(bbox, list(all_possible_grids), cart)
        elif fbf_lat is not None and fbf_lon is not None:
            all_useful_grids = determine_grid_coverage_fbf(fbf_lon, fbf_lat, list(all_possible_grids), cart)
        else:
            msg = "Grid determination requires a g_ring, a bounding box, or latitude and longitude binary files"
            log.error(msg)
            raise ValueError(msg)
    # Join any determined grids with any forced grids
    grids = set(all_useful_grids + grids)

    # Figure out which grids are useful for data coverage (or forced grids) and the backend can support
    grid_infos = dict((g,cart.get_grid_info(g)) for g in grids)# if g not in [GRIDS_ANY,GRIDS_ANY_GPD,GRIDS_ANY_PROJ4])
    for band_kind, band_id in bands.keys():
        if bands [(band_kind, band_id)]["grids"] == GRIDS_ANY:
            bands [(band_kind, band_id)]["grids"] = list(grids)
        elif bands[(band_kind, band_id)]["grids"] == GRIDS_ANY_PROJ4:
            bands [(band_kind, band_id)]["grids"] = [ g for g in grids if grid_infos[g]["grid_kind"] == GRID_KIND_PROJ4 ]
        elif bands[(band_kind, band_id)]["grids"] == GRIDS_ANY_GPD:
            bands [(band_kind, band_id)]["grids"] = [ g for g in grids if grid_infos[g]["grid_kind"] == GRID_KIND_GPD ]
        elif len(bands[(band_kind, band_id)]["grids"]) == 0:
            log.error("The backend does not support kind %s band %s, won't add to job list..." % (band_kind, band_id))
            # Handled in the next for loop via the inner for loop not adding anything
        else:
            bands[(band_kind, band_id)]["grids"] = grids.intersection(bands[(band_kind, band_id)]["grids"])
            bad_grids = grids - set(bands[(band_kind, band_id)]["grids"])
            if len(bad_grids) != 0 and forced_grids is not None:
                log.error("Backend does not know how to handle grids '%r'" % list(bad_grids))
                raise ValueError("Backend does not know how to handle grids '%r'" % list(bad_grids))

    # Create "grid" jobs to be run through remapping
    # Jobs are per grid per band
    grid_jobs = {}
    for band_kind, band_id in bands.keys():
        for grid_name in bands[(band_kind, band_id)]["grids"]:
            if grid_name not in grid_jobs: grid_jobs[grid_name] = {}
            if (band_kind, band_id) not in grid_jobs[grid_name]: grid_jobs[grid_name][(band_kind, band_id)] = {}
            log.debug("Kind %s band %s will be remapped to grid %s" % (band_kind, band_id, grid_name))
            grid_jobs[grid_name][(band_kind, band_id)] = bands[(band_kind, band_id)].copy()
            grid_jobs[grid_name][(band_kind, band_id)]["grid_info"] = cart.get_grid_info(grid_name)

    if len(grid_jobs) == 0:
        msg = "No backend compatible grids were found to fit the data set"
        log.error(msg)
        raise ValueError(msg)

    return grid_jobs

class Cartographer(roles.CartographerRole):
    """Object that holds grid information about the grids added
    to it. This Cartographer can handle PROJ4 and GPD grids.
    """

    grid_information = {}

    def __init__(self, *grid_configs, **kwargs):
        if len(grid_configs) == 0:
            log.info("Using default grid configuration: '%s' " % (GRIDS_CONFIG_FILEPATH,))
            grid_configs = (GRIDS_CONFIG_FILEPATH,)

        for grid_config in grid_configs:
            log.info("Loading grid configuration '%s'" % (grid_config,))
            self.add_grid_config(grid_config)

    def add_grid_config(self, grid_config_filename):
        """Load a grid configuration file. If a ``grid_name`` was already
        added its information is overwritten.
        """
        grid_information  = self.read_grids_config(grid_config_filename)
        self.grid_information.update(**grid_information)

    def add_grid_config_str(self, grid_config_line):
        grid_information = read_grids_config_str(grid_config_line)
        self.grid_information.update(**grid_information)

    def add_gpd_grid_info(self, grid_name, gpd_filename,
            ul_lon, ul_lat,
            ur_lon, ur_lat,
            lr_lon, lr_lat,
            ll_lon, ll_lat
            ):
        # Trick the parse function to think this came from a config line
        parts = (
                grid_name, "gpd", gpd_filename,
                ul_lon, ul_lat,
                ur_lon, ur_lat,
                lr_lon, lr_lat,
                ll_lon, ll_lat
                )
        self.grid_information[grid_name] = parse_gpd_config_line(grid_name, parts)

    def add_proj4_grid_info(self, grid_name,
            proj4_str, width, height,
            pixel_size_x, pixel_size_y,
            origin_x, origin_y
            ):
        # Trick the parse function to think this came from a config line
        parts = (
                grid_name, "proj4", proj4_str,
                width, height,
                pixel_size_x, pixel_size_y,
                origin_x, origin_y
                )
        self.grid_information[grid_name] = parse_proj4_config_line(grid_name, parts)

    def get_all_grid_info(self):
        # We need to make sure we copy the entire thing so the user can't
        # change things
        ret_ginfo = { grid_name : info.copy()
                for grid_name,info in self.grid_information.items() }
        return ret_ginfo

    def get_static_grid_info(self):
        ret_ginfo = { grid_name : info.copy()
                for grid_name,info in self.grid_information.items() if info["static"] }
        return ret_ginfo

    def get_dynamic_grid_info(self):
        ret_ginfo = { grid_name : info.copy()
                for grid_name,info in self.grid_information.items() if not info["static"] }
        return ret_ginfo

    def get_kind_grid_info(self, grid_kind):
        return { x : info.copy()
                for x,info in self.grid_information.items() if info["grid_kind"] == grid_kind }

    def get_all_grid_names(self, static=False):
        return [ k for k in self.grid_information.keys() if not static or self.grid_information[k]["static"] ]

    def get_kind_grid_names(self, grid_kind, static=False):
        return [ x for x,info in self.grid_information.items() if info["grid_kind"] == grid_kind and (not static or self.grid_information[x]["static"]) ]

    def calculate_grid_corners(self, grid_name):
        log.debug("Calculating corners for '%s'" % (grid_name,))
        grid_info = self.grid_information[grid_name]
        if grid_info["grid_kind"] != GRID_KIND_PROJ4:
            msg = "Don't know how to calculate corners for '%s' of kind '%s'" % (grid_name,grid_info["grid_kind"])
            log.error(msg)
            raise ValueError(msg)

        if not grid_info["static"]:
            log.debug("Won't calculate corners for a dynamic grid: '%s'" % (grid_name,))

        p = pyproj.Proj(grid_info["proj4_str"])
        right_x  = grid_info["grid_origin_x"] + grid_info["pixel_size_x"] * grid_info["grid_width"]
        bottom_y = grid_info["grid_origin_y"] + grid_info["pixel_size_y"] * grid_info["grid_height"]
        grid_info["ul_corner"] = p(grid_info["grid_origin_x"], grid_info["grid_origin_y"], inverse=True)
        grid_info["ur_corner"] = p(right_x, grid_info["grid_origin_y"], inverse=True)
        grid_info["lr_corner"] = p(right_x, bottom_y, inverse=True)
        grid_info["ll_corner"] = p(grid_info["grid_origin_x"], bottom_y, inverse=True)

    def get_grid_info(self, grid_name, with_corners=False):
        """Return a grid information dictionary about the ``grid_name``
        specified. If the ``with_corners`` keyword is specified and the
        corners have not already been calculated they will be calculated
        and stored in the information as (lon,lat) tuples with keys
        ``ul_corner``, ``ur_corner``, ``ll_corner``, and ``lr_corner``.

        The information returned will always be a copy of the information
        stored internally in this object. So a change to the dictionary
        returned does NOT affect the internal information.

        :raises ValueError: if ``grid_name`` does not exist

        """
        if grid_name in self.grid_information:
            if with_corners:
                if "ul_corner" not in self.grid_information[grid_name]:
                    # The grid doesn't have the corners calculated yet
                    self.calculate_grid_corners(grid_name)
            return self.grid_information[grid_name].copy()
        else:
            log.error("Unknown grid '%s'" % (grid_name,))
            raise ValueError("Unknown grid '%s'" % (grid_name,))

    def remove_grid(self, grid_name):
        """Remove ``grid_name`` from the loaded grid information
        for this object.

        :raises ValueError: if ``grid_name`` does not exist
        """
        if grid_name in self.grid_information:
            del self.grid_information[grid_name]
        else:
            log.error("Unknown grid '%s' can't be removed" % (grid_name,))
            raise ValueError("Unknown grid '%s' can't be removed" % (grid_name,))

    def remove_all(self):
        """Remove any loaded grid information from this instance.
        """
        self.grid_information = {}

    def read_grids_config(self, config_filepath):
        """Read the "grids.conf" file and create dictionaries mapping the
        grid name to the necessary information. There are two dictionaries
        created, one for gpd file grids and one for proj4 grids.

        Format for gpd grids:
        grid_name,gpd,gpd_filename

        where 'gpd' is the actual text 'gpd' to define the grid as a gpd grid.

        Format for proj4 grids:
        grid_name,proj4,proj4_str,pixel_size_x,pixel_size_y,origin_x,origin_y,width,height

        where 'proj4' is the actual text 'proj4' to define the grid as a proj4
        grid.

        """
        full_config_filepath = os.path.realpath(os.path.expanduser(config_filepath))
        if not os.path.exists(full_config_filepath):
            try:
                config_str = get_resource_string(__name__, config_filepath)
                return read_grids_config_str(config_str)
            except StandardError:
                log.error("Grids configuration file '%s' does not exist" % (config_filepath,))
                log.debug("Grid configuration error: ", exc_info=1)
                raise

        config_file = open(full_config_filepath, "r")
        config_str = config_file.read()
        return read_grids_config_str(config_str)

def main():
    from argparse import ArgumentParser
    from pprint import pprint
    description = """
Test configuration files and see how polar2grid will read them.
"""
    parser = ArgumentParser(description=description)
    parser.add_argument("--grids", dest="grids", default=GRIDS_CONFIG_FILEPATH,
            help="specify a grids configuration file to check")
    parser.add_argument("--determine", dest="determine", nargs="*",
            help="determine what grids the provided data fits in (<lon fbf>,<lat fbf>,<grid names>")
    args = parser.parse_args()

    print "Running log command"
    logging.basicConfig(level=logging.DEBUG)

    cartographer = Cartographer(args.grids)
    print "Grids from configuration file '%s':" % args.grids
    pprint(cartographer.grid_information)

    if args.determine is not None and len(args.determine) != 0:
        print "Determining if data fits in this grid"
        determine_grid_coverage_fbf(args.determine[0], args.determine[1], args.determine[2:], cartographer)

    print "DONE"

if __name__ == "__main__":
    sys.exit(main())

