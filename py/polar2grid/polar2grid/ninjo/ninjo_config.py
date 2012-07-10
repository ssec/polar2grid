#!/usr/bin/env python
# encoding: utf-8
"""Functions to read configuration files for the ninjo backend.

Instances of default configuration file locations and contents.

Configuration files from which the above are derived
Global objects representing configuration files

:Variables:
    GRIDS : dict
        Mappings to ninjo projection name,xresolution,yresolution
    GRID_TEMPLATES : dict
        Mappings to gpd template
    SHAPES : dict 
        Mappings of grid name to lat/lon boundaries and coverage percentage
    GRIDS_CONFIG 
        File holding grid mappings that get parsed into GRIDS
    ANCIL_DIR
        Directory holding gpd for AWIPS grids.
    SHAPES_FILE
        File holding grid boundaries for grids specified in the
        grids directory and products.conf file

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from polar2grid.core import gpd_to_proj4

import os
import sys
import logging

log = logging.getLogger(__name__)

# Get configuration file locations
script_dir = os.path.split(os.path.realpath(__file__))[0]
grids_dir = os.path.split(script_dir)[0] # grids directory is in root pkg dir
default_grids_config = os.path.join(script_dir, "ninjo_grids.conf")
default_ancil_dir = os.path.join(grids_dir, "grids")
default_shapes_config = os.path.join(script_dir, "ninjo_shapes.conf")
GRIDS_CONFIG = os.environ.get("NINJO_GRIDS_CONFIG", default_grids_config)
ANCIL_DIR     = os.environ.get("GRIDS_ANCIL_DIR", default_ancil_dir)
SHAPES_CONFIG   = os.environ.get("NINJO_SHAPE_CONFIG", default_shapes_config)

def find_grid_templates(ancil_dir):
    grid_templates = {}
    # Get a set of the "grid211" part of every template
    for t in set([x.split(".")[0] for x in os.listdir(ANCIL_DIR) if x.startswith("grid")]):
        gpd_temp = t + ".gpd"
        gpd_path = os.path.join(ANCIL_DIR, gpd_temp)
        grid_number = t[4:]
        if os.path.exists(gpd_path):
            grid_templates[grid_number] = gpd_path
    return grid_templates

def read_grid_config(config_filepath):
    # grid -> (nproj name, xres, yres)
    grids_map = {}
    for line in open(config_filepath):
        # For comments
        if line.startswith("#") or line.startswith("\n"): continue
        parts = line.strip().split(",")
        if len(parts) < 4:
            print "ERROR: Need at least 4 columns in templates.conf (%s)" % line
        grid_number = parts[0]
        nproj = parts[1]
        xres = float(parts[2])
        yres = float(parts[3])

        val = (nproj,xres,yres)
        grids_map[grid_number] = val

    return grids_map

def read_shapes_config(config_filepath):
    shapes = dict((parts[0],tuple([float(x) for x in parts[1:6]])) for parts in [line.split(",") 
        for line in open(config_filepath) if not line.startswith("#") ] )
    return shapes

GRID_TEMPLATES = find_grid_templates(ANCIL_DIR)
GRIDS = read_grid_config(GRIDS_CONFIG)
SHAPES = read_shapes_config(SHAPES_CONFIG)

def _get_grid_meta(grid_name, grids_map=None):
    if grids_map is None: grids_map = GRIDS
    if grid_name not in grids_map:
        log.error("The ninjo backend is not configured to handle grid %s" % grid_name)
        raise ValueError("The ninjo backend is not configured to handle grid %s" % grid_name)
    return grids_map[grid_name]

def _get_gpd_filename(grid_number, gpd=None, grid_templates=None):
    if grid_templates is None: grid_templates = GRID_TEMPLATES

    if grid_number not in grid_templates:
        if gpd is not None:
            return gpd
        else:
            log.error("Couldn't find grid %s in grid templates" % grid_number)
            raise ValueError("Couldn't find grid %s in grid templates" % grid_number)
    else:
        use_gpd = grid_templates[grid_number]
        use_gpd = gpd or use_gpd
        return use_gpd

def get_grid_info(kind, band, grid_number, gpd=None,
        grids_map=None, shapes_map=None, grid_templates=None):
    """Assumes verify_grid was already run to verify that the information
    was available.
    """
    if grids_map is None: grids_map = GRIDS
    if shapes_map is None: shapes_map = SHAPES
    if grid_templates is None: grid_templates = GRID_TEMPLATES

    grid_meta = _get_grid_meta(kind, band, grid_number)
    gpd_template = _get_gpd_filename(grid_number, gpd)

    grid_info = {}
    grid_info["grid_number"] = grid_number
    grid_info["gpd_template"] = gpd_template
    grid_info["nproj"] = grid_meta[0]
    grid_info["xres"] = grid_meta[1]
    grid_info["yres"] = grid_meta[2]
    grid_info["proj4"],grid_info["gpd"] = gpd_to_proj4(gpd_template)
    grid_info["out_rows"] = grid_info["gpd"]["IMAGEWIDTH"]
    grid_info["out_cols"] = grid_info["gpd"]["IMAGELENGTH"]
    return grid_info


def verify_config(kind, band, grid_number, gpd=None, nc=None,
        grids_map=None, bands_map=None,
        shapes_map=None, grid_templates=None):

    if grids_map is None: grids_map = GRIDS
    if shapes_map is None: shapes_map = SHAPES
    if grid_templates is None: grid_templates = GRID_TEMPLATES

    if grid_number in grids_map and \
        grid_number in shapes_map and \
        (grid_number in grid_templates or \
        gpd is not None):
        return True
    else:
        return False

if __name__ == "__main__":
    from pprint import pprint
    print "Grid Templates:"
    pprint(GRID_TEMPLATES)
    print "Grids map:"
    pprint(GRIDS)
    print "Shapes map:"
    pprint(SHAPES)

    if len(sys.argv) == 4:
        valid = verify_config(*sys.argv[1:4])
        if valid:
            print "Kind,band,grid_number in configs: YES"
            pprint(get_grid_info(*sys.argv[1:4]))
        else:
            print "Kind,band,grid_number in configs: NO"
    sys.exit(0)
