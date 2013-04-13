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

from polar2grid.core.constants import *
from polar2grid.core.time_utils import UTC
from pyhdf import SD,error as hdf_error
import numpy

import os
import sys
import re
import logging
from datetime import datetime
from glob import glob

log = logging.getLogger(__name__)

# Instance of the UTC timezone
UTC = UTC()

# Dimension constants
DIMNAME_LINES_750   = "lines_750m"
DIMNAME_SAMPLES_750 = "samples_750m"
DIMNAME_LINES_350   = "lines_350"
DIMNAME_SAMPLES_350 = "samples_350"
DIM_LINES_750   = 768
DIM_SAMPLES_750 = 3200
DIM_LINES_350   = 1536
DIM_SAMPLES_350 = 6400

# Pixel size constants to determine how to interpolate later
PIXEL_SIZE_750  = 750
PIXEL_SIZE_350  = 350

# Constants for dataset names in crefl output files
DS_CR_01 = "CorrRefl_01"
DS_CR_02 = "CorrRefl_02"
DS_CR_03 = "CorrRefl_03"
DS_CR_04 = "CorrRefl_04"
DS_CR_05 = "CorrRefl_05"
DS_CR_06 = "CorrRefl_06"
DS_CR_07 = "CorrRefl_07"
DS_CR_08 = "CorrRefl_08"
DS_CR_09 = "CorrRefl_09"
DS_CR_10 = "CorrRefl_10"

# Constants for navigation dataset names in crefl output files
DS_LONGITUDE = "Longitude"
DS_LATITUDE  = "Latitude"

# Keys in hdf4 attributes
K_FILL_VALUE   = "FillValueKey"
K_SCALE_FACTOR = "ScaleFactorKey"
K_SCALE_OFFSET = "ScaleOffsetKey"
K_UNITS        = "UnitsKey"
K_DATASETS     = "DatasetsKey"
K_DATASET      = "DatasetKey"
K_LONGITUDE    = "LongitudeKey"
K_LATITUDE     = "LatitudeKey"
K_COLUMNS_750  = "Columns750Key"
K_COLUMNS_350  = "Columns350Key"
K_ROWS_750     = "Rows750Key"
K_ROWS_350     = "Rows350Key"
K_GEO_PATTERN  = "GeoGlobPatternKey"


"""
CorrRefl_01 | M5 Corrected reflectances
CorrRefl_02 | M7 Corrected reflectances
CorrRefl_03 | M3 Corrected reflectances
CorrRefl_04 | M4 Corrected reflectances
CorrRefl_05 | M8 Corrected reflectances
CorrRefl_06 | M10 Corrected reflectances
CorrRefl_07 | M11 Corrected reflectances
CorrRefl_08 | I1 Corrected reflectances
CorrRefl_09 | I2 Corrected reflectances
CorrRefl_10 | I3 Corrected reflectances
"""

def _convert_npp_datetimes(date_str, start_str):
    # the last digit in the 7 digit time is tenths of a second
    # we turn it into microseconds
    start_us = int(start_str[-1]) * 100000

    # Parse out the datetime, making sure to add the microseconds and set the timezone to UTC
    start_time = datetime.strptime(date_str + "_" + start_str[:-1], "%Y%m%d_%H%M%S").replace(tzinfo=UTC, microsecond=start_us)

    return start_time

def _convert_modis_datetimes(date_str, start_str):
    return datetime.strptime(date_str + "_" + start_str, "%y%j_%H%M")

