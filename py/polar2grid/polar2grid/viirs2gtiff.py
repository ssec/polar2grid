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
from polar2grid.viirs import make_swaths
from .grids.grids import determine_grid_coverage_fbf,get_grid_info
from .viirs2awips import run_prescaling,_safe_remove
from .remap import remap_bands
from .gtiff_backend import can_handle_inputs,backend,_bits_to_etype
import pyproj

import os
import sys
import logging
from multiprocessing import Process
import numpy
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
    for f in glob("swath*.img"):
        _safe_remove(f)
    for f in glob("lat*.img"):
        _safe_remove(f)
    for f in glob("lon*.img"):
        _safe_remove(f)

    for f in glob("*_rows_*.img"):
        _safe_remove(f)
    for f in glob("*_cols_*.img"):
        _safe_remove(f)

    for f in glob("output*.img"):
        _safe_remove(f)
    for f in glob("result*.real4.*"):
        _safe_remove(f)

    for f in glob("npp_viirs*.tif"):
        _safe_remove(f)

def create_grid_jobs(sat, instrument, kind, bands, fbf_lat, fbf_lon,
        forced_grids=None, custom_proj_name=None):
    if forced_grids is not None:
        if isinstance(forced_grids, list): grids = forced_grids
        else: grids = [forced_grids]
    grids = set(grids)

    # Check what grids the backend can handle
    all_possible_grids = set()
    for band in bands.keys():
        this_band_can_handle  = can_handle_inputs(sat, instrument, kind, band, bands[band]["data_kind"])
        bands[band]["grids"] = this_band_can_handle
        all_possible_grids.update(this_band_can_handle)

    # If they forced grids make sure we can handle them
    if forced_grids is not None:
        grid_infos = dict((g,get_grid_info(g)) for g in grids)
        for band in bands.keys():
            if bands[band]["grids"] == GRIDS_ANY:
                bands[band]["grids"] = grids
            elif bands[band]["grids"] == GRIDS_ANY_PROJ4:
                bands[band]["grids"] = [ g for g in grids if grid_infos[g]["grid_kind"] == GRID_KIND_PROJ4 ]
            elif bands[band]["grids"] == GRIDS_ANY_GPD:
                bands[band]["grids"] = [ g for g in grids if grid_infos[g]["grid_kind"] == GRID_KIND_GPD ]
            else:
                bands[band]["grids"] = grids.intersection(bands[band]["grids"])
                bad_grids = grids - set(bands[band]["grids"])
                if len(bad_grids) != 0:
                    log.error("Backend does not know how to handle grids '%r'" % list(bad_grids))
                    raise ValueError("Backend does not know how to handle grids '%r'" % list(bad_grids))
    elif custom_proj_name is not None:
        # We are fitting the grid to the data
        # the else statement should never be executed
        # TODO
        pass
    else:
        # Check if the data fits in the grids
        all_useful_grids = determine_grid_coverage_fbf(fbf_lon, fbf_lat, list(all_possible_grids))

        # Filter out the grids that aren't useful to the data
        for band in bands.keys():
            bands[band]["grids"] = all_useful_grids.intersection(bands[band]["grids"])

    # Create "grid" jobs to be run through remapping
    # Jobs are per grid per band
    grid_jobs = {}
    for band in bands.keys():
        for grid_name in bands[band]["grids"]:
            if grid_name not in grid_jobs: grid_jobs[grid_name] = {}
            if band not in grid_jobs[grid_name]: grid_jobs[grid_name][band] = {}
            log.debug("Kind %s band %s will be remapped to grid %s" % (kind,band,grid_name))
            grid_jobs[grid_name][band] = bands[band].copy()

    return grid_jobs

def create_pseudobands(kind, bands):
    # Fog pseudo-band
    if (kind == BKIND_I) and (BID_05 in bands) and (BID_04 in bands):
        log.info("Creating IFOG pseudo band...")
        try:
            W = Workspace('.')
            mode_attr = bands[BID_05]["fbf_mode"].split(".")[0]
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
            fog_map[ (~night_mask) | (i5 == -999.0) | (i4 == -999.0) ] = -999.0
            del fog_map
            del i5,i4
            bands[BID_FOG] = fog_dict
        except StandardError:
            log.error("Error creating Fog pseudo band")
            log.debug("Fog creation error:", exc_info=1)

