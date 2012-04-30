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

from polar2grid.core import Workspace,K_BTEMP,K_FOG
from polar2grid.viirs_imager_to_swath import make_swaths
from polar2grid.rescale import prescale
from polar2grid import ms2gt
from polar2grid.awips_netcdf import awips_backend
from polar2grid.awips_config import BANDS,GRID_TEMPLATES,SHAPES,verify_config,get_grid_info

import os
import sys
import logging
import multiprocessing
import numpy
from glob import glob

log = logging.getLogger(__name__)

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

    for f in glob("SSEC_AWIPS_VIIRS*"):
        _safe_remove(f)

def run_prescaling(kind, band, data_kind,
        img_filepath, mode_filepath,
        require_dn=False
        ):
    """A wrapper function for calling the prescaling functions.  This function
    will read the binary image data from ``img_filepath`` as well as any other
    data that may be required to prescale the data correctly, such as
    day/night/twilight masks.

    :Parameters:
        kind : str
            Kind of band that we are prescaling (ex. ``I`` or ``M`` or ``DNB``).
        band : str
            Band number that we are prescaling (ex. ``01`` or ``00`` for DNB).
        data_kind : str
            Kind of data being prescaled using the constants defined
            in `polar2grid.core`.
        img_filepath : str
            Filepath to the binary image swath data in FBF format
            (ex. ``image_I01.real4.6400.10176``).
        mode_filepath : str
            Filepath to the binary mode swath data in FBF format
            (ex. ``mode_I01.real4.6400.10176``).
    
    :Keywords:
        require_dn: bool
            Specify whether the day/night/twilight masks are required to
            make properly prescale this data.  Such as DNB data.
            Defaults to ``False``.
    """
        
    log.debug("Prescaling %s%s" % (kind,band))
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
            good_mask = ~((img == -999.0) | (mode_mask == -999.0))
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

        elif require_dn:
            log.error("Mode shape is different than the data's shape (%s) vs (%s)" % (mode_mask.shape, data.shape))
            raise ValueError("Mode shape is different than the data's shape (%s) vs (%s)" % (mode_mask.shape, data.shape))
    except StandardError:
        if require_dn:
            log.error("Could not open mode mask file %s" % mode_filepath)
            log.debug("Files matching %r" % glob(mode_attr + "*"))
            raise
        else:
            log.debug("Could not open mode mask file %s" % mode_filepath)

    try:
        rescaled_data = prescale(data,
                kind=kind,
                band=band,
                data_kind=data_kind,
                **scale_kwargs)
        log.debug("Data min: %f, Data max: %f" % (rescaled_data.min(),rescaled_data.max()))
        rows,cols = rescaled_data.shape
        fbf_swath_var = "prescale_%s%s" % (kind,band)
        fbf_swath = "./%s.real4.%d.%d" % (fbf_swath_var, cols, rows)
        rescaled_data.tofile(fbf_swath)
    except StandardError:
        log.error("Unexpected error while rescaling data", exc_info=1)
        raise

    return fbf_swath

def _determine_grids(kind, fbf_lat, fbf_lon):
    grids = []
    # Get lat/lon data
    try:
        fbf_lat_var = os.path.split(fbf_lat)[1].split('.')[0]
        fbf_lon_var = os.path.split(fbf_lon)[1].split('.')[0]
        W = Workspace('.')
        lat_data = getattr(W, fbf_lat_var).flatten()
        lon_data = getattr(W, fbf_lon_var).flatten()
        lon_data_flipped = None
    except StandardError:
        log.error("There was an error trying to get the lat/lon swath data for grid determination")
        raise

    for grid_number in SHAPES.keys():
        tbound,bbound,lbound,rbound,percent = SHAPES[grid_number]
        if lbound > rbound:
            lbound = lbound + 360.0
            rbound = rbound + 360.0
            if lon_data_flipped is None:
                lon_mask = lon_data < 0
                lon_data_flipped = lon_data.copy()
                lon_data_flipped[lon_mask] = lon_data_flipped[lon_mask] + 360
                lon_data_use = lon_data_flipped
                del lon_mask
            else:
                lon_data_use = lon_data
        grid_mask = numpy.nonzero( (lat_data < tbound) & (lat_data > bbound) & (lon_data_use < rbound) & (lon_data_use > lbound) )[0]
        grid_percent = (len(grid_mask) / float(len(lat_data)))
        log.debug("Band %s had a %f coverage in grid %s" % (kind,grid_percent,grid_number))
        if grid_percent >= percent:
            grids.append(grid_number)
    return grids

