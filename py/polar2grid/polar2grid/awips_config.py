#!/usr/bin/env python
# encoding: utf-8
"""Functions to read configuration files for the viirs2awips.

Instances of default configuration file locations and contents.

Configuration files from which the above are derived
Global objects representing configuration files

:Variables:
    GRIDS : dict
        Mappings to product_id and NC filename format
    BANDS : dict
        Mappings to product_id and NC filename format
    GRID_TEMPLATES : dict
        Mappings to gpd and NC templates.
    SHAPES : dict 
        Mappings of grid name to lat/lon boundaries and coverage percentage
    PRODUCTS_FILE
        File holding band to grid mappings, including product_id and NC
        filename format
    ANCIL_DIR
        Directory holding gpd and nc templates for AWIPS grids.
    SHAPES_FILE
        File holding grid boundaries for grids specified in the
        grids directory and products.conf file

:newfield revision: Revision
:author: David Hoese (davidh)
:contact: david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"
from netCDF4 import Dataset

import os
import sys
import logging

log = logging.getLogger(__name__)

# Get configuration file locations
script_dir = os.path.split(os.path.realpath(__file__))[0]
default_grids_config = os.path.join(script_dir, "awips_grids.conf")
default_ancil_dir = os.path.join(script_dir, "grids")
default_shapes_config = os.path.join(script_dir, "awips_shapes.conf")
GRIDS_CONFIG = os.environ.get("VIIRS_GRIDS_CONFIG", default_grids_config)
ANCIL_DIR     = os.environ.get("VIIRS_ANCIL_DIR", default_ancil_dir)
SHAPES_CONFIG   = os.environ.get("VIIRS_SHAPE_CONFIG", default_shapes_config)

def find_grid_templates(ancil_dir):
    grid_templates = {}
    # Get a set of the "grid211" part of every template
    for t in set([x.split(".")[0] for x in os.listdir(ANCIL_DIR) if x.startswith("grid")]):
        nc_temp = t + ".nc"
        gpd_temp = t + ".gpd"
        nc_path = os.path.join(ANCIL_DIR, nc_temp)
        gpd_path = os.path.join(ANCIL_DIR, gpd_temp)
        grid_number = t[4:]
        if os.path.exists(nc_path) and os.path.exists(gpd_path):
            grid_templates[grid_number] = (gpd_path, nc_path)
    return grid_templates

def read_grid_config(config_filepath):
    # grid -> band -> (product_id,nc_name)
    grids_map = {}
    # band -> grid -> (product_id,nc_name)
    bands_map = {}
    for line in open(config_filepath):
        # For comments
        if line.startswith("#"): continue
        parts = line.strip().split(",")
        if len(parts) < 4:
            print "ERROR: Need at least 4 columns in templates.conf (%s)" % line
        product_id = parts[0]
        grid_number = parts[1]
        band = parts[2]
        if len(band) != 3:
            print "ERROR: Expected 3 characters for band got %d (%s)" % (len(band),band)
        nc_name = parts[3]

        if grid_number not in grids_map:
            grids_map[grid_number] = {}
        if band in grids_map[grid_number]:
            print "ERROR: templates.conf contains two or more entries for grid %s and band %s" % (grid_number,band)
            sys.exit(-1)

        if band not in bands_map:
            bands_map[band] = {}
        if grid_number in bands_map[band]:
            print "ERROR: templates.conf contains two or more entries for grid %s and band %s" % (grid_number,band)
            sys.exit(-1)

        val = (product_id,nc_name)
        bands_map[band][grid_number] = val
        grids_map[grid_number][band] = val

    return grids_map,bands_map

def read_shapes_config(config_filepath):
    shapes = dict((parts[0],tuple([float(x) for x in parts[1:6]])) for parts in [line.split(",") 
        for line in open(config_filepath) if not line.startswith("#") ] )
    return shapes

GRID_TEMPLATES = find_grid_templates(ANCIL_DIR)
GRIDS,BANDS = read_grid_config(GRIDS_CONFIG)
SHAPES = read_shapes_config(SHAPES_CONFIG)

def _get_awips_info(kind, band, grid_number,
        GRIDS=GRIDS, BANDS=BANDS):
    if kind == "DNB":
        bname = kind
    else:
        bname = kind + band
    if bname not in BANDS or grid_number not in GRIDS:
        log.error("Band %s or grid %s not found in templates.conf" % (bname,grid_number))
        raise ValueError("Band %s or grid %s not found in templates.conf" % (bname,grid_number))
    else:
        return GRIDS[grid_number][bname]

def _get_grid_templates(grid_number, gpd=None, nc=None,
        GRID_TEMPLATES=GRID_TEMPLATES):
    if grid_number not in GRID_TEMPLATES:
        if nc is not None and gpd is not None:
            return (gpd,nc)
        else:
            log.error("Couldn't find grid %s in grid templates" % grid_number)
            raise ValueError("Couldn't find grid %s in grid templates" % grid_number)
    else:
        use_gpd = GRID_TEMPLATES[grid_number][0]
        use_nc = GRID_TEMPLATES[grid_number][1]
        use_gpd = gpd or use_gpd
        use_nc = nc or use_nc
        return (use_gpd,use_nc)

def get_grid_info(kind, band, grid_number, gpd=None, nc=None,
        GRIDS=GRIDS, BANDS=BANDS,
        SHAPES=SHAPES, GRID_TEMPLATES=GRID_TEMPLATES):
    """Assumes verify_grid was already run to verify that the information
    was available.
    """
    awips_info = _get_awips_info(kind, band, grid_number)
    temp_info = _get_grid_templates(grid_number, gpd, nc)

    # Get number of rows and columns for the output grid
    nc = Dataset(temp_info[1], "r")
    (out_rows,out_cols) = nc.variables["image"].shape
    log.debug("Number of output columns calculated from NC template %d" % out_cols)
    log.debug("Number of output rows calculated from NC template %d" % out_rows)

    grid_info = {}
    grid_info["grid_number"] = grid_number
    grid_info["product_id"] = awips_info[0]
    grid_info["nc_format"] = awips_info[1]
    grid_info["gpd_template"] = temp_info[0]
    grid_info["nc_template"] = temp_info[1]
    grid_info["out_rows"] = out_rows
    grid_info["out_cols"] = out_cols
    return grid_info


def verify_config(kind, band, grid_number, gpd=None, nc=None,
        GRIDS=GRIDS, BANDS=BANDS,
        SHAPES=SHAPES, GRID_TEMPLATES=GRID_TEMPLATES):
    if kind == "DNB":
        bname = kind
    else:
        bname = kind + band

    if bname in BANDS and \
        grid_number in GRIDS and \
        bname in GRIDS[grid_number] and \
        grid_number in SHAPES and \
        (grid_number in GRID_TEMPLATES or \
        (gpd is not None and nc is not None)):
        return True
    else:
        return False

if __name__ == "__main__":
    from pprint import pprint
    print "Grid Templates:"
    pprint(GRID_TEMPLATES)
    print "Grids map:"
    pprint(GRIDS)
    print "Bands map:"
    pprint(BANDS)
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
