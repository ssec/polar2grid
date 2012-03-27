"""Script for going from VIIRS .h5 files to a AWIPS compatible
NetCDF file.

Author: David Hoese,davidh,SSEC
"""
import os
import sys
import logging
import numpy
from glob import glob
from netCDF4 import Dataset

from viirs_imager_to_swath import file_appender
from adl_guidebook import file_info,geo_info,read_file_info,read_geo_info
from rescale import rescale,post_rescale_dnb
from keoni.fbf import Workspace
import ms2gt
import awips_netcdf

log = logging.getLogger(__name__)

script_dir = os.path.split(os.path.realpath(__file__))[0]
default_grids_dir = os.path.join(script_dir, "grids")
default_templates_file = os.path.join(script_dir, "templates.conf")
TEMPLATE_FILE = os.environ.get("VIIRS_TEMPLATE", default_templates_file)
GRIDS_DIR = os.environ.get("VIIRS_GRIDS_DIR", default_grids_dir)

GRID_TEMPLATES = {}
# Get a set of the "grid211" part of every template
for t in set([x[:7] for x in os.listdir(GRIDS_DIR) if x.startswith("grid")]):
    nc_temp = t + ".nc"
    gpd_temp = t + ".gpd"
    nc_path = os.path.join(GRIDS_DIR, nc_temp)
    gpd_path = os.path.join(GRIDS_DIR, gpd_temp)
    grid_number = int(t[4:7])
    if os.path.exists(nc_path) and os.path.exists(gpd_path):
        GRID_TEMPLATES[grid_number] = (gpd_path, nc_path)
del t,nc_temp,gpd_temp,nc_path,gpd_path,grid_number

# grid -> band -> (product_id,nc_name)
GRIDS = {}
# band -> grid -> (product_id,nc_name)
BANDS = {}
for line in open(TEMPLATE_FILE):
    # For comments
    if line.startswith("#"): continue
    parts = line.strip().split(",")
    if len(parts) < 4:
        print "ERROR: Need at least 4 columns in templates.conf (%s)" % line
    product_id = parts[0]
    grid_number = int(parts[1])
    band = parts[2]
    if len(band) != 3:
        print "ERROR: Expected 3 characters for band got %d (%s)" % (len(band),band)
    nc_name = parts[3]

    if grid_number not in GRIDS:
        GRIDS[grid_number] = {}
    if band in GRIDS[grid_number]:
        print "ERROR: templates.conf contains two or more entries for grid %d and band %s" % (grid_number,band)
        sys.exit(-1)

    if band not in BANDS:
        BANDS[band] = {}
    if grid_number in BANDS[band]:
        print "ERROR: templates.conf contains two or more entries for grid %d and band %s" % (grid_number,band)
        sys.exit(-1)

    val = (product_id,nc_name)
    BANDS[band][grid_number] = val
    GRIDS[grid_number][band] = val
del line,val,parts,product_id,band,nc_name

def _get_templates(grid_number, gpd=None, nc=None):
    if grid_number not in GRID_TEMPLATES:
        if nc is not None and gpd is not None:
            return (gpd,nc)
        else:
            log.error("Couldn't find grid %d in grid templates" % grid_number)
            raise ValueError("Couldn't find grid %d in grid templates" % grid_number)
    else:
        use_gpd = GRID_TEMPLATES[grid_number][0]
        use_nc = GRID_TEMPLATES[grid_number][1]
        use_gpd = gpd or use_gpd
        use_nc = nc or use_nc
        return (use_gpd,use_nc)

def _get_awips_info(kind, band, grid_number):
    if kind == "DNB":
        bname = kind
    else:
        bname = kind + band
    if bname not in BANDS or grid_number not in GRIDS:
        log.error("Band %s or grid %d not found in templates.conf" % (bname,grid_number))
        raise ValueError("Band %s or grid %d not found in templates.conf" % (bname,grid_number))
    else:
        return GRIDS[grid_number][bname]