def create_grid_jobs(kind, bands, fbf_lat, fbf_lon, start_dt,
        forced_grids=None, forced_gpd=None, forced_nc=None):
    if forced_grids is None and (forced_gpd is not None or forced_nc is not None):
        log.error("Grid gpd and nc templates cannot be forced if the grids are not forced")
        raise ValueError("Grid gpd and nc templates cannot be forced if the grids are not forced")

    if forced_grids is not None:
        if isinstance(forced_grids, list): grids = forced_grids
        else: grids = [forced_grids]
    else:
        grids = _determine_grids(kind, fbf_lat, fbf_lon)

    ll2cr_jobs = {}
    grid_jobs = {}
    log.debug("Grids to be analyzed %r" % grids)
    for idx,grid_name in enumerate(grids):
        for band in bands.keys():
            if verify_config(kind, band, grid_name):
                grid_info = get_grid_info(kind, band, grid_name, gpd=forced_gpd, nc=forced_nc)
                grid_info["start_dt"] = start_dt
                grid_info["tag"] = "ll2cr_%s_%s" % (kind,grid_name)
                grid_info["swath_rows"] = bands[band]["swath_rows"]
                grid_info["swath_cols"] = bands[band]["swath_cols"]
                grid_info["swath_scans"] = bands[band]["swath_scans"]
                grid_info["rows_per_scan"] = bands[band]["rows_per_scan"]
                if grid_name not in ll2cr_jobs: ll2cr_jobs[grid_name] = grid_info.copy()

                if band not in grid_jobs: grid_jobs[band] = {}
                grid_info["data_kind"] = bands[band]["data_kind"]
                grid_info["nc_filename"] = grid_info["start_dt"].strftime(grid_info["nc_format"])
                grid_jobs[band][grid_name] = grid_info
    return ll2cr_jobs,grid_jobs

def create_pseudo(kind, bands):
    # Fog pseudo-band
    if (kind == "I") and ("05" in bands) and ("04" in bands):
        log.info("Creating IFOG pseudo band...")
        try:
            W = Workspace('.')
            mode_attr = bands["05"]["fbf_mode"].split(".")[0]
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
                "data_kind" : K_FOG,
                "src_kind"  : K_BTEMP,
                "rows_per_scan" : bands["05"]["rows_per_scan"],
                "fbf_img" : "image_IFOG.%s" % ".".join(bands["05"]["fbf_img"].split(".")[1:]),
                "fbf_mode" : bands["05"]["fbf_mode"],
                "swath_scans" : bands["05"]["swath_scans"],
                "swath_rows" : bands["05"]["swath_rows"],
                "swath_cols" : bands["05"]["swath_cols"]
                }
        try:
            W = Workspace(".")
            i5_attr = bands["05"]["fbf_img"].split(".")[0]
            i4_attr = bands["04"]["fbf_img"].split(".")[0]
            i5 = getattr(W, i5_attr)
            i4 = getattr(W, i4_attr)
            fog_map = numpy.memmap(fog_dict["fbf_img"],
                    dtype=numpy.float32,
                    mode="w+",
                    shape=i5.shape
                    )
            numpy.subtract(i5, i4, fog_map)
            fog_map[~night_mask] = -999.0
            del fog_map
            del i5,i4
            bands["FOG"] = fog_dict
        except StandardError:
            log.error("Error creating Fog pseudo band")
            log.debug("Fog creation error:", exc_info=1)