# Regular expression file patterns used later
IBAND_REGEX = r'CREFLI_(?P<sat>[A-Za-z0-9]+)_d(?P<date_str>\d+)_t(?P<start_str>\d+)_e(?P<end_str>\d+).hdf'
MBAND_REGEX = r'CREFLM_(?P<sat>[A-Za-z0-9]+)_d(?P<date_str>\d+)_t(?P<start_str>\d+)_e(?P<end_str>\d+).hdf'
MODIS_1000M_REGEX = r'(?P<sat>[at])1.(?P<date_str>\d+).(?P<start_str>\d+).crefl.1000m.hdf'
MODIS_500M_REGEX = r'(?P<sat>[at])1.(?P<date_str>\d+).(?P<start_str>\d+).crefl.500m.hdf'
MODIS_250M_REGEX = r'(?P<sat>[at])1.(?P<date_str>\d+).(?P<start_str>\d+).crefl.250m.hdf'

NAV_SET_USES = {
        IBAND_NAV_UID : [ IBAND_REGEX ],
        MBAND_NAV_UID : [ MBAND_REGEX ],
        GEO_NAV_UID   : [ MODIS_1000M_REGEX ],
        GEO_500M_NAV_UID   : [ MODIS_500M_REGEX ],
        GEO_250M_NAV_UID   : [ MODIS_250M_REGEX ],
        }

# Regular expressions for files we understand and some information that we know based on which one matches
FILE_REGEX = {
        IBAND_REGEX : {
            K_FILL_VALUE   : "_FillValue",
            K_SCALE_FACTOR : "scale_factor",
            K_SCALE_OFFSET : "add_offset",
            K_UNITS        : "units",
            K_DATASETS     : [ DS_CR_08, DS_CR_09, DS_CR_10 ],
            K_GEO_PATTERN  : "GITCO_%(sat)s_d%(date_str)s_t%(start_str)s_e%(end_str)s_b*_c*_*.h5",
            "resolution"   : 500,
            "instrument"   : INST_VIIRS,
            "rows_per_scan" : 32,
            "date_convert_func" : _convert_npp_datetimes,
            },
        MBAND_REGEX : {
            K_FILL_VALUE   : "_FillValue",
            K_SCALE_FACTOR : "scale_factor",
            K_SCALE_OFFSET : "add_offset",
            K_UNITS        : "units",
            K_DATASETS     : [ DS_CR_01, DS_CR_02, DS_CR_03, DS_CR_04, DS_CR_05, DS_CR_06, DS_CR_07 ],
            K_GEO_PATTERN  : "GMTCO_%(sat)s_d%(date_str)s_t%(start_str)s_e%(end_str)s_b*_c*_*.h5",
            "resolution"   : 1000,
            "instrument"   : INST_VIIRS,
            "rows_per_scan" : 16,
            "date_convert_func" : _convert_npp_datetimes,
            },
        MODIS_1000M_REGEX : {
            K_FILL_VALUE   : "_FillValue",
            K_SCALE_FACTOR : 0.0001, # Floats are interpreted as constant scaling factors
            K_SCALE_OFFSET : 0.0,
            K_UNITS        : None,
            K_DATASETS     : [ DS_CR_01, DS_CR_02, DS_CR_03, DS_CR_04, DS_CR_05, DS_CR_06, DS_CR_07 ],
            K_GEO_PATTERN  : "%(sat)s1.%(date_str)s.%(start_str)s.geo.hdf",
            "resolution"   : 1000,
            "instrument"   : INST_MODIS,
            "rows_per_scan" : 10,
            "date_convert_func" : _convert_modis_datetimes,
            },
        MODIS_500M_REGEX : {
            K_FILL_VALUE   : "_FillValue",
            K_SCALE_FACTOR : 0.0001,
            K_SCALE_OFFSET : 0.0,
            K_UNITS        : None,
            K_DATASETS     : [ DS_CR_01, DS_CR_02, DS_CR_03, DS_CR_04, DS_CR_05, DS_CR_06, DS_CR_07 ],
            K_GEO_PATTERN  : "%(sat)s1.%(date_str)s.%(start_str)s.geo.hdf",
            "resolution"   : 500,
            "instrument"   : INST_MODIS,
            "rows_per_scan" : 20,
            "date_convert_func" : _convert_modis_datetimes,
            },
        MODIS_250M_REGEX : {
            K_FILL_VALUE   : "_FillValue",
            K_SCALE_FACTOR : 0.0001,
            K_SCALE_OFFSET : 0.0,
            K_UNITS        : None,
            K_DATASETS     : [ DS_CR_01, DS_CR_02, DS_CR_03, DS_CR_04, DS_CR_05, DS_CR_06, DS_CR_07 ],
            K_GEO_PATTERN  : "%(sat)s1.%(date_str)s.%(start_str)s.geo.hdf",
            "resolution"   : 250,
            "instrument"   : INST_MODIS,
            "rows_per_scan" : 40,
            "date_convert_func" : _convert_modis_datetimes,
            },
        }

