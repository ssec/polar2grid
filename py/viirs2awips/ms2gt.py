"""Simple python wrapper around the actual shell calls to
ms2gt utilities.

Author: David Hoese,davidh,SSEC
"""
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
        args.extend(["-F", "%d" % fill_io[0], "%d" % fill_io[1]])
    args.extend([colsin, scansin, rowsperscan, latfile, lonfile, gpdfile])
    if tag:
        args.append(tag)

    try:
        args = [ str(a) for a in args ]
        log.debug("Running ll2cr with %r" % args)
        check_call(args)
    except CalledProcessError:
        log.error("Error running ll2cr", exc_info=1)
        return None

    d = {}
    tmp = glob("%s_cols_*.img" % tag)
    if len(tmp) != 1:
        log.error("Couldn't find cols img file from ll2cr")
        return None
    d["colfile"] = tmp[0]
    log.debug("Columns file is %s" % d["colfile"])

    tmp = glob("%s_rows_*.img" % tag)
    if len(tmp) != 1:
        log.error("Couldn't find rows img file from ll2cr")
        return None
    d["rowfile"] = tmp[0]
    log.debug("Rows file is %s" % d["rowfile"])

    col_dict = _ll2cr_cols_info(d["colfile"])
    row_dict = _ll2cr_rows_info(d["rowfile"])
    if col_dict is None or row_dict is None:
        # Log message was delivered before
        return None

    d["num_cols"] = col_dict["num_cols"]
    d["num_rows"] = row_dict["num_rows"]

    if col_dict["scans_out"] != row_dict["scans_out"]:
        log.error("ll2cr didn't produce the same number of scans for cols and rows")
        return None
    d["scans_out"] = col_dict["scans_out"]

    if col_dict["scan_first"] != row_dict["scan_first"]:
        log.error("ll2cr didn't produce the same number for scan first cols and rows")
        return None
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
    if verbose:
        args.append("-v")
    if swath_data_type_1:
        args.extend(["-t", "%s" % swath_data_type_1])
    if swath_fill_1 is not None:
        args.extend(["-f", "%f" % swath_fill_1])
    if grid_fill_1 is not None:
        args.extend(["-F", "%d" % grid_fill_1])
    if weight_delta_max is not None:
        args.extend(["-D", "%d" % weight_delta_max])
    if weight_distance_max is not None:
        args.extend(["-d", "%d" % weight_distance_max])
    if start_scan is not None:
        args.extend(["-s", "%d" % start_scan[0], "%d" % start_scan[1]])

    args.extend([swath_cols, swath_scans, swath_rows_per_scan, colfile, rowfile, swathfile, grid_cols, grid_rows, output_fn])

    try:
        args = [ str(a) for a in args ]
        log.debug("Running fornav with %r" % args)
        check_call(args)
    except CalledProcessError:
        log.error("Error running fornav", exc_info=1)
        return None

    d = {}
    return d

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print "No scripting implemented"
    sys.exit(0)
