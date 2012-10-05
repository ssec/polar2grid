#!/usr/bin/env python
# encoding: utf-8
"""Functions to read configuration files for the viirs2awips.

Instances of default configuration file locations and contents.

Configuration files from which the above are derived
Global objects representing configuration files

:Variables:
    GRIDS : dict
        Mappings to product_id, NC filename format,
        and other meta data needed for NC files
    BANDS : dict
        Mappings to product_id, NC filename format,
        and other meta data needed for NC files
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

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from netCDF4 import Dataset
from xml.etree import cElementTree
from polar2grid.nc import ncml_tag
from polar2grid.core.constants import NOT_APPLICABLE

import os
import sys
import logging

log = logging.getLogger(__name__)

# Get configuration file locations
script_dir = os.path.split(os.path.realpath(__file__))[0]
grids_dir = os.path.split(script_dir)[0] # grids directory is in root pkg dir
default_grids_config = os.path.join(script_dir, "awips_grids.conf")
default_ancil_dir = os.path.join(grids_dir, "grids")
default_shapes_config = os.path.join(script_dir, "awips_shapes.conf")
GRIDS_CONFIG = os.environ.get("VIIRS_GRIDS_CONFIG", default_grids_config)
ANCIL_DIR     = os.environ.get("VIIRS_ANCIL_DIR", default_ancil_dir)
SHAPES_CONFIG   = os.environ.get("VIIRS_SHAPE_CONFIG", default_shapes_config)

def find_grid_templates(ancil_dir):
    grid_templates = {}
    # Get a set of the "grid211" part of every template
    for t in set([x.split(".")[0] for x in os.listdir(ANCIL_DIR) if x.startswith("grid")]):
        nc_temp = t + ".ncml"
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
        if line.startswith("#") or line.startswith("\n"): continue
        parts = line.strip().split(",")
        if len(parts) < 8:
            print "ERROR: Need at least 4 columns in templates.conf (%s)" % line
        product_id = parts[0]
        grid_number = parts[1]
        bkind = parts[2].lower()
        band = parts[3].lower() if parts[3] not in ["NA","None"] else NOT_APPLICABLE
        channel = parts[4]
        source = parts[5]
        satelliteName = parts[6]
        nc_name = parts[7]

        if grid_number not in grids_map:
            grids_map[grid_number] = {}
        if band in grids_map[grid_number]:
            print "ERROR: templates.conf contains two or more entries for grid %s and band %s,%s" % (grid_number,bkind,band)
            sys.exit(-1)

        if (bkind,band) not in bands_map:
            bands_map[(bkind,band)] = {}
        if grid_number in bands_map[(bkind,band)]:
            print "ERROR: templates.conf contains two or more entries for grid %s and band %s,%s" % (grid_number,bkind,band)
            sys.exit(-1)

        val = (product_id,channel,source,satelliteName,nc_name)
        bands_map[(bkind,band)][grid_number] = val
        grids_map[grid_number][(bkind,band)] = val

    return grids_map,bands_map

def read_shapes_config(config_filepath):
    shapes = dict((parts[0],tuple([float(x) for x in parts[1:6]])) for parts in [line.split(",") 
        for line in open(config_filepath) if not line.startswith("#") ] )
    return shapes

GRID_TEMPLATES = find_grid_templates(ANCIL_DIR)
GRIDS,BANDS = read_grid_config(GRIDS_CONFIG)
SHAPES = read_shapes_config(SHAPES_CONFIG)

def _get_awips_info(kind, band, grid_number,
        grids_map=None, bands_map=None):
    if grids_map is None: grids_map = GRIDS
    if bands_map is None: bands_map = BANDS
    key = (kind,band)
    if key not in bands_map or grid_number not in grids_map:
        log.error("Kind: %s, Band: %s or grid %s not found in templates.conf" % (key[0],key[1],grid_number))
        raise ValueError("Kind: %s, Band: %s or grid %s not found in templates.conf" % (key[0],key[1],grid_number))
    else:
        return grids_map[grid_number][key]

def _get_grid_templates(grid_number, gpd=None, nc=None,
        grid_templates=None):
    if grid_templates is None: grid_templates = GRID_TEMPLATES

    if grid_number not in grid_templates:
        if nc is not None and gpd is not None:
            return (gpd,nc)
        else:
            log.error("Couldn't find grid %s in grid templates" % grid_number)
            raise ValueError("Couldn't find grid %s in grid templates" % grid_number)
    else:
        use_gpd = grid_templates[grid_number][0]
        use_nc = grid_templates[grid_number][1]
        use_gpd = gpd or use_gpd
        use_nc = nc or use_nc
        return (use_gpd,use_nc)

def get_shape_from_ncml(fn, var_name):
    """Returns (rows,cols) of the variable with name
    `var_name` in the ncml file with filename `fn`.
    """
    xml_parser = cElementTree.parse(fn)
    all_vars = xml_parser.findall(ncml_tag("variable"))
    important_var = [ elem for elem in all_vars if elem.get("name") == var_name]
    if len(important_var) != 1:
        log.error("Couldn't find a variable with name %s in the ncml file %s" % (var_name,fn))
        raise ValueError("Couldn't find a variable with name %s in the ncml file %s" % (var_name,fn))
    important_var = important_var[0]

    # Get the shape out
    shape = important_var.get("shape")
    if shape is None:
        log.error("NCML variable %s does not have the required shape attribute" % (var_name,))
        raise ValueError("NCML variable %s does not have the required shape attribute" % (var_name,))

    # Get dimension names from shape attribute
    shape_dims = shape.split(" ")
    if len(shape_dims) != 2:
        log.error("2 dimensions are required for variable %s" % (var_name,))
        raise ValueError("2 dimensions are required for variable %s" % (var_name,))
    rows_name,cols_name = shape_dims

    # Get the dimensions by their names
    all_dims = xml_parser.findall(ncml_tag("dimension"))
    important_dims = [ elem for elem in all_dims if elem.get("name") == rows_name or elem.get("name") == cols_name ]
    if len(important_dims) != 2:
        log.error("Corrupt NCML file %s, can't find both of %s's dimensions" % (fn, var_name))
        raise ValueError("Corrupt NCML file %s, can't find both of %s's dimensions" % (fn, var_name))

    if important_dims[0].get("name") == rows_name:
        rows = int(important_dims[0].get("length"))
        cols = int(important_dims[1].get("length"))
    else:
        rows = int(important_dims[1].get("length"))
        cols = int(important_dims[0].get("length"))
    return rows,cols

def get_grid_info(kind, band, grid_number, gpd=None, nc=None,
        grids_map=None, bands_map=None,
        shapes_map=None, grid_templates=None):
    """Assumes verify_grid was already run to verify that the information
    was available.
    """
    if grids_map is None: grids_map = GRIDS
    if bands_map is None: bands_map = BANDS
    if shapes_map is None: shapes_map = SHAPES
    if grid_templates is None: grid_templates = GRID_TEMPLATES

    awips_info = _get_awips_info(kind, band, grid_number)
    temp_info = _get_grid_templates(grid_number, gpd, nc)

    # Get number of rows and columns for the output grid
    out_rows,out_cols = get_shape_from_ncml(temp_info[1], "image")
    log.debug("Number of output columns calculated from NC template %d" % out_cols)
    log.debug("Number of output rows calculated from NC template %d" % out_rows)

    grid_info = {}
    grid_info["grid_number"] = grid_number
    grid_info["product_id"] = awips_info[0]
    grid_info["channel"] = awips_info[1]
    grid_info["source"] = awips_info[2]
    grid_info["sat_name"] = awips_info[3]
    grid_info["nc_format"] = awips_info[4]
    grid_info["gpd_template"] = temp_info[0]
    grid_info["nc_template"] = temp_info[1]
    grid_info["out_rows"] = out_rows
    grid_info["out_cols"] = out_cols
    return grid_info


def verify_config(kind, band, grid_number, gpd=None, nc=None,
        grids_map=None, bands_map=None,
        shapes_map=None, grid_templates=None):

    if grids_map is None: grids_map = GRIDS
    if bands_map is None: bands_map = BANDS
    if shapes_map is None: shapes_map = SHAPES
    if grid_templates is None: grid_templates = GRID_TEMPLATES

    key = (kind,band)

    if key in bands_map and \
        grid_number in grids_map and \
        key in grids_map[grid_number] and \
        grid_number in shapes_map and \
        (grid_number in grid_templates or \
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
