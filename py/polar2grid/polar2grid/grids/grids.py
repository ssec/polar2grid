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
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

from polar2grid.core.constants import GRIDS_ANY,GRIDS_ANY_GPD,GRIDS_ANY_PROJ4,GRID_KIND_PROJ4,GRID_KIND_GPD
from polar2grid.core import Workspace
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
GRIDS_DIR = os.environ.get("POLAR2GRID_GRIDS_DIR", script_dir)
SHAPES_CONFIG_FILEPATH = os.environ.get("POLAR2GRID_SHAPES_CONFIG", "grid_shapes.conf")
GRIDS_CONFIG_FILEPATH = os.environ.get("POLAR2GRID_GRIDS_CONFIG", "grids.conf")

# Filled in later
SHAPES = None
GPD_GRIDS = None
PROJ4_GRIDS = None

def determine_grid_coverage(lon_data, lat_data, grids):
    """Take latitude and longitude arrays and a list of grids and determine
    if the data covers any of those grids enough to be "useful".

    The percentage considered useful and the grids shape is contained in
    "grid_shapes.conf".

    `grids` can either be a list of grid names held in the "grids.conf" file,
    that must also be in the "grid_shapes.conf" file, or it can be one of a
    set of constants `GRIDS_ANY`, `GRIDS_ANY_GPD`, `GRIDS_ANY_PROJ4`.
    """
    # Interpret constants
    # Make sure to remove the constant from the list of valid grids
    if grids == GRIDS_ANY or GRIDS_ANY in grids:
        grids = list(set(grids + GPD_GRIDS.keys() + PROJ4_GRIDS.keys()))
        grids.remove(GRIDS_ANY)
    if grids == GRIDS_ANY_PROJ4 or GRIDS_ANY_PROJ4 in grids:
        grids = list(set(grids + PROJ4_GRIDS.keys()))
        grids.remove(GRIDS_ANY_PROJ4)
    if grids == GRIDS_ANY_GPD or GRIDS_ANY_GPD in grids:
        grids = list(set(grids + GPD_GRIDS.keys()))
        grids.remove(GRIDS_ANY_GPD)

    # Flatten the data for easier operations
    lon_data = lon_data.flatten()
    lat_data = lat_data.flatten()

    # Look through each grid to see the data coverage
    useful_grids = []
    lon_data_flipped = None
    for grid_name in grids:
        # If the grid isn't in shapes, then it must be a fit grid
        if grid_name not in SHAPES:
            log.debug("Including fit grid '%s' in processing" % grid_name)
            useful_grids.append(grid_name)
            continue
        tbound,bbound,lbound,rbound,percent = SHAPES[grid_name]
        lon_data_use = lon_data
        if lbound > rbound:
            rbound = rbound + 360.0
            if lon_data_flipped is None:
                lon_data_flipped = lon_data.copy()
                lon_data_flipped[lon_data < 0] += 360
                lon_data_use = lon_data_flipped
        grid_mask = numpy.nonzero( (lat_data < tbound) & (lat_data > bbound) & (lon_data_use < rbound) & (lon_data_use > lbound) )[0]
        grid_percent = (len(grid_mask) / float(len(lat_data)))
        log.debug("Data had a %f coverage in grid %s" % (grid_percent,grid_name))
        if grid_percent >= percent:
            useful_grids.append(grid_name)
    return useful_grids

def determine_grid_coverage_fbf(fbf_lon, fbf_lat, grids):
    lon_workspace,fbf_lon = os.path.split(os.path.realpath(fbf_lon))
    lat_workspace,fbf_lat = os.path.split(os.path.realpath(fbf_lat))
    W = Workspace(lon_workspace)
    lon_data = getattr(W, fbf_lon.split(".")[0])
    W = Workspace(lat_workspace)
    lat_data = getattr(W, fbf_lat.split(".")[0])
    del W

    return determine_grid_coverage(lon_data, lat_data, grids)

def get_grid_info(grid_name):
    if grid_name in GPD_GRIDS:
        return GPD_GRIDS[grid_name].copy()
    elif grid_name in PROJ4_GRIDS:
        return PROJ4_GRIDS[grid_name].copy()
    else:
        log.error("Unknown grid '%s'" % (grid_name,))
        raise ValueError("Unknown grid '%s'" % (grid_name,))

