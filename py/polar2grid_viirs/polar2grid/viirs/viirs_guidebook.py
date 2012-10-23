#!/usr/bin/env python
# encoding: utf-8
"""
Provide information about ADL product files for a variety of uses.

:group Data Kinds: K_*
:group Guides: ROWS_PER_SCAN,COLS_PER_ROW,DATA_KINDS,*_GUIDE

:author:       David Hoese (davidh)
:author:       Ray Garcia (rayg)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from polar2grid.core import UTC
from polar2grid.core.constants import *
import h5py as h5
import numpy as np

import sys, os
import re
import logging
from datetime import datetime,timedelta

LOG = logging.getLogger(__name__)
UTC= UTC()

K_LATITUDE = 'LatitudeVar'
K_LONGITUDE = 'LongitudeVar'
K_RADIANCE = 'RadianceVar'
K_REFLECTANCE = 'ReflectanceVar'
K_BTEMP = "BrightnessTemperatureVar"
K_SOLARZENITH = "SolarZenithVar"
K_ALTITUDE = 'AltitudeVar'
K_RADIANCE_FACTORS = "RadianceFactorsVar"
K_REFLECTANCE_FACTORS = "ReflectanceFactorsVar"
K_BTEMP_FACTORS = "BrightnessTemperatureFactorsVar"
K_STARTTIME = "StartTimeVar"
K_MODESCAN = "ModeScanVar"
K_MODEGRAN = "ModeGranVar"
K_QF3 = "QF3Var"
K_NAVIGATION = 'NavigationFilenameGlob'  # glob to search for to find navigation file that corresponds
K_GEO_REF = 'CdfcbGeolocationFileGlob' # glob which would match the N_GEO_Ref attribute

GEO_GUIDE = {
        BKIND_M : 'GMODO',
        BKIND_I : 'GIMGO'
        }

FACTORS_GUIDE = {
        DKIND_REFLECTANCE : K_REFLECTANCE_FACTORS,
        DKIND_RADIANCE    : K_RADIANCE_FACTORS,
        DKIND_BTEMP       : K_BTEMP_FACTORS
        }

# FIXME: add RadianceFactors/ReflectanceFactors
GEO_FILE_GUIDE = {
            r'GITCO.*' : {
                            K_LATITUDE: '/All_Data/VIIRS-IMG-GEO-TC_All/Latitude',
                            K_LONGITUDE: '/All_Data/VIIRS-IMG-GEO-TC_All/Longitude',
                            K_ALTITUDE: '/All_Data/VIIRS-IMG-GEO-TC_All/Height',
                            K_STARTTIME: '/All_Data/VIIRS-IMG-GEO-TC_All/StartTime',
                            K_SOLARZENITH: '/All_Data/VIIRS-IMG-GEO-TC_All/SolarZenithAngle'
                            },
            r'GMTCO.*' : {
                            K_LATITUDE: '/All_Data/VIIRS-MOD-GEO-TC_All/Latitude',
                            K_LONGITUDE: '/All_Data/VIIRS-MOD-GEO-TC_All/Longitude',
                            K_ALTITUDE: '/All_Data/VIIRS-MOD-GEO-TC_All/Height',
                            K_STARTTIME: '/All_Data/VIIRS-MOD-GEO-TC_All/StartTime',
                            K_SOLARZENITH: '/All_Data/VIIRS-MOD-GEO-TC_All/SolarZenithAngle'
                            },
            r'GDNBO.*' : {
                            K_LATITUDE: '/All_Data/VIIRS-DNB-GEO_All/Latitude',
                            K_LONGITUDE: '/All_Data/VIIRS-DNB-GEO_All/Longitude',
                            K_ALTITUDE: '/All_Data/VIIRS-DNB-GEO_All/Height',
                            K_STARTTIME: '/All_Data/VIIRS-DNB-GEO_All/StartTime',
                            K_SOLARZENITH: '/All_Data/VIIRS-DNB-GEO_All/SolarZenithAngle'
                            }
            }
SV_FILE_GUIDE = {
            r'SV(?P<file_kind>[IM])(?P<file_band>\d\d).*': { 
                            K_RADIANCE: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/Radiance',
                            K_REFLECTANCE: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/Reflectance',
                            K_BTEMP: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/BrightnessTemperature',
                            K_RADIANCE_FACTORS: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/RadianceFactors',
                            K_REFLECTANCE_FACTORS: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/ReflectanceFactors',
                            K_BTEMP_FACTORS: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/BrightnessTemperatureFactors',
                            K_MODESCAN: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/ModeScan',
                            K_MODEGRAN: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/ModeGran',
                            K_QF3: '/All_Data/VIIRS-%(file_kind)s%(int(file_band))d-SDR_All/QF3_SCAN_RDR',
                            K_GEO_REF: r'%(GEO_GUIDE[kind])s_%(sat)s_d%(date)s_t%(file_start_time_str)s_e%(file_end_time_str)s_b%(orbit)s_*_%(site)s_%(domain)s.h5',
                            K_NAVIGATION: r'G%(file_kind)sTCO_%(sat)s_d%(date)s_t%(file_start_time_str)s_e%(file_end_time_str)s_b%(orbit)s_*_%(site)s_%(domain)s.h5' },
            r'SVDNB.*': { K_RADIANCE: '/All_Data/VIIRS-DNB-SDR_All/Radiance',
                            K_REFLECTANCE: None,
                            K_BTEMP: None,
                            K_RADIANCE_FACTORS: '/All_Data/VIIRS-DNB-SDR_All/RadianceFactors',
                            K_REFLECTANCE_FACTORS: None,
                            K_BTEMP_FACTORS: None,
                            K_MODESCAN: '/All_Data/VIIRS-DNB-SDR_All/ModeScan',
                            K_MODEGRAN: '/All_Data/VIIRS-DNB-SDR_All/ModeGran',
                            K_QF3: '/All_Data/VIIRS-DNB-SDR_All/QF3_SCAN_RDR',
                            K_GEO_REF: r'GDNBO_%(sat)s_d%(date)s_t%(file_start_time_str)s_e%(file_end_time_str)s_b%(orbit)s_*_%(site)s_%(domain)s.h5',
                            K_NAVIGATION: r'GDNBO_%(sat)s_d%(date)s_t%(file_start_time_str)s_e%(file_end_time_str)s_b%(orbit)s_*_%(site)s_%(domain)s.h5'}
            }

ROWS_PER_SCAN = {
        BKIND_M  : 16,
        "GMTCO" : 16,
        BKIND_I  : 32,
        "GITCO" : 32,
        BKIND_DNB : 16,
        "GDNBO" : 16
        }

COLS_PER_ROW = {
        BKIND_M   : 3200,
        BKIND_I   : 6400,
        BKIND_DNB : 4064
        }

DATA_KINDS = {
        (BKIND_M,BID_01) : DKIND_REFLECTANCE,
        (BKIND_M,BID_02) : DKIND_REFLECTANCE,
        (BKIND_M,BID_03) : DKIND_REFLECTANCE,
        (BKIND_M,BID_04) : DKIND_REFLECTANCE,
        (BKIND_M,BID_05) : DKIND_REFLECTANCE,
        (BKIND_M,BID_06) : DKIND_REFLECTANCE,
        (BKIND_M,BID_07) : DKIND_REFLECTANCE,
        (BKIND_M,BID_08) : DKIND_REFLECTANCE,
        (BKIND_M,BID_09) : DKIND_REFLECTANCE,
        (BKIND_M,BID_10) : DKIND_REFLECTANCE,
        (BKIND_M,BID_11) : DKIND_REFLECTANCE,
        (BKIND_M,BID_12) : DKIND_BTEMP,
        (BKIND_M,BID_13) : DKIND_BTEMP,
        (BKIND_M,BID_14) : DKIND_BTEMP,
        (BKIND_M,BID_15) : DKIND_BTEMP,
        (BKIND_M,BID_16) : DKIND_BTEMP,
        (BKIND_I,BID_01) : DKIND_REFLECTANCE,
        (BKIND_I,BID_02) : DKIND_REFLECTANCE,
        (BKIND_I,BID_03) : DKIND_REFLECTANCE,
        (BKIND_I,BID_04) : DKIND_BTEMP,
        (BKIND_I,BID_05) : DKIND_BTEMP,
        (BKIND_I,BID_06) : DKIND_REFLECTANCE,
        (BKIND_DNB,NOT_APPLICABLE) : DKIND_RADIANCE
        }

VAR_PATHS = {
        (BKIND_M,BID_01) : K_REFLECTANCE,
        (BKIND_M,BID_02) : K_REFLECTANCE,
        (BKIND_M,BID_03) : K_REFLECTANCE,
        (BKIND_M,BID_04) : K_REFLECTANCE,
        (BKIND_M,BID_05) : K_REFLECTANCE,
        (BKIND_M,BID_06) : K_REFLECTANCE,
        (BKIND_M,BID_07) : K_REFLECTANCE,
        (BKIND_M,BID_08) : K_REFLECTANCE,
        (BKIND_M,BID_09) : K_REFLECTANCE,
        (BKIND_M,BID_10) : K_REFLECTANCE,
        (BKIND_M,BID_11) : K_REFLECTANCE,
        (BKIND_M,BID_12) : K_BTEMP,
        (BKIND_M,BID_13) : K_BTEMP,
        (BKIND_M,BID_14) : K_BTEMP,
        (BKIND_M,BID_15) : K_BTEMP,
        (BKIND_M,BID_16) : K_BTEMP,
        (BKIND_I,BID_01) : K_REFLECTANCE,
        (BKIND_I,BID_02) : K_REFLECTANCE,
        (BKIND_I,BID_03) : K_REFLECTANCE,
        (BKIND_I,BID_04) : K_BTEMP,
        (BKIND_I,BID_05) : K_BTEMP,
        (BKIND_I,BID_06) : K_REFLECTANCE,
        (BKIND_DNB,NOT_APPLICABLE) : K_RADIANCE
        }

band2const = {
        "01" : BID_01,
        "02" : BID_02,
        "03" : BID_03,
        "04" : BID_04,
        "05" : BID_05,
        "06" : BID_06,
        "07" : BID_07,
        "08" : BID_08,
        "09" : BID_09,
        "10" : BID_10,
        "11" : BID_11,
        "12" : BID_12,
        "13" : BID_13,
        "14" : BID_14,
        "15" : BID_15,
        "16" : BID_16
        }

# missing value sentinels for different datasets
# 0 if scaling exists, 1 if scaling is None
MISSING_GUIDE = {
                DKIND_REFLECTANCE: (lambda A: A>=65528, lambda A:A<0.0),
                DKIND_RADIANCE: (lambda A: A>=65528, lambda A: A<0.0),
                DKIND_BTEMP: (lambda A: A>=65528, lambda A: A<0.0),
                K_SOLARZENITH: (lambda A: A>=65528, lambda A: A<0.0),
                K_MODESCAN: (lambda A: A>1, lambda A: A>1),
                K_LATITUDE: (lambda A: A>=65528, lambda A: A<=-999),
                K_LONGITUDE: (lambda A: A>=65528, lambda A: A<=-999)
                }


# a regular expression to split up granule names into dictionaries
RE_NPP = re.compile('(?P<file_kindnband>[A-Z0-9]+)_(?P<sat>[A-Za-z0-9]+)_d(?P<date>\d+)_t(?P<file_start_time_str>\d+)_e(?P<file_end_time_str>\d+)_b(?P<orbit>\d+)_c(?P<created_time>\d+)_(?P<site>[a-zA-Z0-9]+)_(?P<domain>[a-zA-Z0-9]+)\.h5')
# format string to turn it back into a filename
FMT_NPP = r'%(file_kindnband)s_%(sat)s_d%(date)s_t%(file_start_time_str)s_e%(file_end_time_str)s_b%(orbit)s_c%(created_time)s_%(site)s_%(domain)s.h5'

class evaluator(object):
    """
    evaluate expressions in format statements
    e.g. '%(4*2)d %(", ".join([c]*b))s' % evaluator(a=2,b=3,c='foo')
    """
    def __init__(self,**argd):
        vars(self).update(argd)
    def __getitem__(self, expr):
        return eval(expr, globals(), vars(self))


def get_datetimes(finfo):
    """Takes a file info dictionary and creates a datetime object for the
    start of the granule and the end of the granule.
    """
    d = finfo["date"]
    st = finfo["file_start_time_str"]
    s_us = int(st[-1])*100000
    et = finfo["file_end_time_str"]
    e_us = int(et[-1])*100000
    s_dt = datetime.strptime(d + st[:-1], "%Y%m%d%H%M%S").replace(tzinfo=UTC, microsecond=s_us)
    e_dt = datetime.strptime(d + et[:-1], "%Y%m%d%H%M%S").replace(tzinfo=UTC, microsecond=e_us)
    finfo["file_start_time"] = s_dt
    finfo["file_end_time"] = e_dt

def h5path(hp, path, h5_path, required=False):
    "traverse an hdf5 path to return a nested data object"
    LOG.debug('fetching %s from %s' % (path, h5_path))
    x = hp
    for a in path.split('/'):
        if a:
            if a in x:
                x = x[a]
            else:
                LOG.debug("Couldn't find %s (or its parent) in %s" % (a,path))
                x = None
                break
        else:
            # If they put a / at the end of the var path
            continue
    if x is hp:
        LOG.error("Could not get %s from h5 file" % path)
        x = None

    if x is None and required:
        LOG.error("Couldn't get data %s from %s" % (path, h5_path))
        raise ValueError("Couldn't get data %s from %s" % (path, h5_path))

    return x

def _st_to_datetime(st):
    """Convert a VIIRS StartTime which is in microseconds since 1958-01-01 to
    a datetime object.
    """
    base = datetime(1958, 1, 1, 0, 0, 0)
    return base + timedelta(microseconds=int(st))

def file_info(fn):
    """Given a filename, returns a dictionary of information that could
    be derived.

    :postcondition:
        The returned ``finfo`` will have the following keys:
            - kind
            - band
            - data_kind
            - rows_per_scan
            - cols_per_row
            - factors
            - geo_glob
            - img_path

    :attention:
        This method does not require that the file actually exists.

    :Parameters:
        fn : str
            Filename of image data to be analyzed

    :raises ValueError:
        if filename matches 1 regular expression for a data file, but not of a generic NPP filename
    """
    fn = os.path.abspath(fn)
    finfo = {}
    finfo["img_path"] = fn
    finfo["base_path"],finfo["filename"] = base_path,filename = os.path.split(fn)

    for pat, nfo in SV_FILE_GUIDE.items():
        # Find what type of file we have
        m = re.match(pat, filename)
        if not m:
            continue

        # collect info from filename
        pat_match = RE_NPP.match(filename)
        if not pat_match:
            LOG.error("Filename matched initial pattern, but not full name pattern")
            raise ValueError("Filename matched initial pattern, but not full name pattern")
        pat_info = dict(pat_match.groupdict())

        minfo = m.groupdict()
        # Translate band info into constants for rest of polar2grid processing
        if "file_kind" not in minfo:
            # For dnb
            minfo["kind"] = BKIND_DNB
            minfo["band"] = NOT_APPLICABLE
        elif minfo["file_kind"] == "M":
            minfo["kind"] = BKIND_M
        elif minfo["file_kind"] == "I":
            minfo["kind"] = BKIND_I
        else:
            LOG.error("Band kind not known '%s'" % minfo["kind"])
            raise ValueError("Band kind not known '%s'" % minfo["kind"])

        # Translate band identifier/number into constants
        if "file_band" in minfo:
            if minfo["file_band"] not in band2const:
                LOG.error("Band number not known '%s'" % (minfo["file_band"],))
                raise ValueError("Band number not known '%s'" % (minfo["file_band"],))
            minfo["band"] = band2const[minfo["file_band"]]

        # merge the guide info
        finfo.update(pat_info)
        finfo.update(minfo)

        # Figure out what type of data we want to use
        dkind = (finfo["kind"],finfo["band"])
        if dkind not in DATA_KINDS:
            LOG.error("Data kind not known (Kind: %s; Band: %s)" % dkind)
            raise ValueError("Data kind not known (Kind: %s; Band: %s)" % dkind)
        finfo["data_kind"] = DATA_KINDS[dkind]
        finfo["rows_per_scan"] = ROWS_PER_SCAN[finfo["kind"]]
        finfo["cols_per_row"] = COLS_PER_ROW[finfo["kind"]]
        finfo["factors"] = FACTORS_GUIDE[finfo["data_kind"]]

        # Convert time information to datetime objects
        get_datetimes(finfo)
        finfo.update(**nfo)
        eva = evaluator(GEO_GUIDE=GEO_GUIDE, **finfo)
        for k,v in finfo.items():
            if isinstance(v,str):
                finfo[k] = v % eva
        finfo["geo_glob"] = os.path.join(base_path, finfo[K_NAVIGATION])
        return finfo
    LOG.warning('unable to find %s in guidebook' % filename)
    return finfo

def read_file_info(finfo, extra_mask=None, fill_value=-999, dtype=np.float32):
    """Reads the hdf file associated with the file info dictionary provided
    and returns all of the information that could be useful outside of this
    function.

    :precondition:
        ``finfo`` was returned from `file_info` or meets the post
        condition of `file_info`.
    :precondition:
        ``finfo`` is allowed to be changed/updated/added to in place.
    :postcondition:
        ``finfo`` will have the following new keys:
            - image_data
            - image_mask
            - mode_mask

    :Parameters:
        finfo : dict
            File info dictionary returned from `file_info`.
    :Keywords:
        extra_mask : ``numpy.ndarray``
            An additional mask that will be used to fill the data.
        fill_value : int or float
            Fill value to be used for all bad data found.
        dtype : ``numpy.dtype``
            The data type that the returned data array will be forced to.
    """
    hp = h5.File(finfo["img_path"], 'r')

    data_kind = finfo["data_kind"]
    data_var_path = finfo[VAR_PATHS[(finfo["kind"],finfo["band"])]]
    factors_var_path = finfo[finfo["factors"]]
    qf3_var_path = finfo[K_QF3]

    # Get image data
    h5v = h5path(hp, data_var_path, finfo["img_path"], required=True)
    image_data = h5v[:,:]
    image_data = image_data.astype(dtype)
    del h5v

    # Get QF3 data
    h5v = h5path(hp, qf3_var_path, finfo["img_path"], required=True)
    qf3_data = h5v[:]
    del h5v

    # Get scaling function (also reads scaling factors from hdf)
    factvar = h5path(hp, factors_var_path, finfo["img_path"], required=False)   # FUTURE: make this more elegant please
    if factvar is None:
        LOG.debug("No scaling factors found for %s at %s (this is OK)" % (data_var_path, factors_var_path))
        def scaler(image_data):
            return image_data,np.zeros(image_data.shape).astype(np.bool)
        needs_scaling = False
    else:
        factor_list = list(factvar[:])
        LOG.debug("scaling factors for %s are %s" % (data_var_path, str(factor_list)))
        if len(factor_list) % 2 != 0:
            LOG.error("There are an odd number of scaling factors for %s" % (data_var_path,))
            raise ValueError("There are an odd number of scaling factors for %s" % (data_var_path,))

        # Figure out how data should be scaled
        def scaler(image_data, scaling_factors=factor_list):
            num_grans = len(scaling_factors)/2
            gran_size = image_data.shape[0]/num_grans
            scaling_mask = np.zeros(image_data.shape)
            for i in range(num_grans):
                start_idx = i * gran_size
                end_idx = start_idx + gran_size
                m = scaling_factors[i*2]
                b = scaling_factors[i*2 + 1]
                if m <= -999 or b <= -999:
                    scaling_mask[start_idx : end_idx] = 1
                else:
                    image_data[start_idx : end_idx] = m * image_data[start_idx : end_idx] + b

            scaling_mask = scaling_mask.astype(np.bool)
            return image_data,scaling_mask

        needs_scaling = True

    # Calculate mask
    mask = MISSING_GUIDE[data_kind][not needs_scaling](image_data) if data_kind in MISSING_GUIDE else None
    if extra_mask is not None:
        mask = mask | extra_mask

    # Scale image data
    image_data,scaling_mask = scaler(image_data)
    mask = mask | scaling_mask

    # Create scan_quality array
    scan_quality = np.nonzero(np.repeat(qf3_data > 0, finfo["rows_per_scan"]))

    # Mask off image data
    image_data[mask] = fill_value

    finfo["image_data"] = image_data
    finfo["image_mask"] = mask
    finfo["mode_mask"] = None
    finfo["scan_quality"] = scan_quality

    return finfo

def geo_info(fn):
    """Will return a dictionary of information that could be derived from the
    provided geo-navigation filename.

    :postcondition:
        The returned ``finfo`` (or ginfo) will contain the following keys:
            - geo_path
            - kind
            - rows_per_scan

    :Parameters:
        fn : str
            Geo-navigation filename to be analyzed

    :raises ValueError:
        if filename matches 1 regular expression for a geonav, but not of a generic NPP filename
    """
    fn = os.path.abspath(fn)
    finfo = {}
    finfo["geo_path"] = fn
    finfo["filename"] = filename = os.path.split(fn)[1]
    for pat, nfo in GEO_FILE_GUIDE.items():
        # Find what type of file we have
        m = re.match(pat, filename)
        if not m:
            continue

        # collect info from filename
        pat_match = RE_NPP.match(filename)
        if not pat_match:
            LOG.error("Filename matched initial pattern, but not full name pattern")
            raise ValueError("Filename matched initial pattern, but not full name pattern")
        pat_info = dict(pat_match.groupdict())
        minfo = m.groupdict()

        # merge the guide info
        finfo.update(pat_info)
        finfo.update(minfo)

        # Get constant/known information from mappings
        finfo["rows_per_scan"] = ROWS_PER_SCAN[finfo["file_kindnband"]]

        # Fill any information if needed
        finfo.update(**nfo)
        eva = evaluator(GEO_GUIDE=GEO_GUIDE, **finfo)
        for k,v in finfo.items():
            if isinstance(v,str):
                finfo[k] = v % eva
        return finfo
    LOG.warning('unable to find %s in guidebook' % filename)
    return finfo

def read_geo_info(finfo, fill_value=-999, dtype=np.float32):
    """Will fill in finfo with the data that is assumed to
    be necessary for future processing.

    :precondition:
        ``finfo`` is allowed to be changed/updated/added to in place.
    :precondition:
        ``finfo`` cam from `geo_info` or at least meets the post
        condition of `geo_info`.
    :postcondition:
        ``finfo`` will have the following keys added:
            - lat_data
            - lon_data
            - lat_mask
            - lon_mask
            - mode_mask
            - start_time
            - scan_quality

    :Parameters:
        finfo : dict
            Dictionary of information from `geo_info`.
    :Keywords:
        fill_value : int or float
            Fill value for any bad data found.
        dtype : ``numpy.dtype``
            Data type that the returned data is forced to.
    """

    hp = h5.File(finfo["geo_path"], 'r')

    lat_var_path = finfo[K_LATITUDE]
    lon_var_path = finfo[K_LONGITUDE]
    st_var_path = finfo[K_STARTTIME]
    sza_var_path = finfo[K_SOLARZENITH]

    # Get latitude data
    h5v = h5path(hp, lat_var_path, finfo["geo_path"], required=True)
    lat_data = h5v[:,:]
    lat_data = lat_data.astype(dtype)
    del h5v

    # Get longitude data
    h5v = h5path(hp, lon_var_path, finfo["geo_path"], required=True)
    lon_data = h5v[:,:]
    lon_data = lon_data.astype(dtype)
    del h5v

    # Get start time
    h5v = h5path(hp, st_var_path, finfo["geo_path"], required=True)
    start_time = _st_to_datetime(h5v[0])

    # Get solar zenith angle
    h5v = h5path(hp, sza_var_path, finfo["geo_path"], required=True)
    sza_data = h5v[:,:]
    sza_data = sza_data.astype(dtype)

    # Calculate latitude mask
    lat_mask = MISSING_GUIDE[K_LATITUDE][1](lat_data) if K_LATITUDE in MISSING_GUIDE else None

    # Calculate longitude mask
    lon_mask = MISSING_GUIDE[K_LONGITUDE][1](lat_data) if K_LONGITUDE in MISSING_GUIDE else None

    # Calculate solar zenith angle mask
    sza_mask = MISSING_GUIDE[K_SOLARZENITH][1](lat_data) if K_SOLARZENITH in MISSING_GUIDE else None

    # Mask off bad data
    # NOTE: There could still be missing image data to account for
    sza_data[ lat_mask | lon_mask | sza_mask ] = fill_value
    lat_data[ lat_mask ] = fill_value
    lon_data[ lon_mask ] = fill_value

    finfo["lat_data"] = lat_data
    finfo["lon_data"] = lon_data
    finfo["lat_mask"] = lat_mask
    finfo["lon_mask"] = lon_mask
    finfo["mode_mask"] = sza_data
    finfo["start_time"] = start_time
    # Rows only
    finfo["scan_quality"] = (np.unique(np.nonzero(lat_mask)[0]),)
    return finfo

def generic_info(fn):
    """Wrapper function that tells what function should be called based
    on the first letter of the filename passed.

    'S' for data files, 'G' for geo files

    :raises ValueError: if `fn` doesn't start with 'S' or 'G'
    """
    if os.path.split(fn)[1].startswith("S"):
        return file_info(fn)
    elif os.path.split(fn)[1].startswith("G"):
        return geo_info(fn)
    else:
        LOG.error("Unknown file type for %s" % fn)
        raise ValueError("Unknown file type for %s" % fn)

def generic_read(fn, finfo):
    """Wrapper function that tells what read function should be called based
    on the first letter of the filename passed.

    'S' for data files, 'G' for geo files

    :raises ValueError: if `fn` doesn't start with 'S' or 'G'
    """
    if os.path.split(fn)[1].startswith("S"):
        return read_file_info(finfo)
    elif os.path.split(fn)[1].startswith("G"):
        return read_geo_info(finfo)
    else:
        LOG.error("Unknown file type for %s" % fn)
        raise ValueError("Unknown file type for %s" % fn)

def main():
    import optparse
    from pprint import pprint
    usage = """
