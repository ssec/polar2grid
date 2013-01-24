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
from polar2grid.modis import GEO_FILE_GROUPING

from polar2grid.modis import Frontend

from .util_glue_functions import *
from .remap import remap_bands
from .awips import Backend

import os
import sys
import re
import logging
from multiprocessing import Process
import numpy
from glob import glob
from collections import defaultdict

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
    
    list_to_remove = ["latitude*.real4.*", "longitude*.real4.*",
                      "image*.real4.*", "btimage*.real4.*",
                      "bt_prescale*.real4.*", "cloud_cleared*.real4.*",
                      "ll2cr_*.img",
                      "result*.real4.*",
                      "SSEC_AWIPS_MODIS*" ]
    
    remove_products(list_to_remove)

def process_data_sets(filepaths,
                      nav_uid,
                      fornav_D=None, fornav_d=None,
                      fornav_m=True,
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
    
    status_to_return = STATUS_SUCCESS
    
    # create the front and backend objects
    # these calls should load any configuration files needed
    frontend_object = Frontend()
    backend_object  = Backend(rescale_config=rescale_config, backend_config=backend_config)
    
    # Extract Swaths
    log.info("Extracting swaths...")
    meta_data = { }
    try:
        meta_data = frontend_object.make_swaths(filepaths, cut_bad=True, nav_uid=nav_uid, create_fog=create_pseudo)
    except StandardError:
        log.error("Swath creation failed")
        log.debug("Swath creation error:", exc_info=1)
        status_to_return |= STATUS_FRONTEND_FAIL
    
    # if we weren't able to load any of the swaths... stop now
    if len(meta_data.keys()) <= 0 :
        log.error("Unable to load swaths for any of the bands, quitting...")
        return status_to_return or STATUS_UNKNOWN_FAIL
    
    # for convenience, pull some things out of the meta data
    sat = meta_data["sat"]
    instrument = meta_data["instrument"]
    start_time = meta_data["start_time"]
    band_info = meta_data["bands"]
    flatbinaryfilename_lat = meta_data["fbf_lat"]
    flatbinaryfilename_lon = meta_data["fbf_lon"]
    
    log.debug("band_info after prescaling: " + str(band_info.keys()))
    
    # Determine grids
    try:
        log.info("Determining what grids the data fits in...")
        grid_jobs = create_grid_jobs(sat, instrument, band_info, flatbinaryfilename_lat, flatbinaryfilename_lon,
                                     backend_object, forced_grids=forced_grid)
    except StandardError:
        log.debug("Grid Determination error:", exc_info=1)
        log.error("Determining data's grids failed")
        status_to_return |= STATUS_GDETER_FAIL
        return status_to_return
    
    ### Remap the data
    try:
        remapped_jobs = remap_bands(sat, instrument, nav_uid,
                flatbinaryfilename_lon, flatbinaryfilename_lat, grid_jobs,
                num_procs=num_procs, fornav_d=fornav_d, fornav_D=fornav_D,
                lat_fill_value=meta_data.get("lat_fill_value", None),
                lon_fill_value=meta_data.get("lon_fill_value", None),
                do_single_sample=fornav_m, 
                )
    except StandardError:
        log.debug("Remapping Error:", exc_info=1)
        log.error("Remapping data failed")
        status_to_return |= STATUS_REMAP_FAIL
        return status_to_return
    
    ### BACKEND ###
    W = Workspace('.')
    # for each grid
    for grid_name, grid_dict in remapped_jobs.items():
        
        # process each band for this grid
        for band_kind, band_id in grid_dict.keys():
            
            band_dict = grid_dict[(band_kind, band_id)]
            
            log.info("Running AWIPS backend for %s%s band grid %s" % (band_kind, band_id, grid_name))
            try:
                # Get the data from the flat binary file
                data = getattr(W, band_dict["fbf_remapped"].split(".")[0]).copy()
                
                # Call the backend
                backend_object.create_product(
                                            sat,
                                            instrument,
                                            band_kind,
                                            band_id,
                                            band_dict["data_kind"],
                                            data,
                                            start_time=start_time,
                                            grid_name=grid_name,
                                            ncml_template=forced_nc or None,
                                            fill_value=band_dict.get("fill_value", None)
                                            )
            except StandardError:
                log.error("Error in the AWIPS backend for %s%s in grid %s" % (band_kind, band_id, grid_name))
                log.debug("AWIPS backend error:", exc_info=1)
                del remapped_jobs[grid_name][(band_kind, band_id)]
        
        # if all the jobs for a grid failed, warn the user and take that grid off the list
        if len(remapped_jobs[grid_name]) == 0 :
            log.error("All backend jobs for grid %s failed" % (grid_name,))
            del remapped_jobs[grid_name]
    
    # if remapping failed for all grids, warn the user
    if len(remapped_jobs) == 0:
        log.warning("AWIPS backend failed for all grids in this data set")
        status_to_return |= STATUS_BACKEND_FAIL
    
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
                    multiprocess=True,
                    **kwargs):
    """Go through the motions of converting
    a MODIS hdf file into a AWIPS NetCDF file.
    
    1.  modis_guidebook.py       : Info on what's in the files
    2.  modis_to_swath.py        : Code to load the data
    3.  Clear clouds             : if we have the cloud mask data, clear any cloud cleared bands
    4.  Convert BT               : (in to_swath) converts IR channels to brightness temps
    5.  Create Fog band          : if we have the appropriate bands, create the bt difference for fog
    6.  create_grid_jobs         : Figure out what grids the data fits in
    7.  ll2cr
    8.  fornav
    9.  rescale.py
    10. awips_netcdf.py
    """
    # Rewrite/force parameters to specific format
    filepaths = [ os.path.abspath(os.path.expanduser(x)) for x in sorted(filepaths) ]
    
    # separate these by the MODIS types
    nav_file_type_sets = defaultdict(dict)
    all_used           = set([ ])
    # for each of the possible navigation types
    for nav_file_pattern_key in GEO_FILE_GROUPING.keys() :
        # for each file pattern that uses that navigation type
        for file_pattern in GEO_FILE_GROUPING[nav_file_pattern_key] :
            # add the files matching that pattern to the appropriate set
            nav_file_type_sets[nav_file_pattern_key][file_pattern] = set([ ]) if file_pattern not in nav_file_type_sets[nav_file_pattern_key] else nav_file_type_sets[nav_file_pattern_key][file_pattern]
            nav_file_type_sets[nav_file_pattern_key][file_pattern].update(set([ x for x in filepaths if re.match(file_pattern, os.path.split(x)[1]) ]))
            all_used.update(nav_file_type_sets[nav_file_pattern_key][file_pattern]) # keep a running set of all the files we've found matching nav files for
    all_provided = set(filepaths)
    not_used = all_provided - all_used
    if len(not_used):
        log.warning("Didn't know what to do with\n%s" % "\n".join(list(not_used)))
    
    # some things that we'll use later for clean up
    processes_to_wait_for = defaultdict(list)
    exit_status           = 0
    
    # go through and process each of our file sets by navigation type
    for geo_nav_key in nav_file_type_sets.keys() :
        log.debug("Processing files for %s navigation" % geo_nav_key)
        
        temp_files_for_this_nav = nav_file_type_sets[geo_nav_key]
        try:
            if multiprocess:
                temp_processes = Process(target=_process_data_sets,
                                         args = (temp_files_for_this_nav, geo_nav_key),
                                         kwargs = kwargs
                                         )
                temp_processes.start()
                processes_to_wait_for[geo_nav_key].append(temp_processes)
            else:
                stat = _process_data_sets(temp_files_for_this_nav, geo_nav_key **kwargs)
                exit_status = exit_status or stat
        except StandardError:
            log.error("Could not process files for %s navigation" % geo_nav_key)
            exit_status = exit_status or len(temp_files_for_this_nav)
    
    log.debug("Waiting for subprocesses")
    # look through our processes and wait for any processes we saved to wait for
    for geo_nav_key in processes_to_wait_for.keys() :
        for each_process in processes_to_wait_for[geo_nav_key] :
            each_process.join()
            stat = each_process.exitcode
            exit_status = exit_status or stat
    
    return exit_status