# Satellites that we know how to handle
# XXX: JPSS satellites will need to be added to this
SATELLITES = {
        "npp"   : SAT_NPP,
        "a"     : SAT_AQUA,
        "t"     : SAT_TERRA,
        }

DATASET2BID = {
        DS_CR_01 : BID_01,
        DS_CR_02 : BID_02,
        DS_CR_03 : BID_03,
        DS_CR_04 : BID_04,
        DS_CR_05 : BID_05,
        DS_CR_06 : BID_06,
        DS_CR_07 : BID_07,
        DS_CR_08 : BID_08,
        DS_CR_09 : BID_09,
        DS_CR_10 : BID_10,
        }

def _safe_glob(pat, num_allowed=1):
    glob_results = glob(pat)
    if len(glob_results) < num_allowed:
        log.error("Could not find enough files matching file pattern: '%s'" % (pat,))
        raise ValueError("Could not find enough files matching file pattern: '%s'" % (pat,))
    if len(glob_results) > num_allowed:
        log.error("Too many files found matching file pattern: '%s'" % (pat,))
        raise ValueError("Too many files found matching file pattern: '%s'" % (pat,))

    if num_allowed == 1: return glob_results[0]
    return glob_results

def parse_datetimes_from_filepaths(filepaths):
    """Provide a list of datetime objects for each understood file provided.

    >>> assert( not parse_datetimes_from_filepaths([]) )
    >>> assert( not parse_datetimes_from_filepaths([ "fake1.txt", "fake2.txt" ]) )
    >>> dts = parse_datetimes_from_filepaths([
    ...     "CREFLI_npp_d20130311_t1916582_e1918223.hdf",
    ...     "CREFLI_npp_d20130311_t1918236_e1919477.hdf",
    ...     "CREFLI_npp_d20130311_t1919490_e1921131.hdf",
    ...     "CREFLI_npp_d20130311_t1921144_e1922385.hdf",
    ...     "CREFLI_npp_d20130311_t1922398_e1924039.hdf",
    ...     "CREFLI_npp_d20130311_t1924052_e1925294.hdf",
    ...     "CREFLI_npp_d20130311_t1925306_e1926548.hdf",
    ...     "CREFLI_npp_d20130311_t1926560_e1928202.hdf",
    ...     "CREFLI_npp_d20130311_t1928214_e1929456.hdf",
    ...     "fake3.txt",
    ...     "CREFLM_npp_d20130311_t1916582_e1918223.hdf",
    ...     "CREFLM_npp_d20130311_t1918236_e1919477.hdf",
    ...     "CREFLM_npp_d20130311_t1919490_e1921131.hdf",
    ...     "CREFLM_npp_d20130311_t1921144_e1922385.hdf",
    ...     "CREFLM_npp_d20130311_t1922398_e1924039.hdf",
    ...     "CREFLM_npp_d20130311_t1924052_e1925294.hdf",
    ...     "CREFLM_npp_d20130311_t1925306_e1926548.hdf",
    ...     "CREFLM_npp_d20130311_t1926560_e1928202.hdf",
    ...     "CREFLM_npp_d20130311_t1928214_e1929456.hdf"
    ...     ])
    >>> assert( len(dts) == 18 )
    """
    file_dates = []
    for fn in [ os.path.split(fp)[1] for fp in filepaths ]:
        matched_pattern_obj = None
        matched_pattern = None
        for file_pattern in FILE_REGEX:
            matched_pattern_obj = re.match(file_pattern, fn)
            if not matched_pattern_obj:
                continue
            else:
                matched_pattern = file_pattern
                break

        if not matched_pattern_obj:
            # ignore any files we don't understand
            continue

        filename_info = matched_pattern_obj.groupdict()
        file_dates.append(FILE_REGEX[matched_pattern]["date_convert_func"](filename_info["date_str"], filename_info["start_str"]))

    return file_dates

