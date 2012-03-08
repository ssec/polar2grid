"""Script for going from VIIRS .h5 files to a AWIPS compatible
NetCDF file.

Author: David Hoese,davidh,SSEC
"""
import os
import sys
import logging
from glob import glob
from netCDF4 import Dataset

from viirs_imager_to_swath import _test_fbf
from rescale import rescale
from keoni.fbf import Workspace
import ms2gt
import awips_netcdf

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

    for f in glob("awips.nc"):
        _safe_remove(f)

def run_viirs2awips(gpd_file, nc_template, filepaths, fornav_D=None):
    """Go through the motions of converting
    a VIIRS h5 file into a AWIPS NetCDF file.

    1. viirs_imager_to_swath.py
    2. ll2cr
    3. fornav
    4. rescale.py
    5. awips_netcdf.py
    """
    log.debug("Removing any previous files")
    remove_products()

    file_info = {}
    # FIXME: These files will come from guidebook in the future
    file_info["grid_gpd"] = gpd_file
    file_info["nc_template"] = nc_template
    # Create latitude.real4.*
    # Create longitude.real4.*
    # Create image.real4.*
    swath_info = _test_fbf(*filepaths)

    file_info["fbf_lat"] = _glob_file("latitude.real4.*")
    file_info["fbf_lon"] = _glob_file("longitude.real4.*")
    file_info["fbf_img"] = _glob_file("image.real4.*")

    # Move and/or link recently created files
    _force_symlink(file_info["fbf_lat"], "lat.img")
    file_info["img_lat"] = "lat.img"
    _force_symlink(file_info["fbf_lon"], "lon.img")
    file_info["img_lon"] = "lon.img"
    _force_symlink(file_info["fbf_img"], "swath.img")
    file_info["img_swath"] = "swath.img"

    # Get number of rows and columns for the output grid
    nc = Dataset(file_info["nc_template"], "r")
    (out_cols,out_rows) = nc.variables["image"].shape
    log.debug("Number of output columns calculated from NC template %d" % out_cols)
    log.debug("Number of output rows calculated from NC template %d" % out_rows)

    # Run ll2cr
    # TODO: Do I need to calculate 3200 and 48 from the input data?
    cr_dict = ms2gt.ll2cr(
            3200,
            48,
            len(filepaths) * 16,
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
    # TODO: Get 5120,5120 from the template file
    file_info["img_output"] = "output.img"
    fornav_dict = ms2gt.fornav(
            1,
            3200,
            cr_dict["scans_out"],
            len(filepaths) * 16,
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
            weight_delta_max=fornav_D
            )
    if fornav_dict is None:
        log.error("fornav didn't return any information")
        return

    # Move and/or link recently created files
    _force_symlink(file_info["img_output"], "result.real4.5120.5120")
    file_info["fbf_output"] = "result.real4.5120.5120"

    # Rescale the image
    try:
        W = Workspace('.')
        img = getattr(W, "result")[0]
        data = img.copy()
    except StandardError:
        log.error("Could not open img file %s" % file_info["fbf_output"])
        log.debug("Files matching %r" % glob("result.*"))
        return

    try:
        rescaled_data = rescale(data, kind=swath_info["kind"], band=swath_info["band"], data_kind=swath_info["data_kind"])
    except StandardError:
        log.error("Unexpected error while rescaling data", exc_info=1)
        return

    # Make NetCDF files
    file_info["nc_file"] = "awips.nc"
    nc_stat = awips_netcdf.fill(file_info["nc_file"], rescaled_data, file_info["nc_template"], swath_info["start_dt"])
    if not nc_stat:
        log.error("Error while creating NC file")
        return

def main():
    import optparse
    usage = """%prog gpd_file nc_template file1.h5 file2.h5 ..."""
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_option('-D', dest='fornav_D', default=40,
            help="Specify the -D option for fornav")
    options,args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])

    if len(args) == 0 or "help" in args:
        parser.print_help()
        sys.exit(0)
    elif len(args) == 1 and "remove" in args:
        log.debug("Removing previous products")
        remove_products()
        sys.exit(0)

    if len(args) < 3:
        log.error("Wrong number of arguments")
        parser.print_help()

    stat = run_viirs2awips(args[0], args[1], args[2:], fornav_D=int(options.fornav_D))
    sys.exit(stat)

if __name__ == "__main__":
    sys.exit(main())