%prog [options] filename1.h5

"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
            help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_option('-r', '--no-read', dest='read_h5', action='store_false', default=True,
            help="don't read or look for the h5 file, only analyze the filename")
    (options, args) = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])

    if not args:
        parser.error( 'must specify 1 filename, try -h or --help.' )
        return -1

    for fn in args:
        try:
            finfo = generic_info(fn)
        except:
            LOG.error("Failed to get info from filename '%s'" % fn, exc_info=1)
            continue

        if options.read_h5:
            generic_read(fn, finfo)
            pprint(finfo)
            if finfo["data_kind"] == K_RADIANCE:
                data_shape = str(finfo["data"].shape)
                print "Got Radiance with shape %s" % data_shape
            elif finfo["data_kind"] == K_REFLECTANCE:
                data_shape = str(finfo["data"].shape)
                print "Got Reflectance with shape %s" % data_shape
            elif finfo["data_kind"] == K_BTEMP:
                data_shape = str(finfo["data"].shape)
                print "Got Brightness Temperature with shape %s" % data_shape
            else:
                data_shape = "Unknown data type"
                print "Got %s" % data_shape
            mask_shape = str(finfo["mask"].shape)
            print "Mask was created with shape %s" % mask_shape
        else:
            pprint(finfo)

if __name__ == '__main__':
    sys.exit(main())