def sort_files_by_nav_uid(filepaths):
    """Sort the provided filepaths into a dictionary structure keyed by
    `nav_set_uid` and file pattern.

    >>> assert( not sort_files_by_nav_uid([]) )
    >>> assert( not sort_files_by_nav_uid([ "fake1.txt", "fake2.txt" ]) )
    >>> filepaths_dict = sort_files_by_nav_uid([
    ...     "CREFLI_npp_d20130311_t1916582_e1918223.hdf",
    ...     "CREFLI_npp_d20130311_t1918236_e1919477.hdf",
    ...     "CREFLI_npp_d20130311_t1919490_e1921131.hdf",
    ...     "CREFLI_npp_d20130311_t1921144_e1922385.hdf",
    ...     "CREFLI_npp_d20130311_t1922398_e1924039.hdf",
    ...     "CREFLI_npp_d20130311_t1924052_e1925294.hdf",
    ...     "CREFLI_npp_d20130311_t1925306_e1926548.hdf",
    ...     "CREFLI_npp_d20130311_t1926560_e1928202.hdf",
    ...     "CREFLI_npp_d20130311_t1928214_e1929456.hdf",
    ...     "fake3.txt",
    ...     "CREFLM_npp_d20130311_t1916582_e1918223.hdf",
    ...     "CREFLM_npp_d20130311_t1918236_e1919477.hdf",
    ...     "CREFLM_npp_d20130311_t1919490_e1921131.hdf",
    ...     "CREFLM_npp_d20130311_t1921144_e1922385.hdf",
    ...     "CREFLM_npp_d20130311_t1922398_e1924039.hdf",
    ...     "CREFLM_npp_d20130311_t1924052_e1925294.hdf",
    ...     "CREFLM_npp_d20130311_t1925306_e1926548.hdf",
    ...     "CREFLM_npp_d20130311_t1926560_e1928202.hdf",
    ...     "CREFLM_npp_d20130311_t1928214_e1929456.hdf"
    ...     ])
    >>> assert( len(filepaths_dict) == 2 )
    >>> assert( len( filepaths_dict[MBAND_NAV_UID][MBAND_REGEX]) == 9 )
    >>> assert( len( filepaths_dict[IBAND_NAV_UID][IBAND_REGEX]) == 9 )
    """
    filepaths_dict = { nav_set : { file_pattern : [] for file_pattern in NAV_SET_USES[nav_set] } for nav_set in NAV_SET_USES }

    for nav_set,file_pattern_dict in filepaths_dict.items():
        for file_pattern,file_pattern_match_list in file_pattern_dict.items():
            for fp in filepaths:
                fn = os.path.split(fp)[1]
                if re.match(file_pattern, fn):
                    file_pattern_match_list.append(fp)

            if not file_pattern_match_list:
                # remove any file patterns that aren't used
                del file_pattern_dict[file_pattern]

        if not file_pattern_dict:
            # remove any empty nav sets
            del filepaths_dict[nav_set]

    return filepaths_dict

