"""Script for going from VIIRS .h5 files to a AWIPS compatible
NetCDF file.

Author: David Hoese,davidh,SSEC
"""
import os
import sys
import logging
import re
import numpy
from glob import glob
from netCDF4 import Dataset

from viirs_imager_to_swath import _test_fbf
from rescale import rescale
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

TEMPLATES = {}
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
    if (grid_number,band) in TEMPLATES:
        print "ERROR: templates.conf contains two or more entries for grid %d and band %s" % (grid_number,band)
        sys.exit(-1)
    TEMPLATES[(grid_number,band)] = (product_id,nc_name)


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
    os.symlink(dst, linkname)

def _safe_remove(fn):
    try:
        log.info("Removing %s" % fn)
        os.remove(fn)
    except StandardError:
        log.error("Could not remove %s" % fn)

def remove_products():
    for f in glob("latitude.real4.*"):
        _safe_remove(f)
    for f in glob("longitude.real4.*"):
        _safe_remove(f)
    for f in glob("image.real4.*"):
        _safe_remove(f)
    for f in glob("day_mask.int1.*"):
        _safe_remove(f)
    for f in glob("night_mask.int1.*"):
        _safe_remove(f)
    for f in glob("swath.img"):
        _safe_remove(f)
    for f in glob("lat.img"):
        _safe_remove(f)
    for f in glob("lon.img"):
        _safe_remove(f)

    for f in glob("*_rows_*.img"):
        _safe_remove(f)
    for f in glob("*_cols_*.img"):
        _safe_remove(f)

    for f in glob("output.img"):
        _safe_remove(f)
    for f in glob("result.real4.*"):
        _safe_remove(f)

    nc_files = glob("SSEC_AWIPS_VIIRS*")
    if len(nc_files) > 1:
        log.error("There are more than one NC file found, not sure what to remove %s" % str(nc_files))
        sys.exit(-1)
    elif len(nc_files) == 1:
        _safe_remove(nc_files[0])

