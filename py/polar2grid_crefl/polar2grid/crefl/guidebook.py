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

from polar2grid.core.constants import SAT_NPP,INST_VIIRS,BKIND_I,BKIND_M
from polar2grid.core.time_utils import UTC
from pyhdf import SD
import numpy

import os
import sys
import re
import glob
import logging
from datetime import datetime

log = logging.getLogger(__name__)

# Instance of the UTC timezone
UTC = UTC()

### CONSTANTS TO BE PUT IN POLAR2GRID.CORE XXX ###
BID_CREFL_02="crefl02"
BID_CREFL_03="crefl03"
BID_CREFL_04="crefl04"
BID_CREFL_05="crefl05"
BID_CREFL_07="crefl07"
BID_CREFL_08="crefl08"
BID_CREFL_10="crefl10"
BID_CREFL_11="crefl11"
BID_CREFL_12="crefl12"

DKIND_CREFL_02="crefl_02"
DKIND_CREFL_03="crefl_03"
DKIND_CREFL_04="crefl_04"
DKIND_CREFL_05="crefl_05"
DKIND_CREFL_07="crefl_07"
DKIND_CREFL_08="crefl_08"
DKIND_CREFL_10="crefl_10"
DKIND_CREFL_11="crefl_11"
DKIND_CREFL_12="crefl_12"
### CONSTANTS TO BE PUT IN POLAR2GRID.CORE XXX ###

# Constants for dataset names in crefl output files
DS_CR_03 = "CorrRefl_03"
DS_CR_04 = "CorrRefl_04"
DS_CR_05 = "CorrRefl_05"
DS_CR_12 = "CorrRefl_12"

# Keys in hdf4 attributes
K_FILL_VALUE   = "FillValueKey"
K_SCALE_FACTOR = "ScaleFactorKey"
K_SCALE_OFFSET = "ScaleOffsetKey"
K_UNITS        = "UnitsKey"
K_DATASETS     = "DatasetsKey"

"""
I1  | CorrRefl_12
I2  | CorrRefl_7
I3  | CorrRefl_10
M2  | CorrRefl_2
M3  | CorrRefl_3
M4  | CorrRefl_4
M5  | CorrRefl_5
M7  | CorrRefl_7
M8  | CorrRefl_8
M10 | CorrRefl_10
M11 | CorrRefl_11
"""

""" Example of SVM file (lower resolution)
[davidh@glados new_crefl]$ hdfdump -h test.hdf 
netcdf test {
dimensions:
    lines_750m = 768 ;
    samples_750m = 3200 ;

variables:
    short CorrRefl_03(lines_750m, samples_750m) ;
        CorrRefl_03:_FillValue = 32767s ;
        CorrRefl_03:scale_factor = 0.0001 ;
        CorrRefl_03:add_offset = 0. ;
        CorrRefl_03:units = "none" ;
    short CorrRefl_04(lines_750m, samples_750m) ;
        CorrRefl_04:_FillValue = 32767s ;
        CorrRefl_04:scale_factor = 0.0001 ;
        CorrRefl_04:add_offset = 0. ;
        CorrRefl_04:units = "none" ;
    short CorrRefl_05(lines_750m, samples_750m) ;
        CorrRefl_05:_FillValue = 32767s ;
        CorrRefl_05:scale_factor = 0.0001 ;
        CorrRefl_05:add_offset = 0. ;
        CorrRefl_05:units = "none" ;
    float Longitude(lines_750m, samples_750m) ;
        Longitude:_FillValue = -999.f ;
        Longitude:scale_factor = 1. ;
        Longitude:add_offset = 0. ;
        Longitude:units = "none" ;
    float Latitude(lines_750m, samples_750m) ;
        Latitude:_FillValue = -999.f ;
        Latitude:scale_factor = 1. ;
        Latitude:add_offset = 0. ;
        Latitude:units = "none" ;

// global attributes:
        :ProcessVersionNumber = "1.7.1" ;
        :MaxSolarZenithAngle = 86.5f ;
        :sealevel = '\0' ;
        :toa = '\0' ;
        :nearest = '\0' ;
}
"""