def get_file_meta(nav_set_uid, file_pattern, filepath):
    """Gets all the meta data information for one specific
    file. It is up to the user to separate a file's information into
    separate bands.

    Assumes the file exists.

    >>> file_info = get_file_meta(IBAND_NAV_UID, IBAND_REGEX, "CREFLI_npp_d20130311_t1916582_e1918223.hdf")
    Traceback (most recent call last):
    ...
    ValueError: Could not find enough files matching file pattern: 'GITCO_npp_d20130311_s1916582_e1918223_b*_c*_*.h5'
    """
    base_path,filename = os.path.split(filepath)
    m = re.match(file_pattern, filename)
    if not m:
        log.error("Filename '%s' does not match the pattern provided '%s'" % (filename, file_pattern))
        raise ValueError("Filename '%s' does not match the pattern provided '%s'" % (filename, file_pattern))

    file_info = {}
    file_info.update(m.groupdict())
    file_info.update(FILE_REGEX[file_pattern])
    file_info["data_dir"] = base_path
    file_info["data_filepath"] = filepath

    # Get start time
    _convert_datetimes = file_info["date_convert_func"]
    file_info["start_time"] = _convert_datetimes(file_info["date_str"], file_info["start_str"])
    if "end_str" in file_info:
        file_info["end_time"]   = _convert_datetimes(file_info["date_str"], file_info["end_str"])

    # Geo file information
    # MUST do before satellite constant so we don't get the right entry in the glob
    file_info["geo_filename_pat"] = file_info[K_GEO_PATTERN] % file_info
    file_info["geo_filepath"] = _safe_glob(os.path.join(base_path, file_info["geo_filename_pat"]))

    # Get the constant value for whatever satellite we have
    file_info["sat"] = SATELLITES[file_info["sat"]]
    # XXX: If band kind is different this will have to be taken from a dictionary
    file_info["kind"] = BKIND_CREFL
    file_info["data_kind"] = DKIND_CREFL

    file_info["bands"] = [ DATASET2BID[ds] for ds in file_info[K_DATASETS] ]

    return file_info

def get_data_from_dataset(ds,
        data_fill_value,
        scale_factor,
        scale_offset,
        fill_value=DEFAULT_FILL_VALUE):
    # get data
    data = ds.get().astype(numpy.float32)

    # unscale data
    fill_mask = data == data_fill_value
    numpy.multiply(data, scale_factor, out=data)
    numpy.add(data, scale_offset, out=data)
    if fill_value is None: fill_value = data_fill_value
    data[fill_mask] = fill_value

    return data

def get_attr_from_dataset(
        ds, file_info):
    ds_info = ds.attributes()

    # fill value
    data_fill_value = ds_info[file_info[K_FILL_VALUE]]

    # scale factor
    scale_factor = ds_info[file_info[K_SCALE_FACTOR]]

    # scale offset
    scale_offset = ds_info[file_info[K_SCALE_OFFSET]]

    # units (not used)

    return data_fill_value,scale_factor,scale_offset


