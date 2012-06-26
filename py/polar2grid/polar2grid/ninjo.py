#!/usr/bin/env python
# encoding: utf-8
"""Module to provide the NinJo backend to a polar2grid chain.  This module
takes reprojected image data and other parameters required by NinJo and
places them correctly in to the modified geotiff format accepted by NinJo.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         June 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from polar2grid.tiff import tag_array,TIFFExtender,TIFFFieldInfo,TIFFDataType,FIELD_CUSTOM,tiff2ctypes
from libtiff import libtiff_ctypes as lc
import libtiff

import os
import sys
import logging
import ctypes

log = logging.getLogger(__name__)

def add_tag(num, name, data_type, convert=lambda d:d.value):
    setattr(lc, "TIFFTAG_" + name, num)
    lc.tifftags[num] = (data_type, convert)
    return num

ninjo_tags = []
REF_POINT = add_tag(33922, "ModelTiePoint", ctypes.c_double)
ninjo_tags.append(TIFFFieldInfo(REF_POINT, 6, 6, TIFFDataType.TIFF_DOUBLE, FIELD_CUSTOM, True, True, "ModelTiePoint"))
ninjo_tags_struct = tag_array(len(ninjo_tags))(*ninjo_tags)
ninjo_extension = TIFFExtender(ninjo_tags_struct)

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
    proj4_str = proj4_str + " " + " ".join(["+%s=%s" % (k,v) for k,v in proj4_dict.items()])
    return proj4_str

def create_ninjo_tiff(image_data, output_fn, **kwargs):
    pass

def main():
    from polar2grid.core import Workspace # used to import image data
    import optparse
    parser = optparse.OptionParser([" "])
    parser.add_option("--debug", dest="show_debug", action="store_true", default=False,
            help="Show additional debug messages")

    options,args = parser.parse_args()
    if options.show_debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    if len(args) == 3:
        image_fn = args[0]
        proj4_str = args[1]
        tiff_fn = args[2]
    else:
        parser.print_usage()
        return -1

    # Get the image data to be put into the ninjotiff
    W = Workspace(".")
    image_data = getattr(W, image_fn.split(".")[0])

    # Create the ninjotiff
    create_ninjo_tiff(image_data, tiff_fn, proj4_dict=from_proj4(proj4_str))

if __name__ == "__main__":
    sys.exit(main())