""" Example of SVI (higher resolution)
[davidh@glados crefl_conus_day]$ hdfdump -h test.hdf 
netcdf test {
dimensions:
    lines_350m = 1536 ;
    samples_350m = 6400 ;
    lines_750m = 768 ;
    samples_750m = 3200 ;

variables:
    short CorrRefl_12(lines_350m, samples_350m) ;
        CorrRefl_12:_FillValue = 32767s ;
        CorrRefl_12:scale_factor = 0.0001 ;
        CorrRefl_12:add_offset = 0. ;
        CorrRefl_12:units = "none" ;
    short CorrRefl_03(lines_750m, samples_750m) ;
        CorrRefl_03:_FillValue = 32767s ;
        CorrRefl_03:scale_factor = 0.0001 ;
        CorrRefl_03:add_offset = 0. ;
        CorrRefl_03:units = "none" ;
    short CorrRefl_04(lines_750m, samples_750m) ;
        CorrRefl_04:_FillValue = 32767s ;
        CorrRefl_04:scale_factor = 0.0001 ;
        CorrRefl_04:add_offset = 0. ;
        CorrRefl_04:units = "none" ;
    short CorrRefl_05(lines_750m, samples_750m) ;
        CorrRefl_05:_FillValue = 32767s ;
        CorrRefl_05:scale_factor = 0.0001 ;
        CorrRefl_05:add_offset = 0. ;
        CorrRefl_05:units = "none" ;
    float Longitude(lines_350m, samples_350m) ;
        Longitude:_FillValue = -999.f ;
        Longitude:scale_factor = 1. ;
        Longitude:add_offset = 0. ;
        Longitude:units = "none" ;
    float Latitude(lines_350m, samples_350m) ;
        Latitude:_FillValue = -999.f ;
        Latitude:scale_factor = 1. ;
        Latitude:add_offset = 0. ;
        Latitude:units = "none" ;

// global attributes:
        :ProcessVersionNumber = "1.7.1" ;
        :1km_input_file = "../../data/viirs/conus_day/SVI01_npp_d20120225_t1801245_e1802487_b01708_c20120226002130255476_noaa_ops.h5" ;
        :MaxSolarZenithAngle = 86.5f ;
        :sealevel = '\0' ;
        :toa = '\0' ;
        :nearest = '\0' ;
}
"""

# Regular expressions for files we understand and some information that we know based on which one matches
FILE_REGEX = {
        r'crefl.(?P<sat>[A-Za-z0-9]+)_viirs_350_d(?P<date_str>\d+)_t(?P<start_str>\d+)_e(?P<end_str>\d+).hdf' : {
            K_FILL_VALUE   : "_FillValue",
            K_SCALE_FACTOR : "scale_factor",
            K_SCALE_OFFSET : "add_offset",
            K_UNITS        : "units",
            K_DATASETS     : [ DS_CR_12, DS_CR_03, DS_CR_04, DS_CR_05 ],
            "band_kind"    : "svi",
            "instrument"   : "viirs"
            },
        r'crefl.(?P<sat>[A-Za-z0-9]+)_viirs_750_d(?P<date_str>\d+)_t(?P<start_str>\d+)_e(?P<end_str>\d+).hdf' : {
            K_FILL_VALUE   : "_FillValue",
            K_SCALE_FACTOR : "scale_factor",
            K_SCALE_OFFSET : "add_offset",
            K_UNITS        : "units",
            K_DATASETS     : [ DS_CR_03, DS_CR_04, DS_CR_05 ],
            "band_kind"    : "svm",
            "instrument"   : "viirs"
            },
        }

# Satellites that we know how to handle
SATELLITES = {
        "npp"   : SAT_NPP#,
        #"aqua"  : SAT_AQUA,
        #"terra" : SAT_TERRA
        }

INSTRUMENTS = {
        "viirs" : INST_VIIRS#,
        #"modis" : INST_MODIS
        }

FILE_BKIND_CONSTANT = {
        "svi"   : BKIND_I,
        "i"     : BKIND_I,
        "svm"   : BKIND_M,
        "m"     : BKIND_M
        }

DATASET2DKIND = {
        DS_CR_03 : DKIND_CREFL_03,
        DS_CR_04 : DKIND_CREFL_04,
        DS_CR_05 : DKIND_CREFL_05,
        DS_CR_12 : DKIND_CREFL_12
        }

DATASET2BID = {
        DS_CR_03 : BID_CREFL_03,
        DS_CR_04 : BID_CREFL_04,
        DS_CR_05 : BID_CREFL_05,
        DS_CR_12 : BID_CREFL_12
        }

DATASET2RPS = {
        DS_CR_03 : 16,
        DS_CR_04 : 16,
        DS_CR_05 : 16,
        DS_CR_12 : 32
        }

BKIND2NAV = {
        BKIND_I : ("GIMGO", "GITCO"),
        BKIND_M : ("GMODO", "GMTCO")
        }

def _convert_datetimes(date_str, start_str, end_str):
    # the last digit in the 7 digit time is tenths of a second
    # we turn it into microseconds
    start_us = int(start_str[-1]) * 100000
    end_us   = int(  end_str[-1]) * 100000

    # Parse out the datetime, making sure to add the microseconds and set the timezone to UTC
    start_time = datetime.strptime(date_str + "_" + start_str[:-1], "%Y%m%d_%H%M%S").replace(tzinfo=UTC, microsecond=start_us)
    end_time   = datetime.strptime(date_str + "_" +   end_str[:-1], "%Y%m%d_%H%M%S").replace(tzinfo=UTC, microsecond=  end_us)

    return start_time,end_time