def process_kind(filepaths,
        fornav_D=None, fornav_d=None,
        forced_grid=None,
        forced_gpd=None, forced_nc=None,
        num_procs=1
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
    # backend failed
    BACKEND_FAIL = 32
    # grid determination failed
    GDETER_FAIL = 64
    # there aren't any jobs left, not sure why
    UNKNOWN_FAIL = -1

    proc_pool = multiprocessing.Pool(num_procs)

    # Extract Swaths
    log.info("Extracting swaths...")
    def _band_filter(finfo):
        if finfo["kind"] == "DNB":
            if "DNB" not in BANDS:
                return False
            else:
                return True
        elif finfo["kind"] + finfo["band"] not in BANDS:
            return False
        else:
            return True
    try:
        meta_data = make_swaths(filepaths, filter=_band_filter, cut_bad=True)
    except StandardError:
        log.error("Swath creation failed")
        log.debug("Swath creation error:", exc_info=1)
        SUCCESS |= SWATH_FAIL
        return SUCCESS
    kind = meta_data["kind"]
    start_dt = meta_data["start_dt"]
    bands = meta_data["bands"]
    fbf_lat = meta_data["fbf_lat"]
    fbf_lon = meta_data["fbf_lon"]

    # Create pseudo-bands
    create_pseudo(kind, bands)

    # Do any pre-remapping rescaling
    log.info("Prescaling data before remapping...")
    for band,band_job in bands.items():
        if kind != "DNB":
            # It takes too long to read in the data, so just skip it
            band_job["fbf_swath"] = band_job["fbf_img"]
            continue

        try:
            fbf_swath = run_prescaling(
                    kind,
                    band,
                    band_job["data_kind"],
                    band_job["fbf_img"],
                    band_job["fbf_mode"],
                    require_dn = kind == "DNB"
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
        ll2cr_jobs,grid_jobs = create_grid_jobs(kind, bands, fbf_lat, fbf_lon, start_dt,
                forced_grids=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc)
    except StandardError:
        log.error("Determining data's grids failed")
        SUCCESS |= GDETER_FAIL
        return SUCCESS

    # Move nav fbf files to img files to be used by ll2cr
    img_lat = "lat_%s.img" % kind
    img_lon = "lon_%s.img" % kind
    _force_symlink(fbf_lat, img_lat)
    _force_symlink(fbf_lon, img_lon)
    meta_data["img_lat"] = img_lat
    meta_data["img_lon"] = img_lon

    # Run ll2cr
    for grid_number,grid_info in ll2cr_jobs.items():
        log.info("Running ll2cr for the %s band and grid %s" % (kind,grid_number))
        #cr_dict = ms2gt.ll2cr(
        #        grid_info["swath_cols"],
        #        grid_info["swath_scans"],
        #        grid_info["rows_per_scan"],
        #        img_lat,
        #        img_lon,
        #        grid_info["gpd_template"],
        #        verbose=log.getEffectiveLevel() <= logging.DEBUG,
        #        fill_io=(-999.0, -1e30),
        #        tag=grid_info["tag"]
        #        )

        grid_info["result_object"] = proc_pool.apply_async(ms2gt.ll2cr, args=(
                    grid_info["swath_cols"],
                    grid_info["swath_scans"],
                    grid_info["rows_per_scan"],
                    img_lat,
                    img_lon,
                    grid_info["gpd_template"]
                    ),
                    kwds=dict(
                        verbose=log.getEffectiveLevel() <= logging.DEBUG,
                        fill_io=(-999.0, -1e30),
                        tag=grid_info["tag"]
                        )
                    )

    proc_pool.close()
    proc_pool.join()
    # Yes it would be faster to check each individually and reuse the same pool
    # but its a lot more complicated
    proc_pool = multiprocessing.Pool(num_procs)

    for grid_number,grid_info in ll2cr_jobs.items():
        r = grid_info["result_object"]
        try:
            cr_dict = r.get()

            for grid_job in [ x[grid_number] for x in grid_jobs.values() if grid_number in x ]:
                grid_job["cr_dict"] = cr_dict
        except StandardError:
            log.warning("ll2cr failed for %s band, grid %s" % (kind,grid_number))
            log.warning("Won't process for this grid...")
            log.debug("ll2cr error:", exc_info=1)
            for band in bands.keys():
                if grid_number in grid_jobs[band]:
                    log.error("Removing %s%s for grid %s because of bad ll2cr execution" % (kind,band,grid_number))
                    del grid_jobs[band][grid_number]
                    if len(grid_jobs[band]) == 0:
                        log.error("No more grids to process for %s%s, removing..." % (kind,band))
                        del grid_jobs[band]
                        del bands[band]
                        SUCCESS |= LL2CR_FAIL

    if len(grid_jobs) == 0:
        log.error("No more grids to process for %s, quitting..." % kind)
        return SUCCESS or UNKNOWN_FAIL

    # Move fbf files to img files to be used by ms2gt utilities
    for band,band_job in bands.items():
        band_job["img_swath"] = "swath_%s.img" % band_job["band_name"]
        _force_symlink(band_job["fbf_swath"], band_job["img_swath"])

    # Build fornav call
    fornav_jobs = {}
    for band,band_job in bands.items():
        if band not in grid_jobs:
            log.info("No grids were found for band %s, removing from future processing..." % band)
            del bands[band]
            continue
        for grid_number,grid_job in grid_jobs[band].items():
            k = (grid_number,band_job["src_kind"])
            log.debug("Fornav job key is %s" % str(k))
            if k not in fornav_jobs:
                fornav_jobs[k] = {
                        "inputs"        : [],
                        "outputs"       : [],
                        "fbfs"          : [],
                        "out_rows"      : grid_job["out_rows"],
                        "out_cols"      : grid_job["out_cols"],
                        "swath_cols"    : grid_job["swath_cols"],
                        "swath_rows"    : grid_job["swath_rows"],
                        "rows_per_scan" : grid_job["rows_per_scan"],
                        "scans_out"     : grid_job["cr_dict"]["scans_out"],
                        "colfile"       : grid_job["cr_dict"]["colfile"],
                        "rowfile"       : grid_job["cr_dict"]["rowfile"],
                        "scan_first"    : grid_job["cr_dict"]["scan_first"]
                        }
            # Fornav dictionary
            fornav_job = fornav_jobs[k]

            grid_job["img_output"] = output_img = "output_%s_%s.img" % (band_job["band_name"],grid_number)
            grid_job["fbf_output_var"] = output_var = "result_%s_%s" % (band_job["band_name"],grid_number)
            grid_job["fbf_output"] = output_fbf = "%s.real4.%d.%d" % (output_var, fornav_job["out_cols"], fornav_job["out_rows"])
            fornav_job["inputs"].append(band_job["img_swath"])
            fornav_job["outputs"].append(output_img)
            fornav_job["fbfs"].append(output_fbf)

    # Run fornav
    for (grid_number,src_kind),fornav_job in fornav_jobs.items():
        log.info("Running fornav for grid %s, data_kind %s" % (grid_number,src_kind))
        fornav_job["result_object"] = proc_pool.apply_async(ms2gt.fornav,
                args = (
                        len(fornav_job["inputs"]),
                        fornav_job["swath_cols"],
                        fornav_job["scans_out"],
                        fornav_job["rows_per_scan"],
                        fornav_job["colfile"],
                        fornav_job["rowfile"],
                        fornav_job["inputs"],
                        fornav_job["out_cols"],
                        fornav_job["out_rows"],
                        fornav_job["outputs"]
                        ),
                kwds = dict(
                        verbose=log.getEffectiveLevel() <= logging.DEBUG,
                        swath_data_type_1="f4",
                        swath_fill_1=-999.0,
                        grid_fill_1=-999.0,
                        weight_delta_max=fornav_D,
                        weight_distance_max=fornav_d,
                        start_scan=(fornav_job["scan_first"],0)
                        ),
                )

    proc_pool.close()
    proc_pool.join()

    for (grid_number,src_kind),fornav_job in fornav_jobs.items():
        try:
            #ms2gt.fornav(
            #        len(fornav_job["inputs"]),
            #        fornav_job["swath_cols"],
            #        fornav_job["scans_out"],
            #        fornav_job["rows_per_scan"],
            #        fornav_job["colfile"],
            #        fornav_job["rowfile"],
            #        fornav_job["inputs"],
            #        fornav_job["out_cols"],
            #        fornav_job["out_rows"],
            #        fornav_job["outputs"],
            #        verbose=log.getEffectiveLevel() <= logging.DEBUG,
            #        swath_data_type_1="f4",
            #        swath_fill_1=-999.0,
            #        grid_fill_1=0,
            #        weight_delta_max=fornav_D,
            #        weight_distance_max=fornav_d,
            #        start_scan=(fornav_job["scan_first"],0)
            #        )
            fornav_job["result_object"].get()
        except StandardError:
            log.warning("fornav failed for %s band, grid %s, data_kind %s" % (kind,grid_number,src_kind))
            log.debug("Exception was:", exc_info=1)
            log.warning("Cleaning up for this job...")
            for band in bands.keys():
                log.error("Removing %s%s because of bad fornav execution" % (kind,band))
                if grid_number in grid_jobs[band]:
                    del grid_jobs[band][grid_number]
                if len(grid_jobs[band]) == 0:
                    log.error("The last grid job for %s%s was removed" % (kind,band))
                    del grid_jobs[band]
                    del bands[band]
                    SUCCESS |= FORNAV_FAIL
                if len(grid_jobs) == 0:
                    log.error("All bands for %s were removed, quitting..." % (kind))
                    return SUCCESS or UNKNOWN_FAIL

        # Move and/or link recently created files
        for o_fn,fbf_name in zip(fornav_job["outputs"],fornav_job["fbfs"]):
            _force_symlink(o_fn, fbf_name)

    ### BACKEND ###
    # Rescale the image
    for band,grid_dict in grid_jobs.items():
        num_grids = len(grid_dict)
        for grid_number,grid_job in grid_dict.items():
            log.info("Running AWIPS backend for %s%s band grid %s" % (kind,band,grid_number))
            try:
                kwargs = grid_job.copy()
                del kwargs["nc_template"]
                del kwargs["nc_filename"]
                del kwargs["data_kind"]
                del kwargs["start_dt"]
                awips_backend(
                        grid_job["fbf_output"],
                        grid_job["nc_template"],
                        grid_job["nc_filename"],
                        kind,
                        band,
                        grid_job["data_kind"],
                        grid_job["start_dt"],
                        **kwargs
                        )
            except StandardError:
                log.error("Error in the AWIPS backend for %s%s in grid %s" % (kind,band,grid_number))
                log.debug("AWIPS backend error:", exc_info=1)
                num_grids -= 1

        if num_grids == 0:
            log.warning("AWIPS backend failed for all grids for %s%s" % (kind,band))
            SUCCESS |= BACKEND_FAIL

    return SUCCESS

def run_viirs2awips(filepaths,
        fornav_D=None, fornav_d=None,
        forced_grid=None,
        forced_gpd=None, forced_nc=None,
        multiprocess=True, num_procs=1):
    """Go through the motions of converting
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
    filepaths = [ os.path.abspath(x) for x in sorted(filepaths) ]

    # Get grid templates and figure out the AWIPS product id to use
    if (forced_nc is None or forced_gpd is None) and forced_grid and forced_grid not in GRID_TEMPLATES:
        log.error("Unknown or unconfigured grid number %s in grids/*" % forced_grid)
        return -1

    M_files = sorted(set([ x for x in filepaths if os.path.split(x)[1].startswith("SVM") ]))
    I_files = sorted(set([ x for x in filepaths if os.path.split(x)[1].startswith("SVI") ]))
    DNB_files = sorted(set([ x for x in filepaths if os.path.split(x)[1].startswith("SVDNB") ]))
    all_used = set(M_files + I_files + DNB_files)
    all_provided = set(filepaths)
    not_used = all_provided - all_used
    if len(not_used):
        log.warning("Didn't know what to do with\n%s" % "\n".join(list(not_used)))

    from multiprocessing import Process
    pM = None
    pI = None
    pDNB = None
    exit_status = 0
    if len(M_files) != 0 and len([x for x in BANDS if x.startswith("M") ]) != 0:
        log.debug("Processing M files")
        try:
            if multiprocess:
                pM = Process(target=process_kind, args=(M_files,), kwargs=dict(
                    fornav_D=fornav_D, fornav_d=fornav_d,
                    forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc,
                    num_procs=num_procs))
                pM.start()
            else:
                stat = process_kind(M_files, fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc, num_procs=num_procs)
                exit_status = exit_status or stat
        except StandardError:
            log.error("Could not process M files", exc_info=1)
            exit_status = exit_status or len(M_files)

    if len(I_files) != 0 and len([x for x in BANDS if x.startswith("I") ]) != 0:
        log.debug("Processing I files")
        try:
            if multiprocess:
                pI = Process(target=process_kind, args=(I_files,), kwargs=dict(
                    fornav_D=fornav_D, fornav_d=fornav_d,
                    forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc,
                    num_procs=num_procs))
                pI.start()
            else:
                stat = process_kind(I_files, fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc, num_procs=num_procs)
                exit_status = exit_status or stat
        except StandardError:
            log.error("Could not process I files", exc_info=1)
            exit_status = exit_status or len(I_files)

    if len(DNB_files) != 0 and len([x for x in BANDS if x.startswith("DNB") ]) != 0:
        log.debug("Processing DNB files")
        try:
            if multiprocess:
                pDNB = Process(target=process_kind, args=(DNB_files,), kwargs=dict(
                    fornav_D=fornav_D, fornav_d=fornav_d,
                    forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc,
                    num_procs=num_procs))
                pDNB.start()
            else:
                stat = process_kind(DNB_files, fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc, num_procs=num_procs)
                exit_status = exit_status or stat
        except StandardError:
            log.error("Could not process DNB files", exc_info=1)
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
    import optparse
    usage = """
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
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_option('-D', dest='fornav_D', default=40,
            help="Specify the -D option for fornav")
    parser.add_option('-d', dest='fornav_d', default=2,
            help="Specify the -d option for fornav")
    parser.add_option('-b', dest='force_band', default=None,
            help="Specify the bands that should be allowed in 'I01' or 'DNB' or 'I' format")
    parser.add_option('-f', dest='get_files', default=False, action="store_true",
            help="Specify that hdf files are listed, not a directory")
    parser.add_option('-g', '--grid', dest='forced_grid', default=None,
            help="Force remapping to only one grid")
    parser.add_option('--sp', dest='single_process', default=False, action='store_true',
            help="Processing is sequential instead of one process per kind of band")
    parser.add_option('--num-procs', dest="num_procs", default=1,
            help="Specify number of processes that can be used to run ll2cr/fornav calls in parallel")
    parser.add_option('--gpd', dest='forced_gpd', default=None,
            help="Specify a different gpd file to use")
    parser.add_option('--nc', dest='forced_nc', default=None,
            help="Specify a different nc file to use")
    parser.add_option('-k', '--keep', dest='remove_prev', default=True, action='store_true',
            help="Don't delete any files that were previously made (WARNING: processing may not run successfully)")
    options,args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])

    fornav_D = int(options.fornav_D)
    fornav_d = int(options.fornav_d)
    num_procs = int(options.num_procs)
    forced_grid = options.forced_grid
    if options.forced_gpd is not None and not os.path.exists(options.forced_gpd):
        log.error("Specified gpd file does not exist '%s'" % options.forced_gpd)
        return -1
    if options.forced_nc is not None and not os.path.exists(options.forced_nc):
        log.error("Specified nc file does not exist '%s'" % options.forced_nc)
        return -1

    if len(args) == 0 or "help" in args:
        parser.print_help()
        sys.exit(0)
    elif len(args) == 1 and "remove" in args:
        log.debug("Removing previous products")
        remove_products()
        sys.exit(0)

    if options.get_files:
        if len(args) < 2:
            log.error("Wrong number of arguments, need 2 or more hdf files")
            parser.print_help()
            return -1
        hdf_files = args[:]
    elif len(args) == 1:
        base_dir = os.path.abspath(args[0])
        hdf_files = [ os.path.join(base_dir,x) for x in os.listdir(base_dir) if x.startswith("SV") and x.endswith(".h5") ]
    else:
        log.error("Wrong number of arguments")
        parser.print_help()
        return -1

    remove_prev = True
    if remove_prev:
        log.debug("Removing any previous files")
        remove_products()

    if options.force_band is not None:
        if len( [ x for x in BANDS.keys() if x.startswith(options.force_band) ] ) == 0:
            log.error("Unknown band %s" % options.force_band)
            parser.print_help()
            return -1
        hdf_files = [ x for x in hdf_files if os.path.split(x)[1].startswith("SV" + options.force_band) ]
        stat = process_kind(hdf_files, fornav_D=fornav_D, fornav_d=fornav_d,
                forced_gpd=options.forced_gpd, forced_nc=options.forced_nc, forced_grid=forced_grid, num_procs=num_procs)
    else:
        stat = run_viirs2awips(hdf_files, fornav_D=fornav_D, fornav_d=fornav_d,
                    forced_gpd=options.forced_gpd, forced_nc=options.forced_nc, forced_grid=forced_grid,
                    multiprocess=not options.single_process, num_procs=num_procs)

    sys.exit(stat)

if __name__ == "__main__":
    sys.exit(main())