def _get_grid_info(kind, band, grid_number, gpd=None, nc=None):
    """Assumes _verify_grid was already run to verify that the information
    was available.
    """
    awips_info = _get_awips_info(kind, band, grid_number)
    temp_info = _get_templates(grid_number, gpd, nc)

    # Get number of rows and columns for the output grid
    nc = Dataset(temp_info[1], "r")
    (out_rows,out_cols) = nc.variables["image"].shape
    log.debug("Number of output columns calculated from NC template %d" % out_cols)
    log.debug("Number of output rows calculated from NC template %d" % out_rows)

    grid_info = {}
    grid_info["grid_number"] = grid_number
    grid_info["product_id"] = awips_info[0]
    grid_info["nc_format"] = awips_info[1]
    grid_info["gpd_template"] = temp_info[0]
    grid_info["nc_template"] = temp_info[1]
    grid_info["out_rows"] = out_rows
    grid_info["out_cols"] = out_cols
    return grid_info

def _verify_grid(kind, band, grid_number, gpd=None, nc=None):
    """Return true if this grid is known to the configuration files/dirs.
    """
    try:
        _get_templates(grid_number, gpd, nc)
    except StandardError:
        return False

    try:
        _get_awips_info(kind, band, grid_number)
    except StandardError:
        return False

    return True

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
    ### NAV STUFF ###
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
            raise ValueError("Error reading data from %s for band kind %s" % (ginfo["geo_path"],kind), exc_info=1)

        ginfos[gname] = ginfo

        # ll2cr/fornav hate entire scans that are bad
        scan_quality = ginfo["scan_quality"]
        if len(scan_quality[0]) != 0:
            ginfo["lat_data"] = numpy.delete(ginfo["lat_data"], scan_quality, axis=0)
            ginfo["lon_data"] = numpy.delete(ginfo["lon_data"], scan_quality, axis=0)

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
        ginfo = ginfos[gname]
        lafa.append(ginfo["lat_data"])
        lofa.append(ginfo["lon_data"])
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
    del lafa
    del lofa

    ### END of NAV FILES STUFF ###
    return start_dt,swath_rows,swath_cols,rows_per_scan,fbf_lat,fbf_lon