def _get_nav_glob(data_dir, sat, inst, band_kind, date_str, start_str, end_str, terrain_corrected=True):
    if sat == SAT_NPP and inst == INST_VIIRS:
        prefix = BKIND2NAV[band_kind][terrain_corrected]
        nav_glob = "%s_npp_d%s_t%s_e%s_*.h5" % (prefix, date_str, start_str, end_str)
        return os.path.join(data_dir, nav_glob)
    else:
        log.error("Not sure how to get the navigation data for %s %s %s" % (sat, inst, band_kind))
        raise ValueError("Not sure how to get the navigation data for %s %s %s" % (sat, inst, band_kind))


def get_file_info(data_filepath, fill_value=-999.0):
    """Return a dictionary of information about the file provided

    """
    file_info = {}
    if not os.path.exists(data_filepath):
        log.error("crefl file '%s' does not exist" % (data_filepath))
        raise ValueError("crefl file '%s' does not exist" % (data_filepath))

    file_info["data_filepath"] = data_filepath
    data_dir,data_filename = os.path.split(data_filepath)
    file_info["data_dir"] = data_dir
    file_info["data_filename"] = data_filename

    # Pull information from the filename
    for pat,nfo in FILE_REGEX.items():
        m = re.match(pat, data_filename)
        if not m:
            continue

        # Get the information from the filename regex
        filename_info = m.groupdict()
        for k,v in filename_info.items():
            # Make everything lower case
            filename_info[k] = filename_info[k].lower()

        file_info.update(filename_info)
        file_info.update(nfo)

        # Convert the satellite name
        if file_info["sat"] not in SATELLITES:
            msg = "Don't know how to process satellite '%s'" % (file_info["sat"],)
            log.error(msg)
            raise ValueError(msg)
        file_info["sat"] = SATELLITES[file_info["sat"]]

        # Convert the instrumen name
        if file_info["instrument"] not in INSTRUMENTS:
            msg = "Don't know how to process instrument '%s'" % (file_info["instrument"],)
            log.error(msg)
            raise ValueError(msg)
        file_info["instrument"] = INSTRUMENTS[file_info["instrument"]]

        # Convert the band kind
        if file_info["band_kind"] not in FILE_BKIND_CONSTANT:
            msg = "Don't know how to process band kind '%s'" % (file_info["band_kind"],)
            log.error(msg)
            raise ValueError(msg)
        file_info["kind"] = FILE_BKIND_CONSTANT[file_info["band_kind"]]
        del file_info["band_kind"] # reduce confusion

        # Convert date, start time, and end time
        start_time,end_time = _convert_datetimes(file_info["date_str"], file_info["start_str"], file_info["end_str"])
        file_info["start_time"] = start_time
        file_info["end_time"] = end_time

        # Open the file to get additional information
        h = SD.SD(file_info["data_filepath"], SD.SDC.READ)

        # Pull band information
        file_info["bands"] = {}
        for ds_name in file_info[K_DATASETS]:
            ds = h.select(ds_name)
            ds_info = ds.attributes()

            # fill value
            data_fill_value = ds_info[file_info[K_FILL_VALUE]]

            # scale factor
            scale_factor = ds_info[file_info[K_SCALE_FACTOR]]

            # scale offset
            scale_offset = ds_info[file_info[K_SCALE_OFFSET]]

            # units (not used)

            # get data
            data = ds.get().astype(numpy.float32)

            # unscale data
            fill_mask = data == data_fill_value
            numpy.multiply(data, scale_factor, out=data)
            numpy.add(data, scale_offset, out=data)
            data[fill_mask] = fill_value

            # write information to the file information
            file_info["bands"][(file_info["kind"],DATASET2BID[ds_name])] = {
                    "data"          : data,
                    "data_kind"     : DATASET2DKIND[ds_name],
                    "remap_data_as" : DATASET2DKIND[ds_name],
                    "kind"          : file_info["kind"],
                    "band"          : DATASET2BID[ds_name],
                    "rows_per_scan" : DATASET2RPS[ds_name]
                    }

        # TODO: Get Navigation data

        return file_info

    # none of the filename patterns matched, we don't know how to handle this file
    log.error("Unrecognized filenaming scheme: '%s'" % data_filename)
    raise ValueError("Unrecognized filenaming scheme: '%s'" % data_filename)

def main():
    from argparse import ArgumentParser
    description = """Simple command line interface to test what information
    the guidebook returns for provided files.
    """
    parser = ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
            help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_argument("data_files", nargs="+",
            help="1 or more crefl product files")
    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, args.verbosity)])

    from pprint import pprint
    for fn in args.data_files:
        print "###              %s                ###" % fn
        pprint(get_file_info(fn))

if __name__ == "__main__":
    sys.exit(main())

