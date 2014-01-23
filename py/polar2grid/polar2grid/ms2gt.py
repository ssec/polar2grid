#!/usr/bin/env python
# encoding: utf-8
"""Simple python wrapper around the actual shell calls to
ms2gt utilities.

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
    CR_REG = r'.*_(?P<scans_out>\d+)_(?P<scan_first>\d+)_(?P<ll2cr_rowsperscan>\d+).img'
    cr_reg = re.compile(CR_REG)
    row_match = cr_reg.match(fn)
    if row_match is None:
        log.error("Couldn't get row information from ll2cr file")
        return None
    d = row_match.groupdict()
    d["scans_out"] = int(d["scans_out"])
    d["scan_first"] = int(d["scan_first"])
    d["ll2cr_rowsperscan"] = int(d["ll2cr_rowsperscan"])
    return d

def _ll2cr_cols_info(fn):
    CR_REG = r'.*_(?P<scans_out>\d+)_(?P<scan_first>\d+)_(?P<ll2cr_rowsperscan>\d+).img'
    cr_reg = re.compile(CR_REG)
    col_match = cr_reg.match(fn)
    if col_match is None:
        log.error("Couldn't get col information from ll2cr file")
        return None
    d = col_match.groupdict()
    d["scans_out"] = int(d["scans_out"])
    d["scan_first"] = int(d["scan_first"])
    d["ll2cr_rowsperscan"] = int(d["ll2cr_rowsperscan"])
    return d

def ll2cr(colsin, scansin, rowsperscan, latfile, lonfile, gpdfile,
        verbose=False, f_scansout=True, rind=None, fill_io=None, tag="ll2cr"):
    args = ["ll2cr"]
    if verbose:
        args.append("-v")
    if f_scansout:
        args.append("-f")
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

    d["ll2cr_rowsperscan"] = col_dict["ll2cr_rowsperscan"]

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

    stem = os.path.splitext(d["cols_filename"])[0]
    stem = stem[:stem.find("cols")] + "cols"
    new_col_fn = stem + ".real4.%d.%d" % (colsin, d["scans_out"] * d["ll2cr_rowsperscan"])
    log.debug("Moving ll2cr cols file '%s' to '%s'", d["cols_filename"], new_col_fn)
    os.rename(d["cols_filename"], new_col_fn)
    d["cols_filename"] = new_col_fn

    stem = os.path.splitext(d["rows_filename"])[0]
    stem = stem[:stem.find("rows")] + "rows"
    new_row_fn = stem + ".real4.%d.%d" % (colsin, d["scans_out"] * d["ll2cr_rowsperscan"])
    log.debug("Moving ll2cr rows file '%s' to '%s'", d["rows_filename"], new_row_fn)
    os.rename(d["rows_filename"], new_row_fn)
    d["rows_filename"] = new_row_fn

    log.debug("Number of Scans Out = %d" % d["scans_out"])
    log.debug("Number for Scan First = %d" % d["scan_first"])
    log.debug("Number of Rows Per Scan = %d" % d["ll2cr_rowsperscan"])

    return d

def fornav(chan_count, swath_cols, swath_scans, swath_rows_per_scan, colfile, rowfile, swathfile, grid_cols, grid_rows, output_fn,
        verbose=False, swath_data_type_1=None, swath_fill_1=None, grid_fill_1=None, weight_delta_max=None, weight_distance_max=None,
        start_scan=None, select_single_samples=False):
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
    
    if select_single_samples:
        # the -m argument tells fornav to select only the highest weighted
        # sample point, rather than doing a weighted average
        args.append("-m")
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
        elif isinstance(swath_fill_1, list):
            args.append(swath_fill_1[0])
        else:
            args.append(swath_fill_1)
    if grid_fill_1 is not None:
        args.append("-F")
        if chan_count > 1 and not isinstance(grid_fill_1, list):
            args.extend(["%f" % grid_fill_1]*chan_count)
        elif chan_count > 1:
            args.extend(grid_fill_1)
        elif isinstance(grid_fill_1, list):
            args.append(grid_fill_1[0])
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

        # Check to make sure fornav actually created the files
        for o_fn in output_fn:
            if not os.path.exists(o_fn):
                log.error("Couldn't find fornav output file '%s'" % o_fn)
                raise RuntimeError("Couldn't find fornav output file '%s'" % o_fn)
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