def create_grid_jobs(sat, instrument, bands, fbf_lat, fbf_lon, backend,
        forced_grids=None):
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
    if forced_grids is not None:
        if isinstance(forced_grids, list): grids = forced_grids
        else: grids = [forced_grids]
        grids = set(grids)
    else:
        # Check if the data fits in the grids
        all_useful_grids = determine_grid_coverage_fbf(fbf_lon, fbf_lat, list(all_possible_grids))
        grids = set(all_useful_grids)

    # Figure out which grids are useful for data coverage (or forced grids) and the backend can support
    grid_infos = dict((g,get_grid_info(g)) for g in grids)# if g not in [GRIDS_ANY,GRIDS_ANY_GPD,GRIDS_ANY_PROJ4])
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

    if len(grid_jobs) == 0:
        msg = "No backend compatible grids were found to fit the data set"
        log.error(msg)
        raise ValueError(msg)

    return grid_jobs


# Projection tools
def from_proj4(proj4_str):
    proj4_elements = proj4_str.split(" ")
    proj4_dict = dict([ y.split("=") for y in [ x.strip("+") for x in proj4_elements ] ])
    return proj4_dict

def to_proj4(proj4_dict):
    """Convert a dictionary of proj4 parameters back into a proj4 string.

    >>> proj4_str = "+proj=lcc +a=123456 +b=12345"
    >>> proj4_dict = from_proj4(proj4_str)
    >>> new_proj4_str = to_proj4(proj4_dict)
    >>> assert(new_proj4_str == proj4_str)
    """
    # Make sure 'proj' is first, some proj4 parsers don't accept it otherwise
    proj4_str = "+proj=%s" % proj4_dict.pop("proj")
    proj4_str = proj4_str + " " + " ".join(["+%s=%s" % (k,str(v)) for k,v in proj4_dict.items()])
    return proj4_str

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

def parse_gpd_str(gpd_file_str):
    gpd_dict = {}
    lines = gpd_file_str.split("\n")
    for line in lines:
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
        gpd_dict[key] = val
    return gpd_dict

def parse_gpd(gpd_filepath):
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

gpd_proj_to_proj4 = {
        "ALBERSCONICEQUALAREA" : "aea",
        "AZIMUTHALEQUALAREA" : None,
        "AZIMUTHALEQUALAREAELLIPSOID" : None,
        "CYLINDRICALEQUALAREA" : "cea",
        "CYLINDRICALEQUALAREAELLIPSOID" : None,
        "CYLINDRICALEQUIDISTANT" : "eqc",
        "INTEGERIZEDSINUSOIDAL" : None,
        "INTERRUPTEDHOMOLOSINEEQUALAREA" : "igh",
        "LAMBERTCONICCONFORMALELLIPSOID" : "lcc",
        "MERCATOR" : "merc",
        "MOLLWEIDE" : "moll",
        "ORTHOGRAPHIC" : "ortho",
        "POLARSTEREOGRAPHIC" : "ups",
        "POLARSTEREOGRAPHICELLIPSOID" : "ups",
        "SINUSOIDAL" : None,
        "TRANSVERSEMERCATOR" : "tmerc",
        "TRANSVERSEMERCATORELLIPSOID" : None,
        "UNIVERSALTRANSVERSEMERCATOR" : "utm"
        }

gpd2proj4 = {
        # gpd file stuff:
        "GRIDWIDTH" : None,
        "GRIDHEIGHT" : None,
        "GRIDMAPUNITSPERCELL" : None,
        "GRIDCELLSPERMAPUNIT" : None,
        # mpp file stuff:
        "MAPPROJECTION" : "proj",
        "MAPREFERENCELATITUDE" : ["lat_0","lat_1"],
        "MAPSECONDREFERENCELATITUDE" : "lat_ts",
        "MAPREFERENCELONGITUDE" : "lon_0",
        "MAPEQUATORIALRADIUS" : "a",
        "MAPPOLARRADIUS" : "b",
        "MAPORIGINLATITUDE" : None,
        "MAPORIGINLONGITUDE" : None,
        "MAPECCENTRICITY" : "e",
        "MAPECCENTRICITYSQUARED" : "es",
        "MAPFALSEEASTING" : "x_0",
        "MAPSCALE" : None # ?
        }

def _gpd2proj4(gpd_dict):
    proj4_dict = {}
    for k,v in gpd_dict.items():
        if k not in gpd2proj4:
            log.error("Don't know how to convert gpd %s to proj.4" % k)
            raise ValueError("Don't know how to convert gpd %s to proj.4" % k)
        if k == "MAPPROJECTION":
            # Special case
            proj4_dict[gpd2proj4[k]] = gpd_proj_to_proj4[v]
            if proj4_dict[gpd2proj4[k]] is None:
                log.warning("Could not find equivalent proj4 projection name for %s" % v)
        elif k == "MAPREFERENCELATITUDE":
            pkey = gpd2proj4[k]
            pk1,pk2 = pkey
            proj4_dict[pk1] = v
            proj4_dict[pk2] = v
        else:
            pkey = gpd2proj4[k]
            if pkey is not None:
                proj4_dict[gpd2proj4[k]] = v

    return proj4_dict