def _determine_grid(kind, start_dt, bands, ginfos, grid_jobs, grids, forced_grid=None, forced_gpd=None, forced_nc=None):
    # Detemine grids
    if forced_grid is not None:
        for band in bands.keys():
            if _verify_grid(kind, band, forced_grid):
                grid_info = _get_grid_info(kind, band, forced_grid, gpd=forced_gpd, nc=forced_nc)
                grid_info["start_dt"] = start_dt
                if band not in grid_jobs: grid_jobs[band] = {}
                grid_jobs[band][grid_info["grid_number"]] = grid_info.copy()
                if grid_info["grid_number"] not in grids: grids.append(grid_info["grid_number"])
            else:
                log.warning("The template files don't have grid %d for %s%s" % (forced_grid, kind, band))
                log.warning("Removing job...")
                del bands[band]
                if len(bands) == 0:
                    # We are out of jobs
                    log.error("The last job was removed, no more to do, quitting...")
                    raise ValueError("The last job was removed, no more to do, quitting...")
    else:
        log.error("There is no grid determination formula implemented yet")
        raise NotImplementedError("There is no grid determination formula implemented yet")

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
    #fbf_lat_var = None
    #fbf_lon_var = None
    img_lat = None
    img_lon = None

    # Identify the kind of these files
    kind = None

    # Get image and geonav file info
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

    ### NAV FILES ###
    # Get nav data and put it in fbf files
    start_dt,swath_rows,swath_cols,rows_per_scan,fbf_lat,fbf_lon = process_geo(kind, gfiles, ginfos)
    #fbf_lat_var = fbf_lat.split(".")[0]
    #fbf_lon_var = fbf_lon.split(".")[0]
    swath_scans = swath_rows/rows_per_scan

    # Determine grid
    _determine_grid(kind, start_dt, bands, ginfos, grid_jobs, grids, forced_grid, forced_gpd, forced_nc)

    # Delete data that isn't needed anymore (free up some memory)
    for ginfo in ginfos.values():
        del ginfo["lat_data"]
        del ginfo["lon_data"]
        del ginfo["lat_mask"]
        del ginfo["lon_mask"]

    # Move nav fbf files to img files to be used by ll2cr
    img_lat = "lat_%s.img" % kind
    img_lon = "lon_%s.img" % kind
    _force_symlink(fbf_lat, img_lat)
    _force_symlink(fbf_lon, img_lon)

    # Run ll2cr
    for grid_number in grids:
        gpd_template = None
        for grid_job in [ x[grid_number] for x in grid_jobs.values() if grid_number in x ]:
            # Make every grid_job know what the col and row files are tagged with
            log.debug("Adding ll2cr_tag to grid %d" % grid_number)
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
            log.warning("ll2cr failed for %s band, grid %d" % (kind,grid_number))
            log.warning("Won't process for this grid...")
            del grids[grid_number]
            for band in bands.keys():
                if grid_number in grid_jobs[band]:
                    log.error("Removing %s%s for grid %d because of bad ll2cr execution" % (kind,band,grid_number))
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

    # Get image data
    for band,band_job in bands.items():
        for finfo in band_job["finfos"]:
            try:
                # XXX: May need to pass the lat/lon masks
                read_file_info(finfo)
            except StandardError:
                log.error("Error reading data from %s" % finfo["img_path"], exc_info=1)
                log.error("Removing entire job associated with this file")
                del finfo
                del bands[band]
                if len(bands) == 0:
                    # We are out of jobs
                    log.error("The last job was removed, no more to do, quitting...")
                    raise ValueError("The last job was removed, no more to do, quitting...")
                # Continue on with the next band
                break

    # Cut out the data that is bad
    # ll2cr/fornav hate entire scans that are bad
    for idx,gname in enumerate(gfiles):
        ginfo = ginfos[gname]
        scan_quality = ginfo["scan_quality"]
        if len(scan_quality[0]) != 0:
            # Take the proper image file for each geonav file
            for finfo in [ x["finfos"][idx] for x in bands.values() ]:
                log.info("Removing %d bad scans from %s" % (len(scan_quality[0])/finfo["rows_per_scan"], finfo["img_path"]))
                finfo["image_data"] = numpy.delete(finfo["image_data"], scan_quality, axis=0)
                finfo["day_mask"] = numpy.delete(finfo["day_mask"], scan_quality, axis=0)
                finfo["night_mask"] = numpy.delete(finfo["night_mask"], scan_quality, axis=0)

    # Write image data and day/night mask data to fbf files
    for band,band_job in bands.items():
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

        for finfo in band_job["finfos"]:
            imfa.append(finfo["image_data"])
            dmask_fa.append(finfo["day_mask"])
            nmask_fa.append(finfo["night_mask"])
            del finfo

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

        del imfa
        del dmask_fa
        del nmask_fa
        imfo.close()
        dmask_fo.close()
        nmask_fo.close()
        del band_job

    # Free up some memory by deleting image data
    for band,band_job in bands.items():
        for finfo in band_job["finfos"]:
            del finfo["image_data"]
            del finfo["image_mask"]
            del finfo["day_mask"]
            del finfo["night_mask"]
            del finfo["scan_quality"]

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
                log.error("Could not open img file %s" % band_job["fbf_nmask"])
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
        else:
            print kind,band
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
                        "out_rows"      : grid_job["out_cols"],
                        "out_cols"      : grid_job["out_rows"]
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
            log.warning("fornav failed for %s band, grid %d" % (kind,grid_number))
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
        remove_prev=True):
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
    forced_grid = forced_grid and int(forced_grid)
    filepaths = [ os.path.abspath(x) for x in sorted(filepaths) ]

    # Get grid templates and figure out the AWIPS product id to use
    if (forced_nc is None or forced_gpd is None) and forced_grid and forced_grid not in GRID_TEMPLATES:
        log.error("Unknown or unconfigured grid number %d in grids/*" % forced_grid)
        return -1

    if remove_prev:
        log.debug("Removing any previous files")
        remove_products()

    M_files = sorted(set([ x for x in filepaths if os.path.split(x)[1].startswith("SVM") ]))
    I_files = sorted(set([ x for x in filepaths if os.path.split(x)[1].startswith("SVI") ]))
    DNB_files = sorted(set([ x for x in filepaths if os.path.split(x)[1].startswith("SVDNB") ]))
    all_used = set(M_files + I_files + DNB_files)
    all_provided = set(filepaths)
    not_used = all_provided - all_used
    if len(not_used):
        log.warning("Didn't know what to do with %s" % ", ".join(list(not_used)))

    from multiprocessing import Process
    pM = None
    pI = None
    pDNB = None
    if len(M_files) != 0:
        log.debug("Processing M files")
        try:
            pM = Process(target=process_kind, args=(M_files,), kwargs=dict(fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc))
            #process_kind(M_files, fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc)
            pM.start()
        except StandardError:
            log.error("Could not process M files", exc_info=1)

    if len(I_files) != 0:
        log.debug("Processing I files")
        try:
            pI = Process(target=process_kind, args=(I_files,), kwargs=dict(fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc))
            #process_kind(I_files, fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc)
            pI.start()
        except StandardError:
            log.error("Could not process I files", exc_info=1)

    if len(DNB_files) != 0:
        log.debug("Processing DNB files")
        try:
            pDNB = Process(target=process_kind, args=(DNB_files,), kwargs=dict(fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc))
            #process_kind(DNB_files, fornav_D=fornav_D, fornav_d=fornav_d, forced_grid=forced_grid, forced_gpd=forced_gpd, forced_nc=forced_nc)
            pDNB.start()
        except StandardError:
            log.error("Could not process DNB files", exc_info=1)

    log.debug("Waiting for subprocesses")
    if pM is not None: pM.join()
    if pI is not None: pI.join()
    if pDNB is not None: pDNB.join()

