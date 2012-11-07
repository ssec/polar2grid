#!/usr/bin/env python
# encoding: utf-8
"""Script that uses the `polar2grid` toolbox of modules to take VIIRS
hdf5 (.h5) files and create a properly scaled AWIPS compatible NetCDF file.

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
from .rescale import dnb_scale
from .grids.grids import determine_grid_coverage_fbf,get_grid_info
from .remap import remap_bands
from .awips import Backend

import os
import sys
import logging
from multiprocessing import Process
import numpy
from glob import glob

log = logging.getLogger(__name__)
LOG_FN = os.environ.get("VIIRS2AWIPS_LOG", "./viirs2awips.log")

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

def _safe_remove(fn):
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
    for f in glob("ll2cr_*.img"):
        _safe_remove(f)

    for f in glob("result*.real4.*"):
        _safe_remove(f)

    for f in glob("SSEC_AWIPS_VIIRS*"):
        _safe_remove(f)

def run_prescaling(img_filepath, mode_filepath, fill_value=DEFAULT_FILL_VALUE):
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
            HIGH = 100
            LOW = 88
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

def create_grid_jobs(sat, instrument, kind, bands, fbf_lat, fbf_lon, backend,
        forced_grids=None):
    # Check what grids the backend can handle
    all_possible_grids = set()
    for band in bands.keys():
        this_band_can_handle  = backend.can_handle_inputs(sat, instrument, kind, band, bands[band]["data_kind"])
        bands[band]["grids"] = this_band_can_handle
        if isinstance(this_band_can_handle, str):
            all_possible_grids.update([this_band_can_handle])
        else:
            all_possible_grids.update(this_band_can_handle)
        log.debug("Kind %s Band %s can handle these grids: '%r'" % (kind,band,this_band_can_handle))

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
    for band in bands.keys():
        if bands[band]["grids"] == GRIDS_ANY:
            bands[band]["grids"] = list(grids)
        elif bands[band]["grids"] == GRIDS_ANY_PROJ4:
            bands[band]["grids"] = [ g for g in grids if grid_infos[g]["grid_kind"] == GRID_KIND_PROJ4 ]
        elif bands[band]["grids"] == GRIDS_ANY_GPD:
            bands[band]["grids"] = [ g for g in grids if grid_infos[g]["grid_kind"] == GRID_KIND_GPD ]
        elif len(bands[band]["grids"]) == 0:
            log.error("The backend does not support kind %s band %s, won't add to job list..." % (kind, band))
            # Handled in the next for loop via the inner for loop not adding anything
        else:
            bands[band]["grids"] = grids.intersection(bands[band]["grids"])
            bad_grids = grids - set(bands[band]["grids"])
            if len(bad_grids) != 0 and forced_grids is not None:
                log.error("Backend does not know how to handle grids '%r'" % list(bad_grids))
                raise ValueError("Backend does not know how to handle grids '%r'" % list(bad_grids))

    # Create "grid" jobs to be run through remapping
    # Jobs are per grid per band
    grid_jobs = {}
    for band in bands.keys():
        for grid_name in bands[band]["grids"]:
            if grid_name not in grid_jobs: grid_jobs[grid_name] = {}
            if band not in grid_jobs[grid_name]: grid_jobs[grid_name][band] = {}
            log.debug("Kind %s band %s will be remapped to grid %s" % (kind,band,grid_name))
            grid_jobs[grid_name][band] = bands[band].copy()

    if len(grid_jobs) == 0:
        log.error("No backend compatible grids were found to fit the data for kind %s" % (kind,))
        raise ValueError("No backend compatible grids were found to fit the data for kind %s" % (kind,))

    return grid_jobs

def create_pseudobands(kind, bands, fill_value=DEFAULT_FILL_VALUE):
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
            fog_map[ (~night_mask) | (i5 == fill_value) | (i4 == fill_value) ] = fill_value
            del fog_map
            del i5,i4
            bands[BID_FOG] = fog_dict
        except StandardError:
            log.error("Error creating Fog pseudo band")
            log.debug("Fog creation error:", exc_info=1)

def process_data_sets(filepaths,
        fornav_D=None, fornav_d=None,
        forced_grid=None,
        forced_gpd=None, forced_nc=None,
        create_pseudo=True,
        num_procs=1,
        rescale_config=None,
        backend_config=None
        ):
    """Process all the files provided from start to finish,
    from filename to AWIPS NC file.
    """
    status_to_return = STATUS_SUCCESS

    # Load any configuration files needed
    frontend = Frontend()
    backend = Backend(rescale_config=rescale_config, backend_config=backend_config)

    # Extract Swaths
    log.info("Extracting swaths...")
    try:
        meta_data = frontend.make_swaths(filepaths, cut_bad=True)

        # Let's be lazy and give names to the 'global' viirs info
        sat = meta_data["sat"]
        instrument = meta_data["instrument"]
        kind = meta_data["kind"]
        start_time = meta_data["start_time"]
        bands = meta_data["bands"]
        fbf_lat = meta_data["fbf_lat"]
        fbf_lon = meta_data["fbf_lon"]
    except StandardError:
        log.error("Swath creation failed")
        log.debug("Swath creation error:", exc_info=1)
        status_to_return |= STATUS_FRONTEND_FAIL
        return status_to_return

    # Create pseudo-bands
    # FIXME: Move pseudoband creation to the frontend
    try:
        if create_pseudo:
            create_pseudobands(kind, bands)
    except StandardError:
        log.error("Pseudo band creation failed")
        log.debug("Pseudo band error:", exc_info=1)
        status_to_return |= STATUS_FRONTEND_FAIL
        return status_to_return

    # Do any pre-remapping rescaling
    # FIXME: Move DNB scaling to the frontend
    for band,band_job in bands.items():
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
            status_to_return |= STATUS_FRONTEND_FAIL

    if len(bands) == 0:
        log.error("No more bands to process, quitting...")
        return status_to_return or UNKNOWN_FAIL

    # Determine grid
    try:
        log.info("Determining what grids the data fits in...")
        grid_jobs = create_grid_jobs(sat, instrument, kind, bands, fbf_lat, fbf_lon, backend,
                forced_grids=forced_grid)
    except StandardError:
        log.debug("Grid Determination error:", exc_info=1)
        log.error("Determining data's grids failed")
        status_to_return |= STATUS_GDETER_FAIL
        return status_to_return

    ### Remap the data
    try:
        remapped_jobs = remap_bands(sat, instrument, kind,
                fbf_lon, fbf_lat, grid_jobs,
                num_procs=num_procs, fornav_d=fornav_d, fornav_D=fornav_D,
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
        for band,band_dict in grid_dict.items():
            log.info("Running AWIPS backend for %s%s band grid %s" % (kind,band,grid_name))
            try:
                # Get the data from the flat binary file
                data = getattr(W, band_dict["fbf_remapped"].split(".")[0]).copy()

                # Call the backend
                backend.create_product(
                        sat,
                        instrument,
                        kind,
                        band,
                        band_dict["data_kind"],
                        data,
                        start_time=start_time,
                        grid_name=grid_name,
                        ncml_template=forced_nc or None,
                        fill_value=band_dict.get("fill_value", None)
                        )
            except StandardError:
                log.error("Error in the AWIPS backend for %s%s in grid %s" % (kind,band,grid_name))
                log.debug("AWIPS backend error:", exc_info=1)
                del remapped_jobs[grid_name][band]

        if len(remapped_jobs[grid_name]) == 0:
            log.error("All backend jobs for grid %s failed" % (grid_name,))
            del remapped_jobs[grid_name]

    if len(remapped_jobs) == 0:
        log.warning("AWIPS backend failed for all grids for %s%s" % (kind,band))
        status_to_return |= STATUS_BACKEND_FAIL

    log.info("Processing of bands of kind %s is complete" % kind)

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
        log.error("viirs2awips ran out of memory, check log file for more info")
        log.debug("Memory error:", exc_info=1)
    except OSError:
        log.error("viirs2awips had a OS error, check log file for more info")
        log.debug("OS error:", exc_info=1)
    except StandardError:
        log.error("viirs2awips had an unexpected error, check log file for more info")
        log.debug("Unexpected/Uncaught error:", exc_info=1)
    except KeyboardInterrupt:
        log.info("viirs2awips was cancelled by a keyboard interrupt")

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
    into a AWIPS compatible netcdf file.
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

    # Remapping/Grids
    parser.add_argument('-g', '--grids', dest='forced_grids', nargs="+", default="all",
            help="Force remapping to only some grids, defaults to 'all', use 'all' for determination")
    parser.add_argument('--gpd', dest='forced_gpd', default=None,
            help="Specify a different gpd file to use")

    # Backend Specific
    parser.add_argument('--nc', dest='forced_nc', default=None,
            help="Specify a different ncml file to use")
    parser.add_argument('--backend-config', dest='backend_config', default=None,
            help="specify alternate backend configuration file")

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
                forced_gpd=args.forced_gpd, forced_nc=args.forced_nc,
                create_pseudo=args.create_pseudo,
                multiprocess=not args.single_process, num_procs=num_procs,
                rescale_config=args.rescale_config,
                backend_config=args.backend_config
                )

    return stat

if __name__ == "__main__":
    sys.exit(main())

