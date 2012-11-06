#!/usr/bin/env python
# encoding: utf-8
"""Simple python wrapper around the actual shell calls to
ms2gt utilities.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

import os
import sys
import logging
import re
from glob import glob
from subprocess import check_call,CalledProcessError

log = logging.getLogger(__name__)

CR_REG = r'.*_(\d+).img'
cr_reg = re.compile(CR_REG)

def _ll2cr_rows_info(fn):
    CR_REG = r'.*_(?P<scans_out>\d+)_(?P<scan_first>\d+)_(?P<num_rows>\d+).img'
    cr_reg = re.compile(CR_REG)
    row_match = cr_reg.match(fn)
    if row_match is None:
        log.error("Couldn't get row information from ll2cr file")
        return None
    d = row_match.groupdict()
    d["scans_out"] = int(d["scans_out"])
    d["scan_first"] = int(d["scan_first"])
    d["num_rows"] = int(d["num_rows"])
    return d

def _ll2cr_cols_info(fn):
    CR_REG = r'.*_(?P<scans_out>\d+)_(?P<scan_first>\d+)_(?P<num_cols>\d+).img'
    cr_reg = re.compile(CR_REG)
    col_match = cr_reg.match(fn)
    if col_match is None:
        log.error("Couldn't get col information from ll2cr file")
        return None
    d = col_match.groupdict()
    d["scans_out"] = int(d["scans_out"])
    d["scan_first"] = int(d["scan_first"])
    d["num_cols"] = int(d["num_cols"])
    return d

def ll2cr(colsin, scansin, rowsperscan, latfile, lonfile, gpdfile,
        verbose=False, f_scansout=None, rind=None, fill_io=None, tag="ll2cr"):
    args = ["ll2cr"]
    if verbose:
        args.append("-v")
    if f_scansout is not None:
        args.extend(["-f", "%d" % f_scansout])
    if rind is not None:
        args.extend(["-r", "%d" % rind])
    if fill_io is not None:
        args.extend(["-F", "%f" % fill_io[0], "%f" % fill_io[1]])
    args.extend([colsin, scansin, rowsperscan, latfile, lonfile, gpdfile])
    if tag:
        args.append(tag)

    try:
        args = [ str(a) for a in args ]
        log.debug("Running ll2cr with '%s'" % " ".join(args))
        check_call(args)
    except CalledProcessError:
        log.error("Error running ll2cr", exc_info=1)
        raise ValueError("Error running ll2cr")
    except OSError:
        log.error("Couldn't find 'll2cr' command in PATH")
        raise ValueError("Couldn't find 'll2cr' command in PATH")

    d = {}
    tmp = glob("%s_cols_*.img" % tag)
    if len(tmp) != 1:
        log.error("Couldn't find cols img file from ll2cr: '%s'" % tag)
        raise ValueError("Couldn't find cols img file from ll2cr")
    d["cols_filename"] = tmp[0]
    log.debug("Columns file is %s" % d["cols_filename"])

    tmp = glob("%s_rows_*.img" % tag)
    if len(tmp) != 1:
        log.error("Couldn't find rows img file from ll2cr: '%s'" % tag)
        raise ValueError("Couldn't find rows img file from ll2cr")
    d["rows_filename"] = tmp[0]
    log.debug("Rows file is %s" % d["rows_filename"])

    col_dict = _ll2cr_cols_info(d["cols_filename"])
    row_dict = _ll2cr_rows_info(d["rows_filename"])
    if col_dict is None or row_dict is None:
        # Log message was delivered before
        raise ValueError("Couldn't get information from ll2cr output")

    d["num_cols"] = col_dict["num_cols"]
    d["num_rows"] = row_dict["num_rows"]

    if col_dict["scans_out"] != row_dict["scans_out"]:
        log.error("ll2cr didn't produce the same number of scans for cols and rows")
        raise ValueError("ll2cr didn't produce the same number of scans for cols and rows")
    d["scans_out"] = col_dict["scans_out"]
    if d["scans_out"] == 0:
        log.error("ll2cr did not map any data, 0 scans out")
        raise ValueError("ll2cr did not map any data, 0 scans out")

    if col_dict["scan_first"] != row_dict["scan_first"]:
        log.error("ll2cr didn't produce the same number for scan first cols and rows")
        raise ValueError("ll2cr didn't produce the same number for scan first cols and rows")
    d["scan_first"] = col_dict["scan_first"]

    log.debug("Number of Scans Out = %d" % d["scans_out"])
    log.debug("Number for Scan First = %d" % d["scan_first"])
    log.debug("Number of Columns = %d" % d["num_cols"])
    log.debug("Number of Rows = %d" % d["num_rows"])

    return d

def fornav(chan_count, swath_cols, swath_scans, swath_rows_per_scan, colfile, rowfile, swathfile, grid_cols, grid_rows, output_fn,
        verbose=False, swath_data_type_1=None, swath_fill_1=None, grid_fill_1=None, weight_delta_max=None, weight_distance_max=None,
        start_scan=None):
    args = ["fornav", "%d" % chan_count]

    if chan_count == 1 and not isinstance(swathfile, list):
        swathfile = [swathfile]
    if chan_count == 1 and not isinstance(output_fn, list):
        output_fn = [output_fn]
    if chan_count > 1 and len(swathfile) != chan_count:
        if isinstance(swathfile, list):
            log.error("Number of input files %d does not equal channel count %d" % (len(swathfile), chan_count))
            raise ValueError("Number of input files %d does not equal channel count %d" % (len(swathfile), chan_count))
        else:
            log.error("Input files must be a list if channel count is more than 1")
            raise ValueError("Input files must be a list if channel count is more than 1")

    if chan_count > 1 and len(output_fn) != chan_count:
        if isinstance(output_fn, list):
            log.error("Number of output files %d does not equal channel count %d" % (len(output_fn), chan_count))
            raise ValueError("Number of output files %d does not equal channel count %d" % (len(output_fn), chan_count))
        else:
            log.error("Output files must be a list if channel count is more than 1")
            raise ValueError("Output files must be a list if channel count is more than 1")

    if verbose:
        args.append("-v")
    if swath_data_type_1:
        args.append("-t")
        if chan_count > 1 and not isinstance(swath_data_type_1, list):
            args.extend(["%s" % swath_data_type_1]*chan_count)
        elif chan_count > 1:
            args.extend(swath_data_type_1)
        else:
            args.append(swath_data_type_1)
    if swath_fill_1 is not None:
        args.append("-f")
        if chan_count > 1 and not isinstance(swath_fill_1, list):
            args.extend(["%f" % swath_fill_1]*chan_count)
        elif chan_count > 1:
            args.extend(swath_fill_1)
        else:
            args.append(swath_fill_1)
    if grid_fill_1 is not None:
        args.append("-F")
        if chan_count > 1 and not isinstance(grid_fill_1, list):
            args.extend(["%f" % grid_fill_1]*chan_count)
        elif chan_count > 1:
            args.extend(grid_fill_1)
        else:
            args.append(grid_fill_1)
    if weight_delta_max is not None:
        args.extend(["-D", "%d" % weight_delta_max])
    if weight_distance_max is not None:
        args.extend(["-d", "%d" % weight_distance_max])
    if start_scan is not None:
        args.extend(["-s", "%d" % start_scan[0], "%d" % start_scan[1]])

    args.extend([swath_cols, swath_scans, swath_rows_per_scan, colfile, rowfile])
    args.extend(swathfile)
    args.extend([grid_cols, grid_rows])
    args.extend(output_fn)

    try:
        args = [ str(a) for a in args ]
        log.debug("Running fornav with '%s'" % " ".join(args))
        check_call(args)
    except CalledProcessError:
        log.error("Error running fornav", exc_info=1)
        raise ValueError("Fornav failed")
    except OSError:
        log.error("Couldn't find 'fornav' command in PATH")
        raise ValueError("Fornav was not found your PATH")

    d = {}
    return d

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print "No scripting implemented"
    sys.exit(0)
