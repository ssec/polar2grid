#!/usr/bin/env python
# encoding: utf-8
"""Functions to create 'pseudo' or 'synthetic' bands from raw VIIRS data.

There is no interface currently defined for these functions; arguments and
returned values are up to the rest of the VIIRS frontend calling them.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2012
:license:      GNU GPLv3
"""

import numpy
from polar2grid.core.constants import *
from polar2grid.core import Workspace

import os
import sys
import logging

log = logging.getLogger(__name__)

def create_fog_band(bands, fill_value=DEFAULT_FILL_VALUE):
    # Fog pseudo-band
    if (BKIND_I, BID_04) in bands and (BKIND_I, BID_05) in bands:
        log.info("Creating IFOG pseudo band...")
        try:
            W = Workspace('.')
            mode_attr = bands[(BKIND_I,BID_05)]["fbf_mode"].split(".")[0]
            mode_data = getattr(W, mode_attr)
            night_mask = mode_data >= 100
            del mode_data
        except StandardError:
            log.error("Error getting mode data while creating FOG band")
            log.debug("Mode error:", exc_info=1)
            return

        num_night_points = numpy.sum(night_mask)
        if num_night_points == 0:
            # We only create fog mask if theres nighttime data
            log.info("No night data found to create FOG band for")
            return
        log.debug("Creating FOG band for %s nighttime data points" % num_night_points)

        fog_dict = {
                "kind"           : BKIND_I,
                "band"           : BID_FOG,
                "data_kind"      : DKIND_FOG,
                "remap_data_as"  : DKIND_BTEMP,
                "rows_per_scan"  : bands[(BKIND_I, BID_05)]["rows_per_scan"],
                "fbf_img"        : "image_IFOG.%s" % ".".join(bands[(BKIND_I, BID_05)]["fbf_img"].split(".")[1:]),
                "fbf_mode"       : bands[(BKIND_I, BID_05)]["fbf_mode"],
                "swath_scans"    : bands[(BKIND_I, BID_05)]["swath_scans"],
                "swath_rows"     : bands[(BKIND_I, BID_05)]["swath_rows"],
                "swath_cols"     : bands[(BKIND_I, BID_05)]["swath_cols"]
                }
        try:
            W = Workspace(".")
            i5_attr = bands[(BKIND_I, BID_05)]["fbf_img"].split(".")[0]
            i4_attr = bands[(BKIND_I, BID_04)]["fbf_img"].split(".")[0]
            i5 = getattr(W, i5_attr)
            i4 = getattr(W, i4_attr)
            fog_map = numpy.memmap(fog_dict["fbf_img"],
                    dtype=numpy.float32,
                    mode="w+",
                    shape=i5.shape
                    )
            numpy.subtract(i5, i4, fog_map)
            fog_map[ (~night_mask) | (i5 == fill_value) | (i4 == fill_value) ] = fill_value
            del fog_map
            del i5,i4
            bands[(BKIND_I, BID_FOG)] = fog_dict
        except StandardError:
            log.error("Error creating Fog pseudo band")
            log.debug("Fog creation error:", exc_info=1)