def process_kind(filepaths,
        fornav_D=None, fornav_d=None,
        forced_grid=None, etype=None,
        create_pseudo=True,
        num_procs=1,
        rescale_config=None
        ):
    """Process all the files provided from start to finish,
    from filename to AWIPS NC file.
    """
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

    # Extract Swaths
    log.info("Extracting swaths...")
    try:
        meta_data = make_swaths(filepaths, cut_bad=True)
    except StandardError:
        log.error("Swath creation failed")
        log.debug("Swath creation error:", exc_info=1)
        SUCCESS |= SWATH_FAIL
        return SUCCESS
    # Let's be lazy and give names to the 'global' viirs info
    sat = meta_data["sat"]
    instrument = meta_data["instrument"]
    kind = meta_data["kind"]
    start_time = meta_data["start_time"]
    bands = meta_data["bands"]
    fbf_lat = meta_data["fbf_lat"]
    fbf_lon = meta_data["fbf_lon"]

    # Create pseudo-bands
    try:
        if create_pseudo:
            create_pseudobands(kind, bands)
    except StandardError:
        log.error("Pseudo band creation failed")
        log.debug("Pseudo band error:", exc_info=1)
        SUCCESS |= SWATH_FAIL
        return SUCCESS

    # Do any pre-remapping rescaling
    log.info("Prescaling data before remapping...")
    for band,band_job in bands.items():
        if kind != BKIND_DNB:
            # It takes too long to read in the data, so just skip it
            band_job["fbf_swath"] = band_job["fbf_img"]
            continue

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
            SUCCESS |= PRESCALE_FAIL

    if len(bands) == 0:
        log.error("No more bands to process, quitting...")
        return SUCCESS or UNKNOWN_FAIL

    # Determine grid
    try:
        log.info("Determining what grids the data fits in...")
        grid_jobs = create_grid_jobs(sat, instrument, kind, bands, fbf_lat, fbf_lon,
                forced_grids=forced_grid)
    except StandardError:
        log.debug("Grid Determination error:", exc_info=1)
        log.error("Determining data's grids failed")
        SUCCESS |= GDETER_FAIL
        return SUCCESS

    ### Remap the data
    try:
        remapped_jobs = remap_bands(sat, instrument, kind,
                fbf_lon, fbf_lat, grid_jobs,
                num_procs=num_procs, fornav_d=fornav_d, fornav_D=fornav_D,
                lat_min=meta_data.get("lat_min", None),
                lat_max=meta_data.get("lat_max", None),
                lon_min=meta_data.get("lon_min", None),
                lon_max=meta_data.get("lon_max", None)
                )
    except StandardError:
        log.debug("Remapping Error:", exc_info=1)
        log.error("Remapping data failed")
        SUCCESS |= REMAP_FAIL
        return SUCCESS

    ### BACKEND ###
    W = Workspace('.')
    for grid_name,grid_dict in remapped_jobs.items():
        for band,band_dict in grid_dict.items():
            log.info("Running geotiff backend for %s%s band grid %s" % (kind,band,grid_name))
            try:
                # Get the data from the fbf file
                data = getattr(W, band_dict["fbf_remapped"].split(".")[0]).copy()

                # Call the backend
                backend(
                        sat,
                        instrument,
                        kind,
                        band,
                        band_dict["data_kind"],
                        data,
                        start_time=start_time,
                        grid_name=grid_name,
                        proj4_str=band_dict["proj4_str"],
                        grid_origin_x=band_dict["grid_origin_x"],
                        grid_origin_y=band_dict["grid_origin_y"],
                        pixel_size_x=band_dict["pixel_size_x"],
                        pixel_size_y=band_dict["pixel_size_y"],
                        etype=etype,
                        rescale_config=rescale_config
                        )
            except StandardError:
                log.error("Error in the Geotiff backend for %s%s in grid %s" % (kind,band,grid_name))
                log.debug("Geotiff backend error:", exc_info=1)
                del remapped_jobs[grid_name][band]

        if len(remapped_jobs[grid_name]) == 0:
            log.error("All backend jobs for grid %s failed" % (grid_name,))
            del remapped_jobs[grid_name]

    if len(remapped_jobs) == 0:
        log.warning("Geotiff backend failed for all grids for %s bands" % (kind))
        SUCCESS |= BACKEND_FAIL

    log.info("Processing of bands of kind %s is complete" % kind)

    return SUCCESS

