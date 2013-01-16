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
from .guidebook import get_file_info,read_data_file
import numpy

import os
import sys
import logging

log = logging.getLogger(__name__)

class Frontend(roles.FrontendRole):
    removable_file_patterns = [
            ".lat*",
            ".lon*",
            ".image_*_*_*.bin",
            "image_*_*.real4.*.*",
            "latitude_*.real4.*.*",
            "longitude_*.real4.*.*"
            ]

    def __init__(self):
        pass

    def create_binary_files(self, filepaths, fill_value=DEFAULT_FILL_VALUE):
        meta_data = {
                "bands" : {}
                }

        # Create unique temporary filenames
        spid       = "%d" % os.getpid()
        latname    = '.lat' + spid
        lonname    = '.lon' + spid
        data_names = {}

        lafo       = file(latname, 'wb')
        lofo       = file(lonname, 'wb')
        lafa       = file_appender(lafo, dtype=numpy.float32)
        lofa       = file_appender(lofo, dtype=numpy.float32)

        # Read information from the files and create FBFs
        for fp in filepaths:
            # Get info 
            file_info = get_file_info(fp)
            read_data_file(file_info, fill_value=fill_value)

            # TODO: Interpolate navigation data

            # Add navigation data to the binary files
            lafa.append( file_info["latitude"]  )
            lofa.append( file_info["longitude"] )

            # Remove the lat/lon arrays, they're not needed anymore
            # Frees memory
            del file_info["latitude"]
            del file_info["longitude"]

            # Operate on each band
            for (band_kind,band_id),band_dict in file_info["bands"].items():
                # XXX: Might have to keep count of resolution types to decide
                # on which navigation set this is

                # Check if we already started the FBF
                data_name = ".image_%s_%s_%s.bin" % (band_kind,band_id,spid)
                if data_name not in data_names:
                    data_fo = file(data_name, 'wb')
                    data_names[data_name] = (data_fo, file_appender(data_fo, dtype=numpy.float32))

                # Add the data to the FBF
                data_names[data_name][1].append(band_dict["data"])

                # Remove the data array, it's not needed anymore, frees memory
                del band_dict["data"]

                # Copy information from the file info to the meta data dictionary
                # Start time can't change, so use the previous value if it exists
                start_time = meta_data.get("start_time", file_info["start_time"])
                meta_data.update(file_info)
                meta_data["bands"][(band_kind,band_id)] = band_dict.copy()
                meta_data["bands"][(band_kind,band_id)]["tmp_data_name"] = data_name
                # restore previous start_time
                meta_data["start_time"] = start_time

        # Remove any unneeded data from the meta data dictionary
        # None

        # Move the temporary FBFs to more permanent names
        meta_data["nav_set_uid"] = "ns" + str(meta_data["pixel_size"])
        suffix   = '.real4.' + '.'.join(str(x) for x in reversed(lafa.shape))
        lat_stem = "latitude_%s"  % meta_data["nav_set_uid"]
        lon_stem = "longitude_%s" % meta_data["nav_set_uid"]
        check_stem(lat_stem)
        check_stem(lon_stem)

        fbf_lat = lat_stem + suffix
        fbf_lon = lon_stem + suffix
        os.rename(latname, fbf_lat)
        os.rename(lonname, fbf_lon)
        meta_data["fbf_lat"] = fbf_lat
        meta_data["fbf_lon"] = fbf_lon

        for (band_kind,band_id),band_dict in meta_data["bands"].items():
            data_stem = "image_%s_%s" % (band_kind,band_id)
            check_stem(data_stem)

            fbf_img = data_stem + suffix
            os.rename(band_dict["tmp_data_name"], fbf_img)
            meta_data["bands"][(band_kind,band_id)]["fbf_img"] = fbf_img
            del band_dict["tmp_data_name"]

        swath_rows,swath_cols = lafa.shape
        meta_data["swath_cols"] = swath_cols
        meta_data["swath_rows"] = swath_rows
        # TODO
        #log.debug("Data West Lon: %f, North Lat: %f, East Lon: %f, South Lat: %f" % (lon_west,lat_north,lon_east,lat_south))
        #meta_data["lat_south"] = lat_south
        #meta_data["lat_north"] = lat_north
        #meta_data["lon_west"] = lon_west
        #meta_data["lon_east"] = lon_east
        meta_data["lon_fill_value"] = fill_value
        meta_data["lat_fill_value"] = fill_value
        return meta_data

    def make_swaths(self, filepaths, cut_bad=False):
        """Create binary swath files and return a python dictionary
        of meta data.
        """
        meta_data = self.create_binary_files(filepaths)

        return meta_data

def main():
    from argparse import ArgumentParser
    from polar2grid.core.glue_utils import remove_file_patterns
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

    frontend = Frontend()
    meta_data = frontend.make_swaths(args.crefl_files)

    from pprint import pprint
    pprint(meta_data)
    #print json.dumps(meta_data)

if __name__ == "__main__":
    sys.exit(main())