def read_data_file(file_info, fill_value=DEFAULT_FILL_VALUE):
    """Read information from the HDF4 file specified by ``data_filepath``
    in the ``file_info`` passed as the first argument.
    
    Any numeric data
    returned will have the optional ``fill_value`` keyword for any invalid
    data points or data that could not be found/calculated. The default is
    the :ref:`DEFAULT_FILL_VALUE <default_fill_value>` constant value. If
    ``fill_value`` is ``None``, the fill value will be the same as in the
    crefl file.

    The following keys are required in the ``file_info`` dictionary (all-caps
    means a constant defined in this file):

        - data_filepath:
            The filepath of the crefl file to operate on
        - K_DATASETS:
            A list of dataset names to get info for (not include navigation)
        - K_FILL_VALUE:
            Attribute name in the datasets for the fill_value of the data
        - K_SCALE_FACTOR:
            Attribute name in the datasets for the scale_factor of the data
        - K_SCALE_OFFSET:
            Attribute name in the datasets for the scale_offset of the data
        - kind:
            The kind of the band in the data (I, M, etc.)

    This function fills in file_info with more data, primarily the ``bands``
    key whose value is a dictionary of dictionaries holding 'per dataset'
    information that can be used by other polar2grid components.
    """
    # Open the file to get additional information
    h = SD.SD(file_info["data_filepath"], SD.SDC.READ)

    # Pull band information
    file_info["bands"] = {}
    for ds_name in file_info[K_DATASETS]:
        try:
            ds = h.select(ds_name)
        except hdf_error.HDF4Error:
            msg = "Data set '%s' does not exist in '%s'" % (ds_name,file_info["data_filepath"])
            log.error(msg)
            raise ValueError(msg)

        # Get attributes
        data_fill_value,scale_factor,scale_offset = get_attr_from_dataset(
                ds, file_info
                )

        # Get the data
        if fill_value is None:
            fill_value = data_fill_value
        data = get_data_from_dataset(ds,
                data_fill_value,
                scale_factor,
                scale_offset,
                fill_value=fill_value
                )

        # write information to the file information
        if data.shape[0] == file_info[K_ROWS_750] and data.shape[1] == file_info[K_COLUMNS_750]:
            res = PIXEL_SIZE_750
        elif data.shape[0] == file_info[K_ROWS_350] and data.shape[1] == file_info[K_COLUMNS_350]:
            res = PIXEL_SIZE_350
        else:
            log.error("Don't know how to handle data shape '%r'" % (data.shape,))
            raise ValueError("Don't know how to handle data shape '%r'" % (data.shape,))

        file_info["bands"][(file_info["kind"],DATASET2BID[ds_name])] = {
                "data"          : data,
                "data_kind"     : DATASET2DKIND[ds_name],
                "remap_data_as" : DATASET2DKIND[ds_name],
                "kind"          : file_info["kind"],
                "band"          : DATASET2BID[ds_name],
                "rows_per_scan" : DATASET2RPS[ds_name],
                "fill_value"    : fill_value,
                "pixel_size"    : res
                }

    # Get Navigation data
    lat_ds = h.select(file_info[K_LATITUDE])
    lat_fv,lat_factor,lat_offset = get_attr_from_dataset(lat_ds, file_info)
    file_info["latitude"] = get_data_from_dataset(
            lat_ds, lat_fv, lat_factor, lat_offset)
    lat_shape = file_info["latitude"].shape

    lon_ds = h.select(file_info[K_LATITUDE])
    lon_fv,lon_factor,lon_offset = get_attr_from_dataset(lon_ds, file_info)
    file_info["longitude"] = get_data_from_dataset(
            lon_ds, lon_fv, lon_factor, lon_offset)
    lon_shape = file_info["longitude"].shape
    if lat_shape != lon_shape:
        log.error("Latitude and longitude data are a different shape")
        raise ValueError("Latitude and longitude data are a different shape")

    if lat_shape[0] == DIM_LINES_750 and lat_shape[1] == DIM_SAMPLES_750:
        file_info["pixel_size"] = PIXEL_SIZE_750
    elif lat_shape[0] == DIM_LINES_350 and lat_shape[1] == DIM_SAMPLES_350:
        file_info["pixel_size"] = PIXEL_SIZE_350
    else:
        log.error("Don't know how to handle nav shape '%r'" % (lat_shape,))
        raise ValueError("Don't know how to handle nav shape '%r'" % (lat_shape,))

    return file_info

def main():
    from argparse import ArgumentParser
    description = """Simple command line interface to test what information
    the guidebook returns for provided files.
    """
    parser = ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
            help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_argument('--doctest', dest="run_doctests", action="store_true", default=False,
            help="Run doctests")
    parser.add_argument("data_files", nargs="*",
            help="1 or more crefl product files")
    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, args.verbosity)])

    if args.run_doctests:
        import doctest
        return doctest.testmod()

    if not args.data_files:
        print "No files were provided"
        return 0

    from pprint import pprint
    for fn in args.data_files:
        print "###              %s                ###" % fn
        pprint(get_file_info(fn))

if __name__ == "__main__":
    sys.exit(main())