def _process_kind(*args, **kwargs):
    """Wrapper function around `process_kind` so that it can called
    properly from `run_viir2awips`, where the exitcode is the actual
    returned value from `process_kind`.

    This function also checks for exceptions other than the ones already
    checked for in `process_kind` so that they are
    recorded properly.
    """
    try:
        stat = process_kind(*args, **kwargs)
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

def run_viirs2gtiff(filepaths,
        multiprocess=True, **kwargs
        ):
    """
        num_procs=1,
        fornav_D=None, fornav_d=None,
        forced_grid=None, etype=None,
        create_pseudo=True,
        proj4_str=None, grid_width=None, grid_height=None,
        pixel_size_x=None, pixel_size_y=None):
    Go through the motions of converting
    a VIIRS h5 file into a AWIPS NetCDF file.

    1. viirs_guidebook.py       : Get file info/data
    2. viirs_imager_to_swath.py : Concatenate data
    3. Prescale DNB
    4. Calculat Grid            : Figure out what grids the data fits in
    5. ll2cr
    6. fornav
    7. rescale.py
    8. awips_netcdf.py
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
                pM = Process(target=_process_kind,
                        args = (M_files,),
                        kwargs = kwargs
                        )
                pM.start()
            else:
                stat = _process_kind(M_files, **kwargs)
                exit_status = exit_status or stat
        except StandardError:
            log.error("Could not process M files")
            exit_status = exit_status or len(M_files)

    if len(I_files) != 0:
        log.debug("Processing I files")
        try:
            if multiprocess:
                pI = Process(target=_process_kind,
                        args = (I_files,),
                        kwargs = kwargs
                        )
                pI.start()
            else:
                stat = _process_kind(I_files, **kwargs)
                exit_status = exit_status or stat
        except StandardError:
            log.error("Could not process I files")
            exit_status = exit_status or len(I_files)

    if len(DNB_files) != 0:
        log.debug("Processing DNB files")
        try:
            if multiprocess:
                pDNB = Process(target=_process_kind,
                        args = (DNB_files,),
                        kwargs = kwargs
                        )
                pDNB.start()
            else:
                stat = _process_kind(DNB_files, **kwargs)
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
    description2 = """
    For DB:
    %prog [options] <event directory>

    For testing (usable files are those of bands mentioned in templates.conf):
    # Looks for all usable files in data directory
    %prog [options] <data directory>
    # Uses all usable files of the specfied
    %prog [options] -f file1.h5 file2.h5 ...
    # Only use the I01 files of the files specified
    %prog [options] -b I01 -f file1.h5 file2.h5 ...
    # Only use the I band files of the files specified
    %prog [options] -b I -f file1.h5 file2.h5 ...
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
            help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument('--bits', dest="etype", default=None, type=_bits_to_etype,
            help="number of bits in the geotiff, usually unsigned")
    parser.add_argument('-D', dest='fornav_D', default=40,
            help="Specify the -D option for fornav")
    parser.add_argument('-d', dest='fornav_d', default=2,
            help="Specify the -d option for fornav")
    parser.add_argument('-f', dest='get_files', default=False, action="store_true",
            help="Specify that hdf files are listed, not a directory")
    parser.add_argument('-g', '--grid', dest='forced_grid', default=None,
            help="Force remapping to only one grid")
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
    forced_grid = args.forced_grid

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

    remove_prev = True
    if remove_prev:
        log.debug("Removing any previous files")
        remove_products()

    if forced_grid:
        proj4_str = None
        pixel_size_x = None
        pixel_size_y = None
        grid_width = None
        grid_height = None
        grid_name = None
    else:
        default_projection = "+proj=latlong +a=6378137 +b=6378137"
        grid_name = args.grid_name
        proj4_str = args.proj4_str or default_projection
        p = pyproj.Proj(proj4_str)
        del p
        if args.pixel_size is None and args.grid_size is None:
            log.error("Either pixel size or grid size must be specified")
            return -1
        if args.pixel_size is None:
            pixel_size_x = None
            pixel_size_y = None
        else:
            pixel_size_x,pixel_size_y = args.pixel_size
        if args.grid_size is None:
            grid_width = None
            grid_height = None
        else:
            grid_width,grid_height = args.grid_size

    stat = run_viirs2gtiff(hdf_files, fornav_D=fornav_D, fornav_d=fornav_d,
                forced_grid=forced_grid, etype=args.etype,
                create_pseudo=args.create_pseudo,
                multiprocess=not args.single_process, num_procs=num_procs,
                rescale_config=args.rescale_config
                )

    return stat

if __name__ == "__main__":
    sys.exit(main())