def main():
    import optparse
    usage = """%prog <grid #> file1.h5 file2.h5 ..."""
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_option('-D', dest='fornav_D', default=40,
            help="Specify the -D option for fornav")
    parser.add_option('-d', dest='fornav_d', default=2,
            help="Specify the -d option for fornav")
    parser.add_option('-f', dest='get_files', default=False, action="store_true",
            help="Specify that hdf files are listed, not a directory")
    parser.add_option('-g', '--grid', dest='forced_grid', default=None,
            help="Force remapping to only one grid")
    parser.add_option('--gpd', dest='forced_gpd', default=None,
            help="Specify a different gpd file to use")
    parser.add_option('--nc', dest='forced_nc', default=None,
            help="Specify a different nc file to use")
    options,args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])

    log.debug("Grid directory that was used %s" % GRIDS_DIR)
    log.debug(repr(GRID_TEMPLATES))
    log.debug("Template file that was used %s" % TEMPLATE_FILE)
    log.debug(repr(GRIDS))

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
        base_dir = args[0]
        hdf_files = [ x for x in os.listdir(base_dir) if x.endswith(".h5") ]
    else:
        log.error("Wrong number of arguments")
        parser.print_help()
        return -1

    stat = run_viirs2awips(hdf_files, fornav_D=int(options.fornav_D), fornav_d=int(options.fornav_d),
                forced_gpd=options.forced_gpd, forced_nc=options.forced_nc, forced_grid=options.forced_grid)
    sys.exit(stat)

if __name__ == "__main__":
    sys.exit(main())

