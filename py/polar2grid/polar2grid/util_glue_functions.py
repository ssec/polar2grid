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
from .rescale import dnb_scale
from .grids.grids import determine_grid_coverage_fbf,get_grid_info
from .awips import can_handle_inputs as awips_can_handle_inputs

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
def create_grid_jobs(sat, instrument, bands, fbf_lat, fbf_lon,
        forced_grids=None, can_handle_inputs=awips_can_handle_inputs, 
        log=logging.getLogger('')):
    """
    TODO, documentation
    """
    
    # Check what grids the backend can handle
    all_possible_grids = set()
    for band_kind, band_id in bands.keys():
        this_band_can_handle = can_handle_inputs(sat, instrument, band_kind, band_id, bands[(band_kind, band_id)]["data_kind"])
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

def run_DNB_prescaling(img_filepath, mode_filepath,
                       high_angle_limit=TERMINATOR_HIGH_ANGLE_LIMIT, low_angle_limit=TERMINATOR_LOW_ANGLE_LIMIT,
                       fill_value=-999.0,
                       log=logging.getLogger('')):
    """A wrapper function for calling the prescaling function for dnb.
    This function will read the binary image data from ``img_filepath``
    as well as any other data that may be required to prescale the data
    correctly, such as day/night/twilight masks.

    :Parameters:
        img_filepath : str
            Filepath to the binary image swath data in FBF format
            (ex. ``image_I01.real4.6400.10176``).
        mode_filepath : str
            Filepath to the binary mode swath data in FBF format
            (ex. ``mode_I01.real4.6400.10176``).
    """
        
    img_attr = os.path.split(img_filepath)[1].split('.')[0]
    mode_attr = os.path.split(mode_filepath)[1].split('.')[0]

    # Rescale the image
    try:
        W = Workspace('.')
        img = getattr(W, img_attr)
        data = img.copy()
        log.debug("Data min: %f, Data max: %f" % (data.min(),data.max()))
    except StandardError:
        log.error("Could not open img file %s" % img_filepath)
        log.debug("Files matching %r" % glob(img_attr + "*"))
        raise

    scale_kwargs = {}
    try:
        mode_mask = getattr(W, mode_attr)
        # Only add parameters if they're useful
        if mode_mask.shape == data.shape:
            log.debug("Adding mode mask to rescaling arguments")
            HIGH = high_angle_limit
            LOW  = low_angle_limit
            MIXED_STEP = HIGH - LOW
            good_mask = ~((img == fill_value) | (mode_mask == fill_value))
            scale_kwargs["night_mask"]    = (mode_mask >= HIGH) & good_mask
            scale_kwargs["day_mask"]      = (mode_mask <= LOW ) & good_mask
            scale_kwargs["mixed_mask"] = []
            steps = range(LOW, HIGH+1, MIXED_STEP)
            if steps[-1] >= HIGH: steps[-1] = HIGH
            steps = zip(steps, steps[1:])
            for i,j in steps:
                log.debug("Processing step %d to %d" % (i,j))
                tmp = (mode_mask >  i) & (mode_mask < j) & good_mask
                if numpy.sum(tmp) > 0:
                    log.debug("Adding step %d to %d" % (i,j))
                    scale_kwargs["mixed_mask"].append(tmp)
                del tmp
            del good_mask

        else:
            log.error("Mode shape is different than the data's shape (%s) vs (%s)" % (mode_mask.shape, data.shape))
            raise ValueError("Mode shape is different than the data's shape (%s) vs (%s)" % (mode_mask.shape, data.shape))
    except StandardError:
        log.error("Could not open mode mask file %s" % mode_filepath)
        log.debug("Files matching %r" % glob(mode_attr + "*"))
        raise

    try:
        rescaled_data = dnb_scale(data,
                **scale_kwargs)
        log.debug("Data min: %f, Data max: %f" % (rescaled_data.min(),rescaled_data.max()))
        rows,cols = rescaled_data.shape
        fbf_swath_var = "prescale_dnb"
        fbf_swath = "./%s.real4.%d.%d" % (fbf_swath_var, cols, rows)
        rescaled_data.tofile(fbf_swath)
    except StandardError:
        log.error("Unexpected error while rescaling data")
        log.debug("Rescaling error:", exc_info=1)
        raise

    return fbf_swath

def create_viirs_fog_pseudobands(kind, bands,
                                 high_angle_limit=TERMINATOR_HIGH_ANGLE_LIMIT,
                                 fill_value=-999.0,
                                 log=logging.getLogger('')):
    """
    TODO documentation
    """
    
    # Fog pseudo-band
    if (kind == BKIND_I) and (BID_05 in bands) and (BID_04 in bands):
        log.info("Creating IFOG pseudo band...")
        try:
            W = Workspace('.')
            mode_attr = bands[BID_05]["fbf_mode"].split(".")[0]
            mode_data = getattr(W, mode_attr)
            night_mask = mode_data >= high_angle_limit
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
                "kind" : "I",
                "band" : "FOG",
                "band_name" : "IFOG",
                "data_kind" : DKIND_FOG,
                "remap_data_as"  : DKIND_BTEMP,
                "rows_per_scan" : bands[BID_05]["rows_per_scan"],
                "fbf_img" : "image_IFOG.%s" % ".".join(bands[BID_05]["fbf_img"].split(".")[1:]),
                "fbf_mode" : bands[BID_05]["fbf_mode"],
                "swath_scans" : bands[BID_05]["swath_scans"],
                "swath_rows" : bands[BID_05]["swath_rows"],
                "swath_cols" : bands[BID_05]["swath_cols"]
                }
        try:
            W = Workspace(".")
            i5_attr = bands[BID_05]["fbf_img"].split(".")[0]
            i4_attr = bands[BID_04]["fbf_img"].split(".")[0]
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
            bands[BID_FOG] = fog_dict
        except StandardError:
            log.error("Error creating Fog pseudo band")
            log.debug("Fog creation error:", exc_info=1)

if __name__=='__main__':
    import doctest
    doctest.testmod()