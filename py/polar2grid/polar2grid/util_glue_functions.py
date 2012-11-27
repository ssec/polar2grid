#!/usr/bin/env python
# encoding: utf-8
"""Some functions that the glue scripts may use (separated form viirs2awips).

:author:       David Hoese (davidh)
:author:       Eva Schiffer (evas)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Oct 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from polar2grid.core import Workspace
from polar2grid.core.constants import *
from .grids.grids import determine_grid_coverage_fbf,get_grid_info

import os
import sys
import logging
import numpy
from glob import glob

TERMINATOR_HIGH_ANGLE_LIMIT = 100
TERMINATOR_LOW_ANGLE_LIMIT  = 88

def setup_logging(log_fn, console_level=logging.INFO):
    """Setup the logger to the console to the logging level defined in the
    command line (default INFO).  Sets up a file logging for everything,
    regardless of command line level specified.  Adds extra logger for
    tracebacks to go to the log file if the exception is caught.  See
    `exc_handler` for more information.

    :Keywords:
        console_level : int
            Python logging level integer (ex. logging.INFO).
    """
    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.DEBUG)

    # Console output is minimal
    console = logging.StreamHandler(sys.stderr)
    console_format = "%(levelname)-8s : %(message)s"
    console.setFormatter(logging.Formatter(console_format))
    console.setLevel(console_level)
    root_logger.addHandler(console)

    # Log file messages have a lot more information
    file_handler = logging.FileHandler(log_fn)
    file_format = "[%(asctime)s] : %(levelname)-8s : %(name)s : %(funcName)s : %(message)s"
    file_handler.setFormatter(logging.Formatter(file_format))
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # Make a traceback logger specifically for adding tracebacks to log file
    traceback_log = logging.getLogger('traceback')
    traceback_log.propagate = False
    traceback_log.setLevel(logging.ERROR)
    traceback_log.addHandler(file_handler)

def _glob_file(pattern, log=logging.getLogger('')):
    """Globs for a single file based on the provided pattern.

    :raises ValueError: if more than one file matches pattern
    """
    tmp = glob(pattern)
    if len(tmp) != 1:
        log.error("There were no files or more than one fitting the pattern %s" % pattern)
        raise ValueError("There were no files or more than one fitting the pattern %s" % pattern)
    return tmp[0]

def _force_symlink(dst, linkname):
    """Create a symbolic link named `linkname` pointing to `dst`.  If the
    symbolic link already exists, remove it and create the new one.

    :Parameters:
        dst : str
            Filename to be pointed to.
        linkname : str
            Filename of the symbolic link being created or overwritten.
    """
    if os.path.exists(linkname):
        log.info("Removing old file %s" % linkname)
        os.remove(linkname)
    log.debug("Symlinking %s -> %s" % (linkname,dst))
    os.symlink(dst, linkname)

def _safe_remove(fn, log):
    """Remove the file `fn` if you can, if not log an error message,
    but continue on.

    :Parameters:
        fn : str
            Filename of the file to be removed.
    """
    try:
        log.info("Removing %s" % fn)
        os.remove(fn)
    except StandardError:
        log.error("Could not remove %s" % fn)

def remove_products(list_of_file_patterns_to_remove, log=logging.getLogger('')):
    """Remove files that match the patterns in the given list.

    :note:
        This should not be used to remove the long file because
        it requires the log file to report what's being removed.
    """
    
    for file_pattern in list_of_file_patterns_to_remove :
        for file_name in glob(file_pattern) :
            _safe_remove(file_name, log)

# TODO, by default can_handle_inputs runs on awips, is there a more elegant way of doing this?
def create_grid_jobs(sat, instrument, bands, fbf_lat, fbf_lon, backend_object,
        forced_grids=None, log=logging.getLogger('')):
    """
    TODO, documentation
    """
    
    # Check what grids the backend can handle
    all_possible_grids = set()
    for band_kind, band_id in bands.keys():
        this_band_can_handle = backend_object.can_handle_inputs(sat, instrument, band_kind, band_id, bands[(band_kind, band_id)]["data_kind"])
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
        if  bands [(band_kind, band_id)]["grids"] == GRIDS_ANY:
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
            log.debug("Kind %s band %s will be remapped to grid %s" % (band_kind, band_id ,grid_name))
            grid_jobs[grid_name][(band_kind, band_id)] = bands[(band_kind, band_id)].copy()

    if len(grid_jobs) == 0:
        msg = "No backend compatible grids were found to fit the data set"
        log.error(msg)
        raise ValueError(msg)

    return grid_jobs

if __name__=='__main__':
    import doctest
    doctest.testmod()