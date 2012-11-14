#!/usr/bin/env python
# encoding: utf-8
"""Script that uses the `polar2grid` toolbox of modules to take VIIRS
hdf5 (.h5) files and create a properly scaled geotiff file.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from polar2grid.core import Workspace
from polar2grid.core.constants import *
from polar2grid.viirs import Frontend
from .viirs2awips import _safe_remove,create_grid_jobs
from .remap import remap_bands
from .gtiff_backend import Backend,_bits_to_etype

import os
import sys
import logging
from multiprocessing import Process
from glob import glob

log = logging.getLogger(__name__)
LOG_FN = os.environ.get("VIIRS2GTIFF_LOG", "./viirs2gtiff.log")

def setup_logging(console_level=logging.INFO):
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
    file_handler = logging.FileHandler(LOG_FN)
    file_format = "[%(asctime)s] : %(levelname)-8s : %(name)s : %(funcName)s : %(message)s"
    file_handler.setFormatter(logging.Formatter(file_format))
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # Make a traceback logger specifically for adding tracebacks to log file
    traceback_log = logging.getLogger('traceback')
    traceback_log.propagate = False
    traceback_log.setLevel(logging.ERROR)
    traceback_log.addHandler(file_handler)

def exc_handler(exc_type, exc_value, traceback):
    """An execption handler/hook that will only be called if an exception
    isn't called.  This will save us from print tracebacks or unrecognizable
    errors to the user's console.

    Note, however, that this doesn't effect code in a separate process as the
    exception never gets raised in the parent.
    """
    logging.getLogger(__name__).error(exc_value)
    logging.getLogger('traceback').error(exc_value, exc_info=(exc_type,exc_value,traceback))

def remove_products():
    """Remove as many of the possible files that were created from a previous
    run of this script, including temporary files.

    :note:
        This does not remove the log file because it requires the log file
        to report what's being removed.
    """
    for f in glob(".lat*"):
        _safe_remove(f)
    for f in glob(".lon*"):
        _safe_remove(f)
    for f in glob(".mode*"):
        _safe_remove(f)
    for f in glob(".image*"):
        _safe_remove(f)
    for f in glob("latitude*.real4.*"):
        _safe_remove(f)
    for f in glob("longitude*.real4.*"):
        _safe_remove(f)
    for f in glob("image*.real4.*"):
        _safe_remove(f)
    for f in glob("mode_*.real4.*"):
        _safe_remove(f)
    for f in glob("prescale_*.real4.*"):
        _safe_remove(f)
    for f in glob("ll2cr_*.real4.*"):
        _safe_remove(f)

    for f in glob("result*.real4.*"):
        _safe_remove(f)

    for f in glob("npp_viirs*.tif"):
        _safe_remove(f)

def process_data_sets(filepaths,
        fornav_D=None, fornav_d=None,
        forced_grid=None, etype=None,
        create_pseudo=True,
        num_procs=1,
        rescale_config=None,
        inc_by_one=False,
        new_dnb=False # XXX
        ):
    """Process all the files provided from start to finish,
    from filename to Geotiff file.
    """
    status_to_return = STATUS_SUCCESS

    # Declare polar2grid components
    frontend = Frontend()
    backend = Backend(etype=etype, rescale_config=rescale_config,
            inc_by_one=inc_by_one)

    # Extract Swaths
    log.info("Extracting swaths...")
    try:
        meta_data = frontend.make_swaths(
                filepaths,
                scale_dnb=True,
                new_dnb=new_dnb,
                create_fog=True,
                cut_bad=True
                )

        # Let's be lazy and give names to the 'global' viirs info
        sat = meta_data["sat"]
        instrument = meta_data["instrument"]
        start_time = meta_data["start_time"]
        bands = meta_data["bands"]
        fbf_lat = meta_data["fbf_lat"]
        fbf_lon = meta_data["fbf_lon"]
        nav_set_uid = meta_data["nav_set_uid"]
    except StandardError:
        log.error("Swath creation failed")
        log.debug("Swath creation error:", exc_info=1)
        status_to_return |= STATUS_FRONTEND_FAIL
        return status_to_return

    if len(bands) == 0:
        log.error("No more bands to process, quitting...")
        return status_to_return or STATUS_UNKNOWN_FAIL

    # Determine grid
    try:
        log.info("Determining what grids the data fits in...")
        grid_jobs = create_grid_jobs(sat, instrument, bands, fbf_lat, fbf_lon, backend,
                forced_grids=forced_grid)
    except StandardError:
        log.debug("Grid Determination error:", exc_info=1)
        log.error("Determining data's grids failed")
        status_to_return |= STATUS_GDETER_FAIL
        return status_to_return

    ### Remap the data
    try:
        remapped_jobs = remap_bands(sat, instrument, nav_set_uid,
                fbf_lon, fbf_lat, grid_jobs,
                num_procs=num_procs, fornav_d=fornav_d, fornav_D=fornav_D,
                lat_fill_value=meta_data.get("lat_fill_value", None),
                lon_fill_value=meta_data.get("lon_fill_value", None),
                lat_south=meta_data.get("lat_south", None),
                lat_north=meta_data.get("lat_north", None),
                lon_west=meta_data.get("lon_west", None),
                lon_east=meta_data.get("lon_east", None)
                )
    except StandardError:
        log.debug("Remapping Error:", exc_info=1)
        log.error("Remapping data failed")
        status_to_return |= STATUS_REMAP_FAIL
        return status_to_return

    ### BACKEND ###
    W = Workspace('.')
    for grid_name,grid_dict in remapped_jobs.items():
        for (band_kind, band_id),band_dict in grid_dict.items():
            log.info("Running geotiff backend for %s%s band grid %s" % (band_kind, band_id, grid_name))
            try:
                # Get the data from the flat binary file
                data = getattr(W, band_dict["fbf_remapped"].split(".")[0]).copy()

                # Call the backend
                backend.create_product(
                        sat,
                        instrument,
                        band_kind,
                        band_id,
                        band_dict["data_kind"],
                        data,
                        start_time=start_time,
                        grid_name=grid_name,
                        proj4_str=band_dict["proj4_str"],
                        grid_origin_x=band_dict["grid_origin_x"],
                        grid_origin_y=band_dict["grid_origin_y"],
                        pixel_size_x=band_dict["pixel_size_x"],
                        pixel_size_y=band_dict["pixel_size_y"],
                        fill_value=band_dict.get("fill_value", None)
                        )
            except StandardError:
                log.error("Error in the Geotiff backend for %s%s in grid %s" % (band_kind, band_id, grid_name))
                log.debug("Geotiff backend error:", exc_info=1)
                del remapped_jobs[grid_name][(band_kind, band_id)]

        if len(remapped_jobs[grid_name]) == 0:
            log.error("All backend jobs for grid %s failed" % (grid_name,))
            del remapped_jobs[grid_name]

    if len(remapped_jobs) == 0:
        log.warning("Geotiff backend failed for all grids for bands %r" % (bands.keys(),))
        status_to_return |= STATUS_BACKEND_FAIL

    log.info("Processing of bands %r is complete" % (bands.keys(),))

    return status_to_return

def _process_data_sets(*args, **kwargs):
    """Wrapper function around `process_data_sets` so that it can called
    properly from `run_viir2awips`, where the exitcode is the actual
    returned value from `process_data_sets`.

    This function also checks for exceptions other than the ones already
    checked for in `process_data_sets` so that they are
    recorded properly.
    """
    try:
        stat = process_data_sets(*args, **kwargs)
        sys.exit(stat)
    except MemoryError:
        log.error("viirs2gtiff ran out of memory, check log file for more info")
        log.debug("Memory error:", exc_info=1)
    except OSError:
        log.error("viirs2gtiff had a OS error, check log file for more info")
        log.debug("OS error:", exc_info=1)
    except StandardError:
        log.error("viirs2gtiff had an unexpected error, check log file for more info")
        log.debug("Unexpected/Uncaught error:", exc_info=1)
    except KeyboardInterrupt:
        log.info("viirs2gtiff was cancelled by a keyboard interrupt")

    sys.exit(-1)

def run_glue(filepaths,
        multiprocess=True, **kwargs
        ):
    """Separate input files into groups that share navigation files data.

    Call the processing function in separate process or same process depending
    on value of `multiprocess` keyword.
    """
    # Rewrite/force parameters to specific format
    filepaths = [ os.path.abspath(os.path.expanduser(x)) for x in sorted(filepaths) ]

    M_files = sorted(set([ x for x in filepaths if os.path.split(x)[1].startswith("SVM") ]))
    I_files = sorted(set([ x for x in filepaths if os.path.split(x)[1].startswith("SVI") ]))
    DNB_files = sorted(set([ x for x in filepaths if os.path.split(x)[1].startswith("SVDNB") ]))
    all_used = set(M_files + I_files + DNB_files)
    all_provided = set(filepaths)
    not_used = all_provided - all_used
    if len(not_used):
        log.warning("Didn't know what to do with\n%s" % "\n".join(list(not_used)))

    pM = None
    pI = None
    pDNB = None
    exit_status = 0
    if len(M_files) != 0:
        log.debug("Processing M files")
        try:
            if multiprocess:
                pM = Process(target=_process_data_sets,
                        args = (M_files,),
                        kwargs = kwargs
                        )
                pM.start()
            else:
                stat = _process_data_sets(M_files, **kwargs)
                exit_status = exit_status or stat
        except StandardError:
            log.error("Could not process M files")
            exit_status = exit_status or len(M_files)

    if len(I_files) != 0:
        log.debug("Processing I files")
        try:
            if multiprocess:
                pI = Process(target=_process_data_sets,
                        args = (I_files,),
                        kwargs = kwargs
                        )
                pI.start()
            else:
                stat = _process_data_sets(I_files, **kwargs)
                exit_status = exit_status or stat
        except StandardError:
            log.error("Could not process I files")
            exit_status = exit_status or len(I_files)

    if len(DNB_files) != 0:
        log.debug("Processing DNB files")
        try:
            if multiprocess:
                pDNB = Process(target=_process_data_sets,
                        args = (DNB_files,),
                        kwargs = kwargs
                        )
                pDNB.start()
            else:
                stat = _process_data_sets(DNB_files, **kwargs)
                exit_status = exit_status or stat
        except StandardError:
            log.error("Could not process DNB files")
            exit_status = exit_status or len(DNB_files)

    log.debug("Waiting for subprocesses")
    if pM is not None:
        pM.join()
        stat = pM.exitcode
        exit_status = exit_status or stat
    if pI is not None:
        pI.join()
        stat = pI.exitcode
        exit_status = exit_status or stat
    if pDNB is not None:
        pDNB.join()
        stat = pDNB.exitcode
        exit_status = exit_status or stat

    return exit_status

def main():
    import argparse
    description = """
    Create VIIRS swaths, remap them to a grid, and place that remapped data
    into a GeoTiff.
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
    parser.add_argument('--sp', dest='single_process', default=False, action='store_true',
            help="Processing is sequential instead of one process per kind of band")
    parser.add_argument('--num-procs', dest="num_procs", default=1,
            help="Specify number of processes that can be used to run ll2cr/fornav calls in parallel")
    parser.add_argument('-k', '--keep', dest='remove_prev', default=True, action='store_true',
            help="Don't delete any files that were previously made (WARNING: processing may not run successfully)")
    parser.add_argument('--no-pseudo', dest='create_pseudo', default=True, action='store_false',
            help="Don't create pseudo bands")
    parser.add_argument('--rescale-config', dest='rescale_config', default=None,
            help="specify alternate rescale configuration file")
    parser.add_argument('--new-dnb', dest='new_dnb', default=False, action='store_true',
            help="run new DNB scaling if provided DNB data (temporary)") # XXX

    # Remapping/Grids
    parser.add_argument('-g', '--grids', dest='forced_grids', nargs="+", default="wgs84_fit",
            help="Force remapping to only some grids, defaults to 'wgs84_fit', use 'all' for determination")

    # Backend Specific
    parser.add_argument('--bits', dest="etype", default=None, type=_bits_to_etype,
            help="number of bits in the geotiff, usually unsigned")
    parser.add_argument('--inc_by_one', dest="inc_by_one", default=False, action="store_true",
            help="tell rescaler to increment by one to scaled data can have a 0 fill value (ex. 0-254 -> 1-255 with 0 being fill)")

    parser.add_argument('data_files', nargs="+",
            help="Data directory where satellite data is stored or list of data filenames if '-f' is specified")

    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)])

    # Don't set this up until after you have setup logging
    sys.excepthook = exc_handler

    fornav_D = int(args.fornav_D)
    fornav_d = int(args.fornav_d)
    num_procs = int(args.num_procs)
    forced_grids = args.forced_grids
    if forced_grids == 'all': forced_grids = None

    if "help" in args.data_files:
        parser.print_help()
        sys.exit(0)
    elif "remove" in args.data_files:
        log.debug("Removing previous products")
        remove_products()
        sys.exit(0)

    if args.get_files:
        hdf_files = args.data_files[:]
    elif len(args.data_files) == 1:
        base_dir = os.path.abspath(args.data_files[0])
        hdf_files = [ os.path.join(base_dir,x) for x in os.listdir(base_dir) if x.startswith("SV") and x.endswith(".h5") ]
    else:
        log.error("Wrong number of arguments")
        parser.print_help()
        return -1

    if args.remove_prev:
        log.debug("Removing any previous files")
        remove_products()

    stat = run_glue(hdf_files, fornav_D=fornav_D, fornav_d=fornav_d,
                forced_grid=forced_grids,
                etype=args.etype,
                create_pseudo=args.create_pseudo,
                multiprocess=not args.single_process, num_procs=num_procs,
                rescale_config=args.rescale_config,
                inc_by_one=args.inc_by_one,
                new_dnb=args.new_dnb # XXX
                )

    return stat

if __name__ == "__main__":
    sys.exit(main())

