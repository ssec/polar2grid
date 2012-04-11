"""Script for going from VIIRS .h5 files to a AWIPS compatible
NetCDF file.

Author: David Hoese,davidh,SSEC
"""
import os
import sys
import logging
import numpy
from glob import glob

from viirs_imager_to_swath import file_appender
from adl_guidebook import file_info,geo_info,read_file_info,read_geo_info
from rescale import rescale,post_rescale_dnb
from keoni.fbf import Workspace
import ms2gt
import awips_netcdf
from awips_config import GRIDS,BANDS,GRID_TEMPLATES,SHAPES,verify_config,get_grid_info

log = logging.getLogger(__name__)

def _glob_file(pat):
    tmp = glob(pat)
    if len(tmp) != 1:
        log.error("There were no files or more than one fitting the pattern %s" % pat)
        raise ValueError("There were no files or more than one fitting the pattern %s" % pat)
    return tmp[0]

def _force_symlink(dst, linkname):
    if os.path.exists(linkname):
        log.info("Removing old file %s" % dst)
        os.remove(linkname)
    log.debug("Symlinking %s -> %s" % (linkname,dst))
    os.symlink(dst, linkname)

def _safe_remove(fn):
    try:
        log.info("Removing %s" % fn)
        os.remove(fn)
    except StandardError:
        log.error("Could not remove %s" % fn)

def remove_products():
    for f in glob("latitude*.real4.*"):
        _safe_remove(f)
    for f in glob("longitude*.real4.*"):
        _safe_remove(f)
    for f in glob("image*.real4.*"):
        _safe_remove(f)
    for f in glob("day_mask*.int1.*"):
        _safe_remove(f)
    for f in glob("night_mask*.int1.*"):
        _safe_remove(f)
    for f in glob("dnb_rescale*.real4.*"):
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

def process_geo(kind, gfiles, ginfos):
    start_dt = None
    
    # Write lat/lon data to fbf files
    # Create fbf files
    spid = '%d' % os.getpid()
    latname = '.lat' + spid
    lonname = '.lon' + spid
    lafo = file(latname, 'wb')
    lofo = file(lonname, 'wb')
    lafa = file_appender(lafo, dtype=numpy.float32)
    lofa = file_appender(lofo, dtype=numpy.float32)

    for gname in gfiles:
        # Get lat/lon information
        try:
            ginfo = geo_info(gname)
        except StandardError:
            log.error("Error analyzing geonav filename %s" % gname)
            raise ValueError("Error analyzing geonav filename %s" % gname)

        # Read in lat/lon data
        try:
            read_geo_info(ginfo)
            # Start datetime used in product backend for NC creation
            if start_dt is None:
                start_dt = ginfo["start_dt"]
        except StandardError:
            # Can't continue without lat/lon data
            log.error("Error reading data from %s for band kind %s" % (ginfo["geo_path"],kind), exc_info=1)
            log.error("Removing any jobs associated with this kind")
            raise ValueError("Error reading data from %s for band kind %s" % (ginfo["geo_path"],kind))

        ginfos[gname] = ginfo

        # ll2cr/fornav hate entire scans that are bad
        scan_quality = ginfo["scan_quality"]
        if len(scan_quality[0]) != 0:
            ginfo["lat_data"] = numpy.delete(ginfo["lat_data"], scan_quality, axis=0)
            ginfo["lon_data"] = numpy.delete(ginfo["lon_data"], scan_quality, axis=0)

        # Append the data to the swath
        lafa.append(ginfo["lat_data"])
        lofa.append(ginfo["lon_data"])
        del ginfo["lat_data"]
        del ginfo["lon_data"]
        del ginfo["lat_mask"]
        del ginfo["lon_mask"]

    lafo.close()
    lofo.close()

    # Rename files
    suffix = '.real4.' + '.'.join(str(x) for x in reversed(lafa.shape))
    fbf_lat_var = "latitude_%s" % kind
    fbf_lon_var = "longitude_%s" % kind
    fbf_lat = fbf_lat_var + suffix
    fbf_lon = fbf_lon_var + suffix
    os.rename(latname, fbf_lat)
    os.rename(lonname, fbf_lon)
    swath_rows,swath_cols = lafa.shape
    rows_per_scan = ginfos[gfiles[0]]["rows_per_scan"]

    return start_dt,swath_rows,swath_cols,rows_per_scan,fbf_lat,fbf_lon