def gpd_to_proj4(gpd_fn):
    gpd_file = open(gpd_fn, "r")
    gpd_dict = _parse_gpd(gpd_file)
    proj4_dict = _gpd2proj4(gpd_dict)
    return proj4_dict,gpd_dict

### Configuration file functions ###

def _load_proj_string(proj_str):
    """Wrapper to accept epsg strings or proj4 strings
    """
    if proj_str[:4].lower() == "epsg":
        return pyproj.Proj(init=proj_str)
    else:
        return pyproj.Proj(proj_str)

def read_shapes_config_str(config_str):
    # NEW RECORD: Most illegible list comprehensions
    shapes = dict(
            (parts[0],tuple([float(x) for x in parts[1:6]])) for parts in
                    [ [ part.strip() for part in line.split(",") ] for line in config_str.split("\n") if line and not line.startswith("#") ]
            )
    return shapes

def read_shapes_config(config_filepath):
    """Read the "grid_shapes.conf" file and create a dictionary mapping the
    grid name to the bounding box information held in the configuration file.
    """
    full_config_filepath = os.path.realpath(os.path.expanduser(config_filepath))
    if not os.path.exists(full_config_filepath):
        try:
            config_str = get_resource_string(__name__, config_filepath)
            return read_shapes_config_str(config_str)
        except StandardError:
            log.error("Shapes configuration file '%s' does not exist" % (config_filepath,))
            raise ValueError("Shapes configuration file '%s' does not exist" % (config_filepath,))

    config_str = open(full_config_filepath, 'r').read()
    return read_shapes_config_str(config_str)

def read_grids_config_str(config_str):
    gpd_grids = {}
    proj4_grids = {}

    for line in config_str.split("\n"):
        # Skip comments and empty lines
        if not line or line.startswith("#") or line.startswith("\n"): continue

        # Clean up the configuration line
        line = line.strip("\n,")
        parts = [ part.strip() for part in line.split(",") ]

        if len(parts) != 5 and len(parts) != 9:
            log.error("Grid configuration line '%s' in grid config does not have the correct format" % (line,))
            raise ValueError("Grid configuration line '%s' in grid config does not have the correct format" % (line,))

        grid_name = parts[0]
        if (grid_name in gpd_grids) or (grid_name in proj4_grids):
            log.error("Grid '%s' is in grid config more than once" % (grid_name,))
            raise ValueError("Grid '%s' is in grid config more than once" % (grid_name,))

        grid_type = parts[1].lower()
        if grid_type == "gpd":
            gpd_filepath = parts[2]
            if not os.path.isabs(gpd_filepath):
                # Its not an absolute path so it must be in the grids dir
                # XXX: This is only done because ll2cr requires an actual filepath
                gpd_filepath = os.path.join(GRIDS_DIR, gpd_filepath)
            gpd_grids[grid_name] = {}
            gpd_grids[grid_name]["grid_kind"] = GRID_KIND_GPD
            gpd_grids[grid_name]["gpd_filepath"] = gpd_filepath

            # Width,Height
            # This is an artifact of when we didn't read the actual file
            try:
                width = int(parts[3])
                gpd_grids[grid_name]["grid_width"] = width
                height = int(parts[4])
                gpd_grids[grid_name]["grid_height"] = height
            except StandardError:
                log.error("Could not convert gpd grid width and height: '%s'" % (line,))
                raise

            # Read the file and get information about the grid
            gpd_dict = parse_gpd(gpd_filepath)
            gpd_grids[grid_name].update(**gpd_dict)

        elif grid_type == "proj4":
            proj4_str = parts[2]
            # Test to make sure the proj4_str is valid in pyproj's eyes
            try:
                p = _load_proj_string(proj4_str)
                del p
            except StandardError:
                log.error("Invalid proj4 string in '%s'" % (line))
                raise

            # Some parts can be None, but not all
            try:
                if parts[3] == "None" or parts[3] == '': grid_width=None
                else: grid_width = int(parts[3])
                if parts[4] == "None" or parts[4] == '': grid_height=None
                else: grid_height = int(parts[4])
                if parts[5] == "None" or parts[5] == '': pixel_size_x=None
                else: pixel_size_x = float(parts[5])
                if parts[6] == "None" or parts[6] == '': pixel_size_y=None
                else: pixel_size_y = float(parts[6])
                if parts[7] == "None" or parts[7] == '': grid_origin_x=None
                else: grid_origin_x = float(parts[7])
                if parts[8] == "None" or parts[8] == '': grid_origin_y=None
                else: grid_origin_y = float(parts[8])
            except StandardError:
                log.error("Could not parse proj4 grid configuration: '%s'" % (line))
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

            proj4_grids[grid_name] = {}
            proj4_grids[grid_name]["grid_kind"] = GRID_KIND_PROJ4
            proj4_grids[grid_name]["proj4_str"]    = proj4_str
            proj4_grids[grid_name]["pixel_size_x"] = pixel_size_x
            proj4_grids[grid_name]["pixel_size_y"] = pixel_size_y
            proj4_grids[grid_name]["grid_origin_x"]     = grid_origin_x
            proj4_grids[grid_name]["grid_origin_y"]     = grid_origin_y
            proj4_grids[grid_name]["grid_width"]        = grid_width
            proj4_grids[grid_name]["grid_height"]       = grid_height
        else:
            log.error("Unknown grid type '%s' for grid '%s' in grid config" % (grid_type,grid_name))
            raise ValueError("Unknown grid type '%s' for grid '%s' in grid config" % (grid_type,grid_name))

    return gpd_grids,proj4_grids