def main():
    import argparse
    description = """
    Create MODIS swaths, remap them to a grid, and place that remapped data
    into a AWIPS compatible netcdf file.
    """
    
    parser = argparse.ArgumentParser(description=description)
    
    # Logging related
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
            help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    
    # Multiprocessing related
    parser.add_argument('--sp', dest='single_process', default=False, action='store_true',
            help="Processing is sequential instead of one process per navigation group")
    parser.add_argument('--num-procs', dest="num_procs", default=1,
            help="Specify number of processes that can be used to run ll2cr/fornav calls in parallel")
    
    # Input related
    parser.add_argument('-f', dest='get_files', default=False, action="store_true",
            help="Specify that hdf files are listed, not a directory")
    parser.add_argument('data_files', nargs="+",
            help="Data directory where satellite data is stored or list of data filenames if '-f' is specified")
    
    # Frontend and product filtering related
    parser.add_argument('--no-pseudo', dest='create_pseudo', default=True, action='store_false',
            help="Don't create pseudo bands")
    
    # Remapping and grid related
    parser.add_argument('-D', dest='fornav_D', default=5,
            help="Specify the -D option for fornav")
    parser.add_argument('-d', dest='fornav_d', default=1,
            help="Specify the -d option for fornav")
    parser.add_argument('-m', dest='fornav_m', default=False, action='store_true',
            help="Specify the -m option for fornav")
    parser.add_argument('-g', '--grids', dest='forced_grids', nargs="+", default="all",
            help="Force remapping to only some grids, defaults to 'all', use 'all' for determination")
    parser.add_argument('--gpd', dest='forced_gpd', default=None,
            help="Specify a different gpd file to use")
    
    # Backend related
    parser.add_argument('--rescale-config', dest='rescale_config', default=None,
            help="specify alternate rescale configuration file")
    parser.add_argument('--backend-config', dest='backend_config', default=None,
            help="specify alternate backend configuration file")
    
    # Output file related
    parser.add_argument('-k', '--keep', dest='remove_prev', default=True, action='store_true',
            help="Don't delete any files that were previously made (WARNING: processing may not run successfully)")
    parser.add_argument('--nc', dest='forced_nc', default=None,
            help="Specify a different nc file to use")
    
    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(LOG_FN, console_level=levels[min(3, args.verbosity)])
    
    # Don't set this up until after you have setup logging
    sys.excepthook = exc_handler
    
    fornav_D = int(args.fornav_D)
    fornav_d = int(args.fornav_d)
    fornav_m = args.fornav_m
    num_procs = int(args.num_procs)
    forced_grids = args.forced_grids
    if forced_grids == 'all': forced_grids = None
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
        hdf_files = [ os.path.join(base_dir,x) for x in os.listdir(base_dir) if x.endswith(".hdf") ]
    else:
        log.error("Wrong number of arguments")
        parser.print_help()
        return -1
    
    if args.remove_prev:
        log.debug("Removing any previous files")
        clean_up_files()
    
    stat = run_modis2awips(hdf_files,
                fornav_D=fornav_D, fornav_d=fornav_d, fornav_m=fornav_m,
                forced_gpd=args.forced_gpd, forced_nc=args.forced_nc,
                forced_grid=forced_grids,
                create_pseudo=args.create_pseudo,
                rescale_config=args.rescale_config,
                backend_config=args.backend_config,
                multiprocess=not args.single_process, num_procs=num_procs)
    
    return stat

if __name__ == "__main__":
    sys.exit(main())

