#!/usr/bin/env python
# encoding: utf-8
"""
Read one or more contiguous in-order HDF4 VIIRS or MODIS corrected reflectance product
granules and aggregate them into one swath per band.  Return a dictionary of meta data.
Write out Swath binary files used by other polar2grid components.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from polar2grid.core import roles
from polar2grid.core.constants import *
from polar2grid.core.fbf import file_appender,check_stem
from polar2grid.viirs import viirs_guidebook
from polar2grid.modis.modis_geo_interp_250 import interpolate_geolocation
from pyhdf import SD
import h5py
from . import guidebook
import numpy

import os
import sys
import logging
from pprint import pprint

log = logging.getLogger(__name__)

# XXX: Temporary - should be replaced with call to VIIRS Frontend when possible
def load_geo_data(nav_set_uid, geo_filepath, fill_value=DEFAULT_FILL_VALUE, dtype=numpy.float32):
    """Place holder for when VIIRS frontend can be rewritten to support
    third-party users.
    """
    if nav_set_uid == IBAND_NAV_UID or nav_set_uid == MBAND_NAV_UID:
        file_info = viirs_guidebook.geo_info(geo_filepath)
        h = h5py.File(file_info["geo_path"], mode='r')
        lon_array = viirs_guidebook.load_geo_variable(h, file_info, viirs_guidebook.K_LONGITUDE, dtype=dtype, required=True)
        lon_array[ viirs_guidebook.get_geo_variable_fill_mask(lon_array, viirs_guidebook.K_LONGITUDE) ] = fill_value
        lat_array = viirs_guidebook.load_geo_variable(h, file_info, viirs_guidebook.K_LATITUDE, dtype=dtype, required=True)
        lat_array[ viirs_guidebook.get_geo_variable_fill_mask(lat_array, viirs_guidebook.K_LATITUDE) ] = fill_value
        west_bound,east_bound,north_bound,south_bound = viirs_guidebook.read_geo_bbox_coordinates(h, file_info, fill_value=fill_value)
    elif nav_set_uid == GEO_NAV_UID or nav_set_uid == GEO_250M_NAV_UID:
        # XXX: Interpolation does not handle 500M navigation yet
        h = SD.SD(geo_filepath, SD.SDC.READ)
        lon_ds = h.select("Longitude")
        lon_array = lon_ds[:].astype(dtype)
        lon_fill_value = lon_ds.attributes()["_FillValue"]
        lon_mask = lon_array == lon_fill_value

        lat_ds = h.select("Latitude")
        lat_array = lat_ds[:].astype(dtype)
        lat_fill_value = lat_ds.attributes()["_FillValue"]
        lat_mask = lat_array == lat_fill_value

        # Interpolate to the proper resolution
        if nav_set_uid == GEO_250M_NAV_UID:
            log.info("Interpolating 250m navigation from 1km")
            lon_array = interpolate_geolocation(lon_array)
            lat_array = interpolate_geolocation(lat_array)

        lon_array[ lon_mask ] = fill_value
        lat_array[ lat_mask ] = fill_value
        west_bound = 0
        east_bound = 0
        north_bound = 0
        south_bound = 0
    else:
        log.error("Don't know how to get navigation data for nav set: %s" % nav_set_uid)
        raise ValueError("Don't know how to get navigation data for nav set: %s" % nav_set_uid)

    return lon_array,lat_array,west_bound,east_bound,north_bound,south_bound

class Frontend(roles.FrontendRole):
    removable_file_patterns = [
            ".latitude_*_",
            ".longitude_*_*",
            ".image_*_*_*_*",
            "image_*_*.real4.*.*",
            "latitude_*.real4.*.*",
            "longitude_*.real4.*.*"
            ]

    def __init__(self):
        pass

    @classmethod
    def parse_datetimes_from_filepaths(cls, filepaths):
        return guidebook.parse_datetimes_from_filepaths(filepaths)

    @classmethod
    def sort_files_by_nav_uid(cls, filepaths):
        return guidebook.sort_files_by_nav_uid(filepaths)

    def load_band_data(self, meta_data, data_filepath, nav_set_uid, band_kind, band_id, fill_value=DEFAULT_FILL_VALUE):
        """Read the specified band from the file in the meta data dictionary
        provided and return a numpy array of the scaled and properly filled data.

        Only operates on one band.
        """
        band_info = meta_data["bands"][(band_kind, band_id)]

        # Get a file object for the file containing this band's information
        h = SD.SD(data_filepath, mode=SD.SDC.READ)

        # Get the name of the attributes and variables in the file
        dataset_name = band_info[guidebook.K_DATASET]
        fill_attr_name = band_info.get(guidebook.K_FILL_VALUE, None)
        scale_factor_attr_name = band_info.get(guidebook.K_SCALE_FACTOR, None)
        scale_offset_attr_name = band_info.get(guidebook.K_SCALE_OFFSET, None)
        units_attr_name = band_info.get(guidebook.K_UNITS, None) # Unused

        # Get the band data from the file
        ds_object = h.select(dataset_name)
        band_data = ds_object.get().astype(numpy.float32)

        attrs = ds_object.attributes()
        if fill_attr_name:
            input_fill_value = attrs[fill_attr_name]
            log.debug("Using fill value attribute '%s' (%s) to filter bad data", fill_attr_name, str(input_fill_value))
            input_fill_value = 16000
            log.debug("Ignoring fill value and using '%s' instead", str(input_fill_value))
            fill_mask = band_data > input_fill_value
        else:
            fill_mask = numpy.zeros_like(band_data).astype(numpy.bool)

        if isinstance(scale_factor_attr_name, float):
            scale_factor = scale_factor_attr_name
        elif scale_factor_attr_name is not None:
            scale_factor = attrs[scale_factor_attr_name]

        if isinstance(scale_offset_attr_name, float):
            scale_offset = scale_offset_attr_name
        elif scale_offset_attr_name is not None:
            scale_offset = attrs[scale_offset_attr_name]

        # Scale the data
        if scale_factor_attr_name is not None and scale_offset_attr_name is not None:
            band_data = band_data * scale_factor + scale_offset
        band_data[fill_mask] = fill_value

        return band_data

    def write_band_fbf(self, meta_data, nav_set_uid, band_kind, band_id, fill_value=DEFAULT_FILL_VALUE):
        """Writes a flat binary file for an entire swath of data.
        """
        # Create a temporary flat binary file (will be renamed later)
        spid = "%d" % os.getpid()
        stem = "image_%s_%s_%s" % (nav_set_uid, band_kind, band_id)
        check_stem(stem)
        fbf_tmp_filename = "." + stem + "_" + spid
        image_fbf_file = file(fbf_tmp_filename, 'wb')
        image_fbf_appender = file_appender(image_fbf_file, dtype=numpy.float32)

        # Iterate over each file that contains data that makes up this band
        for data_filepath in meta_data["bands"][(band_kind,band_id)]["data_filepaths"]:
            # Load the individual array for this band
            band_array = self.load_band_data(meta_data, data_filepath, nav_set_uid, band_kind, band_id, fill_value=fill_value)
            # Add the data to the FBF
            image_fbf_appender.append(band_array)

        # Rename flat binary files to proper fbf names
        suffix = '.real4.' + '.'.join(str(x) for x in reversed(image_fbf_appender.shape))
        fbf_image_filename = stem + suffix
        os.rename(fbf_tmp_filename, fbf_image_filename)

        # Add this new information to the band information
        band_info = meta_data["bands"][(band_kind,band_id)]
        band_info["fbf_img"] = fbf_image_filename
        band_info["fill_value"] = fill_value
        band_info["swath_rows"] = image_fbf_appender.shape[0]
        band_info["swath_cols"] = image_fbf_appender.shape[1]
        band_info["swath_scans"] = band_info["swath_cols"] / band_info["rows_per_scan"]

        # Add info to the main meta data dictionary if its not there already
        if "swath_rows" not in meta_data: meta_data["swath_rows"] = band_info["swath_rows"]
        if "swath_cols" not in meta_data: meta_data["swath_cols"] = band_info["swath_cols"]
        if "swath_scans" not in meta_data: meta_data["swath_scans"] = band_info["swath_scans"]

    def write_geo_fbf(self, meta_data, nav_set_uid, all_geo_filepaths, fill_value=DEFAULT_FILL_VALUE):
        # Create a temporary flat binary file( will be renamed later)
        spid = "%d" % os.getpid()
        lat_stem = "latitude_%s" % (nav_set_uid)
        lon_stem = "longitude_%s" % (nav_set_uid)
        check_stem(lat_stem)
        check_stem(lon_stem)
        fbf_lat_tmp_fn = "." + lat_stem + "_" + spid
        fbf_lon_tmp_fn = "." + lon_stem + "_" + spid
        lat_fbf_file = file(fbf_lat_tmp_fn, 'wb')
        lon_fbf_file = file(fbf_lon_tmp_fn, 'wb')
        lat_fbf_appender = file_appender(lat_fbf_file, dtype=numpy.float32)
        lon_fbf_appender = file_appender(lon_fbf_file, dtype=numpy.float32)

        # Iterate over each navigation file that makes up the swath
        wests,easts,norths,souths = [],[],[],[]
        for geo_filepath in all_geo_filepaths:
            # Get longitude,latitude arrays from navigation files
            # Get the bounding coordinates
            lon_array,lat_array,wbound,ebound,nbound,sbound = load_geo_data(nav_set_uid, geo_filepath, fill_value=fill_value)
            # Add the data to the FBFs
            lon_fbf_appender.append(lon_array)
            lat_fbf_appender.append(lat_array)
            # Add it to a list of all of the bounds for every file
            wests.append(wbound)
            easts.append(ebound)
            norths.append(nbound)
            souths.append(sbound)

        # Find the overall bounding box from the individual bounding box for each file
        if nav_set_uid == IBAND_NAV_UID or nav_set_uid == MBAND_NAV_UID:
            overall_wbound,overall_ebound,overall_nbound,overall_sbound = viirs_guidebook.calculate_bbox_bounds(wests, easts, norths, souths)
            meta_data["lon_west"] = overall_wbound
            meta_data["lon_east"] = overall_ebound
            meta_data["lat_north"] = overall_nbound
            meta_data["lat_south"] = overall_sbound

        # Rename flat binary files to proper fbf names
        suffix = '.real4.' + '.'.join(str(x) for x in reversed(lat_fbf_appender.shape))
        fbf_lat_fn = lat_stem + suffix
        fbf_lon_fn = lon_stem + suffix
        os.rename(fbf_lat_tmp_fn, fbf_lat_fn)
        os.rename(fbf_lon_tmp_fn, fbf_lon_fn)

        # Add this new information to the meta data dictionary
        meta_data["lat_fill_value"] = fill_value
        meta_data["lon_fill_value"] = fill_value
        meta_data["fbf_lat"] = fbf_lat_fn
        meta_data["fbf_lon"] = fbf_lon_fn

        # Check to make sure navigation is the same size as the other data
        if lat_fbf_appender.shape != lon_fbf_appender.shape or \
                lat_fbf_appender.shape != (meta_data["swath_rows"],meta_data["swath_cols"]):
            log.error("Navigation data was not the same size as the band data")
            raise ValueError("Navigation data was not the same size as the band data")

    def extract_band_info(self, meta_data, file_info, nav_set_uid, band_id):
        """Update the meta_data dictionary to include relevant information
        about the band tied to the band_id provided.
        """
        band_kind = file_info["kind"]
        if (band_kind, band_id) not in meta_data["bands"]:
            meta_data["bands"][(band_kind, band_id)] = band_info = {}
        else:
            band_info = meta_data["bands"][(band_kind, band_id)]

        # Fill in global information required by the frontend interface
        if "sat" not in meta_data: meta_data["sat"] = file_info["sat"]
        if "instrument" not in meta_data: meta_data["instrument"] = file_info["instrument"]
        if "start_time" not in meta_data or file_info["start_time"] < meta_data["start_time"]:
                meta_data["start_time"] = file_info["start_time"]

        # Fill in information required by the frontend interface
        band_info["kind"] = band_kind
        band_info["band_id"] = band_id
        band_info["data_kind"] = file_info["data_kind"]
        band_info["remap_data_as"] = file_info["data_kind"]
        band_info["rows_per_scan"] = file_info["rows_per_scan"]
        meta_data["rows_per_scan"] = band_info["rows_per_scan"]

        # Fill in information required to load the data later in the frontend
        if "data_filepaths" not in band_info:
            band_info["data_filepaths"] = [ file_info["data_filepath"] ]
        else:
            band_info["data_filepaths"].append(file_info["data_filepath"])

        band_info[guidebook.K_DATASET]      = file_info[guidebook.K_DATASETS][file_info["bands"].index(band_id)]
        band_info[guidebook.K_FILL_VALUE]   = file_info.get(guidebook.K_FILL_VALUE, None)
        band_info[guidebook.K_SCALE_FACTOR] = file_info.get(guidebook.K_SCALE_FACTOR, None)
        band_info[guidebook.K_SCALE_OFFSET] = file_info.get(guidebook.K_SCALE_OFFSET, None)
        band_info[guidebook.K_UNITS]        = file_info.get(guidebook.K_UNITS, None)

    def make_swaths(self, nav_set_uid, filepaths_dict, cut_bad=False, fill_value=DEFAULT_FILL_VALUE,
            bands_desired=[ BID_08, BID_01, BID_04, BID_03 ]
            ):
        """Create binary swath files and return a python dictionary
        of meta data.
        """
        # Store the information for each file that we look at 
        all_nav_filepaths = set()
        meta_data = {
                "nav_set_uid" : nav_set_uid,
                "bands" : {},
                }

        # Get meta data for all data files
        for file_pattern,filepath_list in filepaths_dict.items():
            # Sort the file list alphabetically (in place)
            filepath_list.sort()

            for filepath in filepath_list:
                log.info("Loading meta data from %s" % filepath)
                # Get meta data for this filepath
                file_info = guidebook.get_file_meta(nav_set_uid, file_pattern, filepath)
                # Store the navigation information for later
                all_nav_filepaths.add(file_info["geo_filepath"])

                # Extract each band that is in this file
                # Data is currently organized in a "per-file" structure, this
                # makes it a "per-band" structure
                for band_id in file_info["bands"]:
                    # Does the user want this band?
                    if band_id in bands_desired:
                        self.extract_band_info(meta_data, file_info, nav_set_uid, band_id)

        # Sort the navigation file list
        all_nav_filepaths = sorted(all_nav_filepaths)

        # Create image data flat binary files
        for band_kind,band_id in meta_data["bands"].keys():
            log.info("Writing swath binary files for band kind %s band %s" % (band_kind,band_id))
            self.write_band_fbf(meta_data, nav_set_uid, band_kind, band_id, fill_value=fill_value)

        log.info("Writing navigation binary files for nav. set %s" % nav_set_uid)
        # Create navigation flat binary files
        self.write_geo_fbf(meta_data, nav_set_uid, all_nav_filepaths, fill_value=fill_value)

        return meta_data

def main():
    from argparse import ArgumentParser
    from polar2grid.core.script_utils import remove_file_patterns
    import json
    description = """Run crefl frontend on files provided, writing JSON-ified
    meta data dictionary to stdout.
    """
    parser = ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
            help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument('-R', dest='remove_prev', default=False, action='store_true',
            help="Delete any files that may conflict with future processing. Processing is not done with this flag.")
    parser.add_argument('crefl_files', nargs="*",
            help="crefl output files for one contiguous swath/pass")

    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(3, args.verbosity)])

    if not args.remove_prev and not args.crefl_files:
        log.error("You must either specify '-R' to remove conflicting files or provide files to process")
        return -1

    if args.remove_prev:
        log.info("Removing any possible conflicting files")
        remove_file_patterns(
                Frontend.removable_file_patterns
                )
        return 0

    nav_set_dict = Frontend.sort_files_by_nav_uid(args.crefl_files)
    for nav_set_uid,filepaths_dict in nav_set_dict.items():
        frontend = Frontend()
        meta_data = frontend.make_swaths(nav_set_uid, filepaths_dict)
        pprint(meta_data)
        #print json.dumps(meta_data)

if __name__ == "__main__":
    sys.exit(main())

