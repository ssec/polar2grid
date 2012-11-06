#!/usr/bin/env python
# encoding: utf-8
"""Script that uses the `polar2grid` toolbox of modules to take MODIS
hdf4 (.hdf) files and create a properly scaled AWIPS compatible NetCDF file.

:author:       Eva Schiffer (evas)
:contact:      eva.schiffer@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Oct 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from polar2grid.core import Workspace
from polar2grid.core.constants import *
from polar2grid.modis import make_swaths
from polar2grid.modis import VIS_INF_FILE_PATTERN
from .util_glue_functions import *
from .remap import remap_bands # TODO, is this needed?
from .awips import can_handle_inputs,backend,load_config as load_backend_config

import os
import sys
import re
import logging
from multiprocessing import Process
import numpy
from glob import glob

# Status Constants

# processing successful
SUCCESS = 0
# Swath extraction failed
SWATH_FAIL = 2
# Swath prescaling failed
PRESCALE_FAIL = 4
# ll2cr failed
LL2CR_FAIL = 8
# fornav failed
FORNAV_FAIL = 16
# remap failed
REMAP_FAIL = 24 # ll2cr and fornav
# backend failed
BACKEND_FAIL = 32
# grid determination failed
GDETER_FAIL = 64
# there aren't any jobs left, not sure why
UNKNOWN_FAIL = -1

log = logging.getLogger(__name__)
LOG_FN = os.environ.get("MODIS2AWIPS_LOG", "./modis2awips.log")

def exc_handler(exc_type, exc_value, traceback):
    """An execption handler/hook that will only be called if an exception
    isn't called.  This will save us from print tracebacks or unrecognizable
    errors to the user's console.

    Note, however, that this doesn't effect code in a separate process as the
    exception never gets raised in the parent.
    """
    logging.getLogger(__name__).error(exc_value)
    logging.getLogger('traceback').error(exc_value, exc_info=(exc_type,exc_value,traceback))

def clean_up_files():
    """Remove as many of the possible files that were created from a previous
    run of this script, including temporary files.

    :note:
        This does not remove the log file because it requires the log file
        to report what's being removed.
    """
    
    # TODO revise this list
    list_to_remove = [ ".lat*", ".lon*", ".image*",
                      "latitude*.real4.*", "longitude*.real4.*",
                      "image*.real4.*",
                      "prescale_*.real4.*", "ll2cr_*.real4.*",
                      "result*.real4.*",
                      "SSEC_AWIPS_MODIS*" ]
    
    remove_products(list_to_remove)

# TODO, revise parameters
def process_data_sets(filepaths,
                      fornav_D=None, fornav_d=None,
                      forced_grid=None,
                      forced_gpd=None, forced_nc=None,
                      create_pseudo=True,
                      num_procs=1,
                      rescale_config=None,
                      backend_config=None
                      ) :
    """Process all the files provided from start to finish,
    from filename to AWIPS NC file.
    
    Note: all files provided are expected to share a navigation source.
    """
    
    status_to_return = SUCCESS
    
    # Load any configuration files needed
    # XXX: Fix this by using object orientated components
    load_backend_config(backend_config) # default
    
    # Extract Swaths
    log.info("Extracting swaths...")
    try:
        meta_data = make_swaths(filepaths, cut_bad=True)
    except StandardError:
        log.error("Swath creation failed")
        log.debug("Swath creation error:", exc_info=1)
        status_to_return |= SWATH_FAIL
        return status_to_return
    sat = meta_data["sat"]
    instrument = meta_data["instrument"]
    start_time = meta_data["start_time"]
    band_info = meta_data["bands"]
    flatbinaryfilename_lat = meta_data["fbf_lat"]
    flatbinaryfilename_lon = meta_data["fbf_lon"]
    
    """ TODO, something like this will be needed for fog
    # Create pseudo-bands
    try:
        if create_pseudo:
            create_pseudobands(kind, bands)
    except StandardError:
        log.error("Pseudo band creation failed")
        log.debug("Pseudo band error:", exc_info=1)
        status_to_return |= SWATH_FAIL
        return status_to_return
    """
    
    """ TODO we may need prescaling of some kind in the future, but not yet
    # Do any pre-remapping rescaling
    for band, band_job in bands.items():
        if kind != BKIND_DNB:
            # It takes too long to read in the data, so just skip it
            band_job["fbf_swath"] = band_job["fbf_img"]
            continue
        
        log.info("Prescaling data before remapping...")
        try:
            fbf_swath = run_prescaling(
                    band_job["fbf_img"],
                    band_job["fbf_mode"]
                    )
            band_job["fbf_swath"] = fbf_swath
        except StandardError:
            log.error("Unexpected error prescaling %s, removing..." % band_job["band_name"])
            log.debug("Prescaling error:", exc_info=1)
            del bands[band]
            status_to_return |= PRESCALE_FAIL
    """
    
    if len(band_info) == 0:
        log.error("No more bands to process, quitting...")
        return status_to_return or UNKNOWN_FAIL
    
    # Determine grids
    try:
        log.info("Determining what grids the data fits in...")
        grid_jobs = create_grid_jobs(sat, instrument, band_info, flatbinaryfilename_lat, flatbinaryfilename_lon,
                forced_grids=forced_grid, can_handle_inputs=can_handle_inputs)
    except StandardError:
        log.debug("Grid Determination error:", exc_info=1)
        log.error("Determining data's grids failed")
        status_to_return |= GDETER_FAIL
        return status_to_return
    
    
    ### Remap the data
    try:
        remapped_jobs = remap_bands(sat, instrument, "geo_nav",
                flatbinaryfilename_lon, flatbinaryfilename_lat, grid_jobs,
                num_procs=num_procs, fornav_d=fornav_d, fornav_D=fornav_D,
                lat_min=meta_data.get("lat_min", None),
                lat_max=meta_data.get("lat_max", None),
                lon_min=meta_data.get("lon_min", None),
                lon_max=meta_data.get("lon_max", None)
                )
    except StandardError:
        log.debug("Remapping Error:", exc_info=1)
        log.error("Remapping data failed")
        status_to_return |= REMAP_FAIL
        return status_to_return
    
    ### BACKEND ###
    W = Workspace('.')
    for grid_name, grid_dict in remapped_jobs.items():
        
        #print ("grid_dict: " + str(grid_dict))
        
        for band_kind, band_id in grid_dict.keys():
            
            band_dict = grid_dict[(band_kind, band_id)]
            
            log.info("Running AWIPS backend for %s%s band grid %s" % (band_kind, band_id, grid_name))
            try:
                # Get the data from the flat binary file
                data = getattr(W, band_dict["fbf_remapped"].split(".")[0]).copy()
                
                # Call the backend
                backend(
                        sat,
                        instrument,
                        band_kind,
                        band_id,
                        band_dict["data_kind"],
                        data,
                        start_time=start_time,
                        grid_name=grid_name,
                        ncml_template=forced_nc or None,
                        rescale_config=rescale_config,
                        backend_config=backend_config
                        )
            except StandardError:
                log.error("Error in the AWIPS backend for %s%s in grid %s" % (band_kind, band_id, grid_name))
                log.debug("AWIPS backend error:", exc_info=1)
                del remapped_jobs[grid_name][(band_kind, band_id)]
        
        if len(remapped_jobs[grid_name]) == 0:
            log.error("All backend jobs for grid %s failed" % (grid_name,))
            del remapped_jobs[grid_name]
    
    if len(remapped_jobs) == 0:
        log.warning("AWIPS backend failed for all grids in this data set")
        status_to_return |= BACKEND_FAIL
    
    log.info("Processing of data set is complete")
    
    return status_to_return

def _process_data_sets(*args, **kwargs):
    """Wrapper function around `process_data_sets` so that it can called
    properly from `run_modis2awips`, where the exitcode is the actual
    returned value from `process_data_sets`.

    This function also checks for exceptions other than the ones already
    checked for in `process_data_sets` so that they are
    recorded properly.
    """
    try:
        stat = process_data_sets(*args, **kwargs)
        sys.exit(stat)
    except MemoryError:
        log.error("modis2awips ran out of memory, check log file for more info")
        log.debug("Memory error:", exc_info=1)
    except OSError:
        log.error("modis2awips had a OS error, check log file for more info")
        log.debug("OS error:", exc_info=1)
    except StandardError:
        log.error("modis2awips had an unexpected error, check log file for more info")
        log.debug("Unexpected/Uncaught error:", exc_info=1)
    except KeyboardInterrupt:
        log.info("modis2awips was cancelled by a keyboard interrupt")
    
    sys.exit(-1)

def run_modis2awips(filepaths,
                    multiprocess=False, # TODO, turn this on later
                    **kwargs):
    """Go through the motions of converting
    a MODIS hdf file into a AWIPS NetCDF file.
    
    TODO, change this to reflect what's actually being done
    1. viirs_guidebook.py       : Get file info/data
    2. viirs_imager_to_swath.py : Concatenate data
    3. Prescale DNB
    4. Calculate Grid            : Figure out what grids the data fits in
    5. ll2cr
    6. fornav
    7. rescale.py
    8. awips_netcdf.py
    """
    # Rewrite/force parameters to specific format
    filepaths = [ os.path.abspath(os.path.expanduser(x)) for x in sorted(filepaths) ]
    
    # separate these by the MODIS types
    vis_inf_files = sorted(set([ x for x in filepaths if re.match(VIS_INF_FILE_PATTERN ,os.path.split(x)[1]) ]))
    all_used = set(vis_inf_files)
    all_provided = set(filepaths)
    not_used = all_provided - all_used
    if len(not_used):
        log.warning("Didn't know what to do with\n%s" % "\n".join(list(not_used)))
    
    #print ("visible and infrared files: " + str(vis_inf_files))
    
    visible_and_infrared_processes = None
    exit_status = 0
    if len(vis_inf_files) > 0 :
        log.debug("Processing visible and infrared files")
        try:
            if multiprocess:
                visible_and_infrared_processes = Process(target=_process_data_sets,
                                                         args = (vis_inf_files,),
                                                         kwargs = kwargs
                                                         )
                visible_and_infrared_processes.start()
            else:
                stat = _process_data_sets(vis_inf_files, **kwargs)
                exit_status = exit_status or stat
        except StandardError:
            log.error("Could not process visible and infrared files")
            exit_status = exit_status or len(vis_inf_files)
    
    log.debug("Waiting for subprocesses")
    if visible_and_infrared_processes is not None:
        visible_and_infrared_processes.join()
        stat = visible_and_infrared_processes.exitcode
        exit_status = exit_status or stat
    
    return exit_status

def main():
    import argparse
    description = """
    Create MODIS swaths, remap them to a grid, and place that remapped data
    into a AWIPS compatible netcdf file.
    """
    description2 = """
    For DB:
    %prog [options] <event directory>
    
    For testing (usable files are those of bands mentioned in templates.conf):
    # Looks for all usable files in data directory
    %prog [options] <data directory>
    # Uses all usable files of the specfied
    %prog [options] -f file1.hdf file2.hdf ...
    """
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
            help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument('-D', dest='fornav_D', default=40,
            help="Specify the -D option for fornav")
    parser.add_argument('-d', dest='fornav_d', default=2,
            help="Specify the -d option for fornav")
    parser.add_argument('-f', dest='get_files', default=False, action="store_true",
            help="Specify that hdf files are listed, not a directory")
    parser.add_argument('-g', '--grids', dest='forced_grids', nargs="+",
            help="Force remapping to only some grids, defaults to 'wgs84_fit', use 'all' for determination")
    parser.add_argument('--sp', dest='single_process', default=False, action='store_true',
            help="Processing is sequential instead of one process per navigation group")
    parser.add_argument('--num-procs', dest="num_procs", default=1,
            help="Specify number of processes that can be used to run ll2cr/fornav calls in parallel")
    parser.add_argument('-k', '--keep', dest='remove_prev', default=True, action='store_true',
            help="Don't delete any files that were previously made (WARNING: processing may not run successfully)")
    #parser.add_argument('--no-pseudo', dest='create_pseudo', default=True, action='store_false',
    #        help="Don't create pseudo bands")
    parser.add_argument('--rescale-config', dest='rescale_config', default=None,
            help="specify alternate rescale configuration file")
    parser.add_argument('--gpd', dest='forced_gpd', default=None,
            help="Specify a different gpd file to use")
    parser.add_argument('--nc', dest='forced_nc', default=None,
            help="Specify a different nc file to use")
    parser.add_argument('--backend-config', dest='backend_config', default=None,
            help="specify alternate backend configuration file")

    parser.add_argument('data_files', nargs="+",
            help="Data directory where satellite data is stored or list of data filenames if '-f' is specified")
    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(LOG_FN, console_level=levels[min(3, args.verbosity)])

    # Don't set this up until after you have setup logging
    sys.excepthook = exc_handler

    fornav_D = int(args.fornav_D)
    fornav_d = int(args.fornav_d)
    num_procs = int(args.num_procs)
    forced_grids = args.forced_grids
    if args.forced_gpd is not None and not os.path.exists(args.forced_gpd):
        log.error("Specified gpd file does not exist '%s'" % args.forced_gpd)
        return -1
    if args.forced_nc is not None and not os.path.exists(args.forced_nc):
        log.error("Specified nc file does not exist '%s'" % args.forced_nc)
        return -1

    if "help" in args.data_files:
        parser.print_help()
        sys.exit(0)
    elif "remove" in args.data_files:
        log.debug("Removing previous products")
        clean_up_files()
        sys.exit(0)

    if args.get_files:
        hdf_files = args.data_files[:]
    elif len(args.data_files) == 1:
        base_dir = os.path.abspath(os.path.expanduser(args[0]))
        hdf_files = [ os.path.join(base_dir,x) for x in os.listdir(base_dir) if x.startswith("SV") and x.endswith(".h5") ]
    else:
        log.error("Wrong number of arguments")
        parser.print_help()
        return -1

    if args.remove_prev:
        log.debug("Removing any previous files")
        clean_up_files()

    stat = run_modis2awips(hdf_files, fornav_D=fornav_D, fornav_d=fornav_d,
                forced_gpd=args.forced_gpd, forced_nc=args.forced_nc, forced_grid=forced_grids,
                create_pseudo=False, # TODO args.create_pseudo,
                rescale_config=args.rescale_config,
                backend_config=args.backend_config,
                multiprocess=not args.single_process, num_procs=num_procs)

    return stat

if __name__ == "__main__":
    sys.exit(main())