def read_grids_config(config_filepath):
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

def validate_configs(shapes_dict, gpd_dict, proj4_dict):
    shapes_grid_names = set(shapes_dict.keys())

    gpd_grid_names = gpd_dict.keys()
    proj4_grid_names = proj4_dict.keys()
    grids_grid_names = set(gpd_grid_names + proj4_grid_names)

    in_shapes = shapes_grid_names - grids_grid_names
    if len(in_shapes) != 0:
        log.error("These grids are in the shapes config, but not the grids config: \n%s" % "\n".join(in_shapes))
        raise ValueError("There were grids in the shapes config, but not the grids config")

    in_grids = grids_grid_names - shapes_grid_names
    # make the set a list, in case we remove items, otherwise exception
    for grid in list(in_grids):
        # Remove grids that fit to the data
        # Could use some more that as to "will the data actually fit this fit grid"
        if grid in proj4_dict and (proj4_dict[grid]["grid_width"] is None or \
                proj4_dict[grid]["pixel_size_x"] is None or \
                proj4_dict[grid]["grid_origin_x"] is None):
            in_grids.remove(grid)
    if len(in_grids) != 0:
        log.error("These grids are in the grids config, but not the shapes config: \n%s" % "\n".join(in_grids))
        raise ValueError("There were grids in the grids config, but not the shapes config")

# See bottom of file where default configuration files are loaded
def load_global_config_files(shapes_config=SHAPES_CONFIG_FILEPATH,
        grids_config=GRIDS_CONFIG_FILEPATH):
    global SHAPES
    global GPD_GRIDS,PROJ4_GRIDS
    SHAPES = read_shapes_config(shapes_config)
    GPD_GRIDS,PROJ4_GRIDS = read_grids_config(grids_config)
    validate_configs(SHAPES, GPD_GRIDS, PROJ4_GRIDS)

def main():
    from argparse import ArgumentParser
    from pprint import pprint
    description = """
Test configuration files and see how polar2grid will read them.
"""
    parser = ArgumentParser(description=description)
    parser.add_argument("--shapes", dest="shapes", default=SHAPES_CONFIG_FILEPATH,
            help="specify a shapes configuration file to check")
    parser.add_argument("--grids", dest="grids", default=GRIDS_CONFIG_FILEPATH,
            help="specify a grids configuration file to check")
    parser.add_argument("--determine", dest="determine", nargs="*",
            help="determine what grids the provided data fits in (<lon fbf>,<lat fbf>,<grid names>")
    args = parser.parse_args()

    print "Running log command"
    logging.basicConfig(level=logging.DEBUG)

    shapes_dict = read_shapes_config(args.shapes)
    print "Shapes configuration file (%s):" % args.shapes
    pprint(shapes_dict)
    gpd_grids,proj4_grids = read_grids_config(args.grids)
    print "GPD Grids from configuration file '%s':" % args.grids
    pprint(gpd_grids)
    print "PROJ4 Grids from configuration file '%s':" % args.grids
    pprint(proj4_grids)

    print "Validating these configuration files..."
    validate_configs(shapes_dict, gpd_grids, proj4_grids)

    if args.determine is not None and len(args.determine) != 0:
        print "Loading the grids and shapes configurations to be used for determination"
        load_global_config_files(args.shapes, args.grids)
        print "Determining if data fits in this grid"
        determine_grid_coverage_fbf(args.determine[0], args.determine[1], args.determine[2:])

    print "DONE"

if __name__ == "__main__":
    sys.exit(main())

# Load the default configurations after the main method
# this way if main shows more information it might be more useful to check the
# configs with that
load_global_config_files()