def _determine_grid(kind, start_dt, fbf_lat_var, fbf_lon_var, bands, ginfos, grid_jobs, grids, forced_grid=None, forced_gpd=None, forced_nc=None):
    # top bound, bottom bound, left bound, right bound, percent
    # Detemine grids
    if forced_grid is not None:
        for band in bands.keys():
            if verify_config(kind, band, forced_grid):
                grid_info = get_grid_info(kind, band, forced_grid, gpd=forced_gpd, nc=forced_nc)
                grid_info["start_dt"] = start_dt
                if band not in grid_jobs: grid_jobs[band] = {}
                grid_jobs[band][grid_info["grid_number"]] = grid_info.copy()
                if grid_info["grid_number"] not in grids: grids.append(grid_info["grid_number"])
            else:
                log.warning("The template files don't have grid %s for %s%s" % (forced_grid, kind, band))
                log.warning("Removing job...")
                del bands[band]
                if len(bands) == 0:
                    # We are out of jobs
                    log.error("The last job was removed, no more to do, quitting...")
                    raise ValueError("The last job was removed, no more to do, quitting...")
    else:
        # Get lat/lon data
        try:
            W = Workspace('.')
            lat_data = getattr(W, fbf_lat_var)[0].flatten()
            lon_data = getattr(W, fbf_lon_var)[0].flatten()
            lon_data_flipped = None
        except StandardError:
            log.error("There was an error trying to get the lat/lon swath data for grid determination")
            raise

        for grid_number in GRIDS:
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
                for band in bands.keys():
                    if verify_config(kind, band, grid_number):
                        grid_info = get_grid_info(kind, band, grid_number, gpd=forced_gpd, nc=forced_nc)
                        grid_info["start_dt"] = start_dt
                        log.debug("Adding grid %s to %s%s" % (grid_number,kind,band))
                        if band not in grid_jobs: grid_jobs[band] = {}
                        grid_jobs[band][grid_number] = grid_info.copy()
                        if grid_number not in grids: grids.append(grid_number)

def process_image(kind, gfiles, ginfos, bands, grid_jobs):
    # Get image data and save it to an fbf file
    for band,band_job in bands.items():
        # Create fbf files and appenders
        spid = '%d' % os.getpid()
        imname = '.image' + spid
        dmask_name = '.day_mask' + spid
        nmask_name = '.night_mask' + spid
        imfo = file(imname, 'wb')
        dmask_fo = file(dmask_name, 'wb')
        nmask_fo = file(nmask_name, 'wb')
        imfa = file_appender(imfo, dtype=numpy.float32)
        dmask_fa = file_appender(dmask_fo, dtype=numpy.int8)
        nmask_fa = file_appender(nmask_fo, dtype=numpy.int8)

        # Get the data
        for idx,finfo in enumerate(band_job["finfos"]):
            try:
                # XXX: May need to pass the lat/lon masks
                read_file_info(finfo)
            except StandardError:
                log.error("Error reading data from %s" % finfo["img_path"], exc_info=1)
                log.error("Removing entire job associated with this file")
                del bands[band]
                del grid_jobs[band]
                if len(bands) == 0:
                    # We are out of jobs
                    log.error("The last job was removed, no more to do, quitting...")
                    raise ValueError("The last job was removed, no more to do, quitting...")
                # Continue on with the next band
                break

            # Cut out bad data
            ginfo = ginfos[gfiles[idx]]
            if len(ginfo["scan_quality"][0]) != 0:
                log.info("Removing %d bad scans from %s" % (len(ginfo["scan_quality"][0])/finfo["rows_per_scan"], finfo["img_path"]))
                finfo["image_data"] = numpy.delete(finfo["image_data"], ginfo["scan_quality"], axis=0)
                # delete returns an array regardless, file_appender requires None
                if finfo["day_mask"] is not None:
                    finfo["day_mask"] = numpy.delete(finfo["day_mask"], ginfo["scan_quality"], axis=0)
                if finfo["night_mask"] is not None:
                    finfo["night_mask"] = numpy.delete(finfo["night_mask"], ginfo["scan_quality"], axis=0)

            # Append the data to the file
            imfa.append(finfo["image_data"])
            dmask_fa.append(finfo["day_mask"])
            nmask_fa.append(finfo["night_mask"])

            # Remove pointers to data so it gets garbage collected
            del finfo["image_data"]
            del finfo["image_mask"]
            del finfo["day_mask"]
            del finfo["night_mask"]
            del finfo["scan_quality"]

        suffix = '.real4.' + '.'.join(str(x) for x in reversed(imfa.shape))
        suffix2 = '.int1.' + '.'.join(str(x) for x in reversed(imfa.shape))
        img_base = "image_%s" % band_job["id"]
        dmask_base = "day_mask_%s" % band_job["id"]
        nmask_base = "night_mask_%s" % band_job["id"]
        fbf_img = img_base + suffix
        fbf_dmask = dmask_base + suffix2
        fbf_nmask = nmask_base + suffix2
        os.rename(imname, fbf_img)
        os.rename(dmask_name, fbf_dmask)
        os.rename(nmask_name, fbf_nmask)
        band_job["fbf_img"] = fbf_img
        band_job["fbf_dmask"] = fbf_dmask
        band_job["fbf_nmask"] = fbf_nmask
        band_job["fbf_img_var"] = img_base
        band_job["fbf_dmask_var"] = dmask_base
        band_job["fbf_nmask_var"] = nmask_base

        imfo.close()
        dmask_fo.close()
        nmask_fo.close()

    return True