def run_viirs2awips(grid_number, filepaths,
        fornav_D=None, fornav_d=None,
        forced_gpd=None, forced_nc=None):
    """Go through the motions of converting
    a VIIRS h5 file into a AWIPS NetCDF file.

    1. viirs_imager_to_swath.py
    2. ll2cr
    3. fornav
    4. rescale.py
    5. awips_netcdf.py
    """
    # Get grid templates and figure out the AWIPS product id to use
    if (forced_nc is None or forced_gpd is None) and grid_number not in GRID_TEMPLATES:
        log.error("Unknown or unconfigured grid number %d in grids/*" % grid_number)
        return
    band = os.path.split(filepaths[0])[1][2:5]
    if (grid_number,band) not in TEMPLATES:
        log.error("Unknown or unconfigured grid number %d and band %s in templates.conf" % (grid_number, band))
        return

    log.debug("Removing any previous files")
    remove_products()

    file_info = {}
    file_info["grid_gpd"] = forced_gpd or GRID_TEMPLATES[grid_number][0]
    log.debug("Using grid template gpd %s" % file_info["grid_gpd"])
    file_info["nc_template"] = forced_nc or GRID_TEMPLATES[grid_number][1]
    log.debug("Using grid template nc %s" % file_info["nc_template"])
    file_info["nc_format"] = TEMPLATES[(grid_number,band)][1]
    log.debug("Using NC name format %s" % file_info["nc_format"])
    # Create latitude.real4.*
    # Create longitude.real4.*
    # Create image.real4.*
    # Create don.int1.* (possibly empty)
    swath_info = _test_fbf(*filepaths)

    # Get filenames for important files made from swath maker
    file_info["fbf_lat"] = _glob_file("latitude.real4.*")
    file_info["fbf_lon"] = _glob_file("longitude.real4.*")
    file_info["fbf_img"] = _glob_file("image.real4.*")
    file_info["fbf_dmask"] = _glob_file("day_mask.int1.*")
    file_info["fbf_nmask"] = _glob_file("night_mask.int1.*")

    # Extract information from image filename
    swath_reg = r'image.real4.(?P<swath_cols>\d+).(?P<swath_rows>\d+)'
    SWATH_FINFO_REG = re.compile(swath_reg)
    swath_dict = SWATH_FINFO_REG.match(file_info["fbf_img"]).groupdict()
    swath_info["swath_rows"] = int(swath_dict["swath_rows"])
    swath_info["swath_cols"] = int(swath_dict["swath_cols"])
    log.debug("Swath maker returned %d rows and %d cols" % (swath_info["swath_rows"], swath_info["swath_cols"]))

    # Move and/or link recently created files
    _force_symlink(file_info["fbf_lat"], "lat.img")
    file_info["img_lat"] = "lat.img"
    _force_symlink(file_info["fbf_lon"], "lon.img")
    file_info["img_lon"] = "lon.img"
    _force_symlink(file_info["fbf_img"], "swath.img")
    file_info["img_swath_orig"] = "swath.img"

    # Get number of rows and columns for the output grid
    nc = Dataset(file_info["nc_template"], "r")
    (out_rows,out_cols) = nc.variables["image"].shape
    log.debug("Number of output columns calculated from NC template %d" % out_cols)
    log.debug("Number of output rows calculated from NC template %d" % out_rows)

    # DNB is a special case
    if swath_info["kind"] == "DNB":
        # Rescale the image
        try:
            W = Workspace('.')
            img = getattr(W, "image")[0]
            data = img.copy()
            log.debug("Data min: %f, Data max: %f" % (data.min(),data.max()))
        except StandardError:
            log.error("Could not open img file %s" % file_info["fbf_img"])
            log.debug("Files matching %r" % glob("image.*"))
            return

        scale_kwargs = {}
        try:
            day_mask = W.day_mask[0]
            # Only add parameters if they're useful
            if day_mask.shape == data.shape:
                log.debug("Adding day mask to rescaling arguments")
                scale_kwargs["day_mask"] = day_mask.copy().astype(numpy.bool)
        except StandardError:
            log.error("Could not open day_mask file %s" % file_info["fbf_dmask"])
            log.debug("Files matching %r" % glob("day_mask.*"))
            return

        try:
            night_mask = W.night_mask[0]
            if night_mask.shape == data.shape:
                log.debug("Adding night mask to rescaling arguments")
                scale_kwargs["night_mask"] = night_mask.copy().astype(numpy.bool)
        except StandardError:
            log.error("Could not open img file %s" % file_info["fbf_nmask"])
            log.debug("Files matching %r" % glob("night_mask.*"))
            return

        try:
            rescaled_data = rescale(data,
                    kind=swath_info["kind"],
                    band=swath_info["band"],
                    data_kind=swath_info["data_kind"],
                    **scale_kwargs)
            log.debug("Data min: %f, Data max: %f" % (rescaled_data.min(),rescaled_data.max()))
            file_info["img_swath"] = "./dnb_rescale.real4.%d.%d" % (swath_info["swath_cols"],swath_info["swath_rows"])
            rescaled_data.tofile(file_info["img_swath"])
        except StandardError:
            log.error("Unexpected error while rescaling data", exc_info=1)
            return
    else:
        file_info["img_swath"] = file_info["img_swath_orig"]

    # Run ll2cr
    # FIXME: The num_rows and num_cols returned by the ll2cr wrapper are wrong
    swath_info["swath_scans"] = int(swath_info["swath_rows"]/swath_info["rows_per_scan"])
    log.debug("Calculated %d scans in combined swath" % swath_info["swath_scans"])
    cr_dict = ms2gt.ll2cr(
            swath_info["swath_cols"],
            swath_info["swath_scans"],
            swath_info["rows_per_scan"],
            file_info["img_lat"],
            file_info["img_lon"],
            file_info["grid_gpd"],
            verbose=True,
            fill_io=(-999.0, -1e30),
            tag="ll2cr"
            )
    if cr_dict is None:
        log.error("ll2cr didn't return any information")
        return

    # Run fornav
    file_info["img_output"] = "output.img"
    fornav_dict = ms2gt.fornav(
            1,
            swath_info["swath_cols"],
            cr_dict["scans_out"],
            swath_info["rows_per_scan"],
            cr_dict["colfile"],
            cr_dict["rowfile"],
            file_info["img_swath"],
            out_cols,
            out_rows,
            file_info["img_output"],
            verbose=True,
            swath_data_type_1="f4",
            swath_fill_1=-999.0,
            grid_fill_1=0,
            weight_delta_max=fornav_D,
            weight_distance_max=fornav_d,
            start_scan=(cr_dict["scan_first"],0)
            )
    if fornav_dict is None:
        log.error("fornav didn't return any information")
        return

    # Move and/or link recently created files
    file_info["fbf_output"] = "result.real4.%d.%d" % (out_cols,out_rows)
    _force_symlink(file_info["img_output"], file_info["fbf_output"])

    # Rescale the image, as long as it isn't DNB
    try:
        W = Workspace('.')
        img = getattr(W, "result")[0]
        data = img.copy()
        log.debug("Data min: %f, Data max: %f" % (data.min(),data.max()))
        scale_kwargs = {}
    except StandardError:
        log.error("Could not open img file %s" % file_info["fbf_output"])
        log.debug("Files matching %r" % glob("result.*"))
        return

    if swath_info["kind"] != "DNB":
        try:
            rescaled_data = rescale(data,
                    kind=swath_info["kind"],
                    band=swath_info["band"],
                    data_kind=swath_info["data_kind"],
                    **scale_kwargs)
            log.debug("Data min: %f, Data max: %f" % (rescaled_data.min(),rescaled_data.max()))
        except StandardError:
            log.error("Unexpected error while rescaling data", exc_info=1)
            return
    else:
        # TODO: Do this better/prettier
        # Fill should still be 0 here
        log.debug("Running DNB rescaling from 0-1 to 0-255")
        rescaled_data = numpy.multiply(data, 255.0, out=data)

    # Make NetCDF files
    file_info["nc_file"] = swath_info["start_dt"].strftime(file_info["nc_format"])
    nc_stat = awips_netcdf.fill(file_info["nc_file"], rescaled_data, file_info["nc_template"], swath_info["start_dt"])
    if not nc_stat:
        log.error("Error while creating NC file")
        return

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
    log.debug(repr(TEMPLATES))

    if len(args) == 0 or "help" in args:
        parser.print_help()
        sys.exit(0)
    elif len(args) == 1 and "remove" in args:
        log.debug("Removing previous products")
        remove_products()
        sys.exit(0)

    if len(args) < 2:
        log.error("Wrong number of arguments")
        parser.print_help()

    stat = run_viirs2awips(int(args[0]), args[1:], fornav_D=int(options.fornav_D), fornav_d=int(options.fornav_d), forced_gpd=options.forced_gpd, forced_nc=options.forced_nc)
    sys.exit(stat)

if __name__ == "__main__":
    sys.exit(main())

