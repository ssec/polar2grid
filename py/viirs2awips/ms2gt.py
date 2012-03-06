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

def ll2cr(colsin, scansin, rowsperscan, latfile, lonfile, gpdfile,
        verbose=False, f_scansout=None, rind=None, fill_io=None, tag="ll2cr"):
    args = ["ll2cr"]
    if verbose:
        args.append("-v")
    if f_scansout:
        args.extend(["-f", "%d" % f_scansout])
    if rind:
        args.extend(["-r", "%d" % rind])
    if fill_io:
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

    num_cols = cr_reg.match(d["colfile"])
    if num_cols is None:
        log.error("Couldn't find number of cols from ll2cr file")
    d["num_cols"] = int(num_cols.groups()[0])
    log.debug("Number of Columns = %d" % d["num_cols"])

    num_rows = cr_reg.match(d["rowfile"])
    if num_cols is None:
        log.error("Couldn't find number of rows from ll2cr file")
    d["num_rows"] = int(num_rows.groups()[0])
    log.debug("Number of Rows = %d" % d["num_rows"])

    return d

def fornav(chan_count, swath_cols, swath_scans, swath_rows_per_scan, colfile, rowfile, swathfile, grid_cols, grid_rows, output_fn,
        verbose=False, swath_data_type_1=None, swath_fill_1=None, grid_fill_1=None, weight_delta_max=None):
    args = ["fornav", "%d" % chan_count]
    if verbose:
        args.append("-v")
    if swath_data_type_1:
        args.extend(["-t", "%s" % swath_data_type_1])
    if swath_fill_1:
        args.extend(["-f", "%f" % swath_fill_1])
    if grid_fill_1:
        args.extend(["-F", "%d" % grid_fill_1])
    if weight_delta_max:
        args.extend(["-D", "%d" % weight_delta_max])

    args.extend([swath_cols, swath_scans, swath_rows_per_scan, colfile, rowfile, swathfile, grid_cols, grid_rows, output_fn])

    try:
        args = [ str(a) for a in args ]
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