def process_kind(filepaths,
        fornav_D=None, fornav_d=None,
        forced_grid=None,
        forced_gpd=None, forced_nc=None
        ):
    """Process all the files provided from start to finish,
    from filename to AWIPS NC file.
    """
    # Set up data structures and important information
    bands = {}
    grids = []
    grid_jobs = {}
    ginfos = {}
    gfiles = []

    rows_per_scan = None
    swath_rows = None
    swath_cols = None
    swath_scans = None
    start_dt = None
    fbf_lat = None
    fbf_lon = None
    fbf_lat_var = None
    fbf_lon_var = None
    img_lat = None
    img_lon = None

    # Identify the kind of these files
    kind = None

    # Get image and geonav file info
    # TODO: This could/should probably go in its own function
    bad_bands = []
    for fn in filepaths:
        try:
            finfo = file_info(fn)
        except StandardError:
            log.error("There was an error getting information from filename '%s'" % fn, exc_info=1)
            log.error("Continuing without that image file...")
            continue

        # Verify some information before adding any jobs
        if finfo["band"] in bad_bands:
            log.info("Couldn't add %s because a previous file of that band was bad" % fn)
            continue

        # Geonav file exists
        geo_glob = finfo["geo_glob"]
        try:
            finfo["geo_path"] = _glob_file(geo_glob)
        except ValueError:
            log.error("Couldn't identify geonav file for %s" % fn)
            log.error("Continuing without that image file...")
            bad_bands.append(finfo["band"])
            continue

        # We are configured to handle this band
        if finfo["kind"] + finfo["band"] not in BANDS and finfo["kind"] not in BANDS:
            log.warning("There aren't any entries for this band (%s) in templates.conf" % (finfo["kind"]+finfo["band"]))
            log.warning("Continuing without that band...")
            bad_bands.append(finfo["band"])
            continue

        # Make sure all files are of the same kind
        if kind is None:
            kind = finfo["kind"]
        elif finfo["kind"] != kind:
            log.error("Inconsistent band kinds in the files provided")
            raise ValueError("Inconsistent band kinds in the files provided")

        # Make sure geonav file is "understandable"
        if finfo["geo_path"] not in gfiles:
            if gfiles and finfo["geo_path"] < gfiles[-1]:
                # For some reason we are out of order
                log.error("Geonav file came up out of order %s in %s" % (finfo["geo-path"],gfiles))
                raise ValueError("Geonav file came up out of order %s in %s" % (finfo["geo-path"],gfiles))
            gfiles.append(finfo["geo_path"])

        # Create any locations that don't exist yet
        if finfo["band"] not in bands:
            # Fill in data structure
            bands[finfo["band"]] = {
                    "kind"          : finfo["kind"],
                    "band"          : finfo["band"],
                    "bname"         : finfo["kind"] + finfo["band"],
                    "data_kind"     : finfo["data_kind"],
                    "finfos"        : [],
                    "ifiles"        : [],
                    "fbf_img"       : None,
                    "fbf_swath"     : None,
                    "fbf_img_var"   : None,
                    "fbf_swath_var" : None,
                    "id"            : "%s%s" % (finfo["kind"],finfo["band"])
                    }

        # Add it to the proper locations for future use
        bands[finfo["band"]]["ifiles"].append(fn)
        bands[finfo["band"]]["finfos"].append(finfo)

        # Don't want any pointers holding on to the jobs if they're removed later
        del finfo

    # SANITY CHECK
    if len(bands) == 0:
        log.error("There aren't any files left to work on, quitting...")
        raise ValueError("There aren't any files left to work on, quitting...")

    for band,band_job in bands.items():
        f_len = len(band_job["ifiles"])
        g_len = len(gfiles)
        if f_len != g_len:
            log.error("Expected same number of image and navigation files for every band")
            log.error("Got (num ifiles: %d, num gfiles: %d)" % (f_len,g_len))
            raise ValueError("Found job with different number of geonav and image files")
        del band_job

    # Get nav data and put it in fbf files
    start_dt,swath_rows,swath_cols,rows_per_scan,fbf_lat,fbf_lon = process_geo(kind, gfiles, ginfos)
    fbf_lat_var = fbf_lat.split(".")[0]
    fbf_lon_var = fbf_lon.split(".")[0]
    swath_scans = swath_rows/rows_per_scan

    # Determine grid
    _determine_grid(kind, start_dt, fbf_lat_var, fbf_lon_var, bands, ginfos, grid_jobs, grids, forced_grid, forced_gpd, forced_nc)

    # Move nav fbf files to img files to be used by ll2cr
    img_lat = "lat_%s.img" % kind
    img_lon = "lon_%s.img" % kind
    _force_symlink(fbf_lat, img_lat)
    _force_symlink(fbf_lon, img_lon)

    # Run ll2cr
    for grid_number in grids:
        print "In ll2cr check"
        gpd_template = None
        for grid_job in [ x[grid_number] for x in grid_jobs.values() if grid_number in x ]:
            # Make every grid_job know what the col and row files are tagged with
            log.debug("Adding ll2cr_tag to grid %s" % grid_number)
            grid_job["ll2cr_tag"] = ll2cr_tag = "ll2cr_%s_%s" % (kind,grid_number)
            gpd_template = grid_job["gpd_template"]

        if gpd_template is None:
            log.error("InternalError, a grid is being processed that isn't in any grid jobs")
            raise ValueError("InternalError, a grid is being processed that isn't in any grid jobs")

        log.debug("Calculated %d scans in combined swath" % swath_scans)
        cr_dict = ms2gt.ll2cr(
                swath_cols,
                swath_scans,
                rows_per_scan,
                img_lat,
                img_lon,
                gpd_template,
                verbose=True,
                fill_io=(-999.0, -1e30),
                tag=ll2cr_tag
                )
        if cr_dict is None:
            log.warning("ll2cr failed for %s band, grid %s" % (kind,grid_number))
            log.warning("Won't process for this grid...")
            del grids[grid_number]
            for band in bands.keys():
                if grid_number in grid_jobs[band]:
                    log.error("Removing %s%s for grid %s because of bad ll2cr execution" % (kind,band,grid_number))
                    del grid_jobs[band][grid_number]
                    if len(grid_jobs[band]) == 0:
                        log.error("No more grids to process for %s%s, removing..." % (kind,band))
                        del grid_jobs[band]
                        del bands[band]
        else:
            for grid_job in [ x[grid_number] for x in grid_jobs.values() if grid_number in x ]:
                grid_job["cr_dict"] = cr_dict

    if len(grid_jobs) == 0:
        log.error("No more grids to process for %s, quitting..." % kind)
        raise ValueError("No more grids to process for %s, quitting..." % kind)

    ### END of NAV FILES STUFF ###

    process_image(kind, gfiles, ginfos, bands, grid_jobs)

    # Do any pre-remapping rescaling
    for band,band_job in bands.items():
        # DNB processing
        if kind == "DNB" and band == "00":
            # Rescale the image
            try:
                W = Workspace('.')
                img = getattr(W, band_job["fbf_img_var"])[0]
                data = img.copy()
                log.debug("Data min: %f, Data max: %f" % (data.min(),data.max()))
            except StandardError:
                log.error("Could not open img file %s" % band_job["fbf_img"])
                log.debug("Files matching %r" % glob(band_job["fbf_img_var"] + "*"))
                return

            scale_kwargs = {}
            try:
                day_mask = getattr(W, band_job["fbf_dmask_var"])[0]
                # Only add parameters if they're useful
                if day_mask.shape == data.shape:
                    log.debug("Adding day mask to rescaling arguments")
                    scale_kwargs["day_mask"] = day_mask.copy().astype(numpy.bool)
            except StandardError:
                log.error("Could not open day mask file %s" % band_job["fbf_dmask"])
                log.debug("Files matching %r" % glob(band_job["fbf_dmask_var"] + "*"))
                return

            try:
                night_mask = getattr(W, band_job["fbf_nmask_var"])[0]
                if night_mask.shape == data.shape:
                    log.debug("Adding night mask to rescaling arguments")
                    scale_kwargs["night_mask"] = night_mask.copy().astype(numpy.bool)
            except StandardError:
                log.error("Could not open night mask file %s" % band_job["fbf_nmask"])
                log.debug("Files matching %r" % glob(band_job["fbf_nmask_var"] + "*"))
                return

            try:
                rescaled_data = rescale(data,
                        kind=kind,
                        band=band,
                        data_kind=band_job["data_kind"],
                        **scale_kwargs)
                log.debug("Data min: %f, Data max: %f" % (rescaled_data.min(),rescaled_data.max()))
                band_job["fbf_swath_var"] = "dnb_rescale_%s" % band_job["id"]
                band_job["fbf_swath"] = "./%s.real4.%d.%d" % (band_job["fbf_swath_var"], swath_cols, swath_rows)
                rescaled_data.tofile(band_job["fbf_swath"])
            except StandardError:
                log.error("Unexpected error while rescaling data", exc_info=1)
                return

            del W,img,data,day_mask,night_mask,rescaled_data

        else:
            band_job["fbf_swath"] = band_job["fbf_img"]
            band_job["fbf_swath_var"] = band_job["fbf_img_var"]

    # Move fbf files to img files to be used by ms2gt utilities
    for band,band_job in bands.items():
        band_job["img_swath"] = "swath_%s.img" % band_job["id"]
        _force_symlink(band_job["fbf_swath"], band_job["img_swath"])

    # Build fornav call
    fornav_jobs = {}
    for band,band_job in bands.items():
        for grid_number,grid_job in grid_jobs[band].items():
            if grid_number not in fornav_jobs:
                # Swath cols and rows should be the same for all
                fornav_jobs[grid_number] = {
                        "inputs"        : [],
                        "outputs"       : [],
                        "fbfs"          : [],
                        "out_rows"      : grid_job["out_rows"],
                        "out_cols"      : grid_job["out_cols"]
                        }
            # Fornav dictionary
            fornav_job = fornav_jobs[grid_number]

            grid_job["img_output"] = output_img = "output_%s_%s.img" % (band_job["id"],grid_number)
            grid_job["fbf_output_var"] = output_var = "result_%s_%s" % (band_job["id"],grid_number)
            grid_job["fbf_output"] = output_fbf = "%s.real4.%d.%d" % (output_var, fornav_job["out_cols"], fornav_job["out_rows"])
            fornav_job["inputs"].append(band_job["img_swath"])
            fornav_job["outputs"].append(output_img)
            fornav_job["fbfs"].append(output_fbf)

    # Run fornav
    for grid_number,fornav_job in fornav_jobs.items():
        # cr_dicts are the same for all bands of that grid, so just pick one
        cr_dict = [ x[grid_number]["cr_dict"] for x in grid_jobs.values() if grid_number in x ][0]
        fornav_dict = ms2gt.fornav(
                len(fornav_job["inputs"]),
                swath_cols,
                cr_dict["scans_out"],
                rows_per_scan,
                cr_dict["colfile"],
                cr_dict["rowfile"],
                fornav_job["inputs"],
                fornav_job["out_cols"],
                fornav_job["out_rows"],
                fornav_job["outputs"],
                verbose=True,
                swath_data_type_1="f4",
                swath_fill_1=-999.0,
                grid_fill_1=0,
                weight_delta_max=fornav_D,
                weight_distance_max=fornav_d,
                start_scan=(cr_dict["scan_first"],0)
                )
        if fornav_dict is None:
            log.warning("fornav failed for %s band, grid %s" % (kind,grid_number))
            log.warning("Cleaning up for this job...")
            for band in bands.keys():
                log.error("Removing %s%s because of bad fornav execution" % (kind,band))
                if grid_number in grid_jobs[band]:
                    del grid_jobs[band][grid_number]
                if len(grid_jobs[band]):
                    log.error("The last grid job for %s%s was removed" % (kind,band))
                    del grid_jobs[band]
                    del bands[band]
                if len(grid_jobs) == 0:
                    log.error("All bands for %s were removed, quitting..." % (kind))
                    raise ValueError("All bands for %s were removed, quitting..." % (kind))

        # Move and/or link recently created files
        for o_fn,fbf_name in zip(fornav_job["outputs"],fornav_job["fbfs"]):
            _force_symlink(o_fn, fbf_name)

    ### BACKEND ###
    # Rescale the image
    for band,grid_dict in grid_jobs.items():
        for grid_number,grid_job in grid_dict.items():
            try:
                W = Workspace('.')
                img = getattr(W, grid_job["fbf_output_var"])[0]
                data = img.copy()
                log.debug("Data min: %f, Data max: %f" % (data.min(),data.max()))
                scale_kwargs = {}
            except StandardError:
                log.error("Could not open img file %s" % grid_job["fbf_output"])
                log.debug("Files matching %r" % glob(grid_job["fbf_output_var"] + "*"))
                return

            if kind != "DNB":
                try:
                    rescaled_data = rescale(data,
                            kind=kind,
                            band=band,
                            data_kind=bands[band]["data_kind"],
                            **scale_kwargs)
                    log.debug("Data min: %f, Data max: %f" % (rescaled_data.min(),rescaled_data.max()))
                except StandardError:
                    log.error("Unexpected error while rescaling data", exc_info=1)
                    return
            else:
                rescaled_data = post_rescale_dnb(data)

            # Make NetCDF files
            grid_job["nc_file"] = grid_job["start_dt"].strftime(grid_job["nc_format"])
            nc_stat = awips_netcdf.fill(grid_job["nc_file"], rescaled_data, grid_job["nc_template"], grid_job["start_dt"])
            if not nc_stat:
                log.error("Error while creating NC file")
                return

def run_viirs2awips(filepaths,
        fornav_D=None, fornav_d=None,
        forced_grid=None,
        forced_gpd=None, forced_nc=None,
        multiprocess=True):
    """Go through the motions of converting
    a VIIRS h5 file into a AWIPS NetCDF file.

    1. adl_guidebook.py         : Get file info/data
    2. viirs_imager_to_swath.py : Concatenate data
    3. Calculat Grid            : Figure out what grids the data fits in
    4. ll2cr
    5. fornav
    6. rescale.py
    7. awips_netcdf.py
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
    if len(M_files) != 0 and len([x for x in BANDS if x.startswith("M") ]) != 0:
        log.debug("Processing M files")
        try:
            if multiprocess:
                pM = Process(target=process_kind, args=(M_files,), kwargs=dict(fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc))
                pM.start()
            else:
                process_kind(M_files, fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc)
        except StandardError:
            log.error("Could not process M files", exc_info=1)

    if len(I_files) != 0 and len([x for x in BANDS if x.startswith("I") ]) != 0:
        log.debug("Processing I files")
        try:
            if multiprocess:
                pI = Process(target=process_kind, args=(I_files,), kwargs=dict(fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc))
                pI.start()
            else:
                process_kind(I_files, fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc)
        except StandardError:
            log.error("Could not process I files", exc_info=1)

    if len(DNB_files) != 0 and len([x for x in BANDS if x.startswith("DNB") ]) != 0:
        log.debug("Processing DNB files")
        try:
            if multiprocess:
                pDNB = Process(target=process_kind, args=(DNB_files,), kwargs=dict(fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc))
                pDNB.start()
            else:
                process_kind(DNB_files, fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc)
        except StandardError:
            log.error("Could not process DNB files", exc_info=1)

    log.debug("Waiting for subprocesses")
    if pM is not None: pM.join()
    if pI is not None: pI.join()
    if pDNB is not None: pDNB.join()

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
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
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
        hdf_files = [ os.path.join(base_dir,x) for x in os.listdir(base_dir) if x.endswith(".h5") ]
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
                forced_gpd=options.forced_gpd, forced_nc=options.forced_nc, forced_grid=forced_grid)
    else:
        stat = run_viirs2awips(hdf_files, fornav_D=fornav_D, fornav_d=fornav_d,
                    forced_gpd=options.forced_gpd, forced_nc=options.forced_nc, forced_grid=forced_grid,
                    multiprocess=not options.single_process)

    sys.exit(stat)

if __name__ == "__main__":
    sys.exit(main())

