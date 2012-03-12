#!/usr/bin/env python
# encoding: utf-8
"""
adl_guidebook.py
$Id$

Purpose: Provide information about ADL product files for a variety of uses.

Created by rayg@ssec.wisc.edu Jan 2012.
Copyright (c) 2011 University of Wisconsin SSEC. All rights reserved.
Licensed under GNU GPLv3.
"""

import sys, os
import re
import logging
from datetime import datetime
from keoni.time.epoch import UTC

import h5py

LOG = logging.getLogger('adl_cdfcb')
UTC= UTC()

K_LATITUDE = 'LatitudeVar'
K_LONGITUDE = 'LongitudeVar'
K_ALTITUDE = 'AltitudeVar'
K_RADIANCE = 'RadianceVar'
K_RADIANCE_FACTORS = "RadianceFactorsVar"
K_REFLECTANCE = 'ReflectanceVar'
K_REFLECTANCE_FACTORS = "ReflectanceFactorsVar"
K_BTEMP = "BrightnessTemperatureVar"
K_BTEMP_FACTORS = "BrightnessTemperatureFactorsVar"
K_SOLARZENITH = "SolarZenithVar"
K_NAVIGATION = 'NavigationFilenameGlob'  # glob to search for to find navigation file that corresponds
K_GEO_REF = 'CdfcbGeolocationFileGlob' # glob which would match the N_GEO_Ref attribute

GEO_GUIDE = {'M' : 'GMODO', 'I': 'GIMGO'}

FACTORS_GUIDE = {
        K_REFLECTANCE : K_REFLECTANCE_FACTORS,
        K_RADIANCE    : K_RADIANCE_FACTORS,
        K_BTEMP       : K_BTEMP_FACTORS
        }

# FIXME: add RadianceFactors/ReflectanceFactors
VAR_GUIDE = { r'GITCO.*' : {
                            K_LATITUDE: '/All_Data/VIIRS-IMG-GEO-TC_All/Latitude',
                            K_LONGITUDE: '/All_Data/VIIRS-IMG-GEO-TC_All/Longitude',
                            K_ALTITUDE: '/All_Data/VIIRS-IMG-GEO-TC_All/Height',
                            K_SOLARZENITH: None
                            },
              r'GMTCO.*' : {
                            K_LATITUDE: '/All_Data/VIIRS-MOD-GEO-TC_All/Latitude',
                            K_LONGITUDE: '/All_Data/VIIRS-MOD-GEO-TC_All/Longitude',
                            K_ALTITUDE: '/All_Data/VIIRS-MOD-GEO-TC_All/Height',
                            K_SOLARZENITH: None
                            },
              r'GDNBO.*' : {
                            K_LATITUDE: '/All_Data/VIIRS-DNB-GEO_All/Latitude',
                            K_LONGITUDE: '/All_Data/VIIRS-DNB-GEO_All/Longitude',
                            K_ALTITUDE: '/All_Data/VIIRS-DNB-GEO_All/Height',
                            K_SOLARZENITH: '/All_Data/VIIRS-DNB-GEO_All/SolarZenithAngle'
                            },
              r'SV(?P<kind>[IM])(?P<band>\d\d).*': { 
                            K_RADIANCE: '/All_Data/VIIRS-%(kind)s%(int(band))d-SDR_All/Radiance',
                            K_REFLECTANCE: '/All_Data/VIIRS-%(kind)s%(int(band))d-SDR_All/Reflectance',
                            K_BTEMP: '/All_Data/VIIRS-%(kind)s%(int(band))d-SDR_All/BrightnessTemperature',
                            K_RADIANCE_FACTORS: '/All_Data/VIIRS-%(kind)s%(int(band))d-SDR_All/RadianceFactors',
                            K_REFLECTANCE_FACTORS: '/All_Data/VIIRS-%(kind)s%(int(band))d-SDR_All/ReflectanceFactors',
                            K_BTEMP_FACTORS: '/All_Data/VIIRS-%(kind)s%(int(band))d-SDR_All/BrightnessTemperatureFactors',
                            K_GEO_REF: r'%(GEO_GUIDE[kind])s_%(sat)s_d%(date)s_t%(start_time)s_e%(end_time)s_b%(orbit)s_*_%(site)s_%(domain)s.h5',
                            K_NAVIGATION: r'G%(kind)sTCO_%(sat)s_d%(date)s_t%(start_time)s_e%(end_time)s_b%(orbit)s_*_%(site)s_%(domain)s.h5' },
              r'SVDNB.*': { K_RADIANCE: '/All_Data/VIIRS-DNB-SDR_All/Radiance',
                            K_REFLECTANCE: None,
                            K_BTEMP: None,
                            K_RADIANCE_FACTORS: '/All_Data/VIIRS-DNB-SDR_All/RadianceFactors',
                            K_REFLECTANCE_FACTORS: None,
                            K_BTEMP_FACTORS: None,
                            K_GEO_REF: r'GDNBO_%(sat)s_d%(date)s_t%(start_time)s_e%(end_time)s_b%(orbit)s_*_%(site)s_%(domain)s.h5',
                            K_NAVIGATION: r'GDNBO_%(sat)s_d%(date)s_t%(start_time)s_e%(end_time)s_b%(orbit)s_*_%(site)s_%(domain)s.h5'}
            }

DATA_KINDS = {
        "M01" : K_REFLECTANCE,
        "M02" : K_REFLECTANCE,
        "M03" : K_REFLECTANCE,
        "M04" : K_REFLECTANCE,
        "M05" : K_REFLECTANCE,
        "M06" : K_REFLECTANCE,
        "M07" : K_REFLECTANCE,
        "M08" : K_REFLECTANCE,
        "M09" : K_REFLECTANCE,
        "M10" : K_REFLECTANCE,
        "M11" : K_REFLECTANCE,
        "M12" : K_BTEMP,
        "M13" : K_BTEMP,
        "M14" : K_BTEMP,
        "M15" : K_BTEMP,
        "M16" : K_BTEMP,
        "I01" : K_REFLECTANCE,
        "I02" : K_REFLECTANCE,
        "I03" : K_REFLECTANCE,
        "I04" : K_BTEMP,
        "I05" : K_BTEMP,
        "I06" : K_REFLECTANCE,
        "DNB" : K_RADIANCE
        }

# missing value sentinels for different datasets
# TODO: Make dependent on if there are scaling factors or not
# 0 if scaling exists, 1 if scaling is None
MISSING_GUIDE = { K_REFLECTANCE: (lambda A: A>=65533, lambda A:A<0.0),
                K_RADIANCE: (lambda A: A>=65533, lambda A: A<0.0),
                K_BTEMP: (lambda A: A>=65533, lambda A: A<0.0),
                K_SOLARZENITH: (lambda A: A>=65533, lambda A: A<0.0)
                }


# a regular expression to split up granule names into dictionaries
RE_NPP = re.compile('(?P<kind>[A-Z0-9]+)_(?P<sat>[A-Za-z0-9]+)_d(?P<date>\d+)_t(?P<start_time>\d+)_e(?P<end_time>\d+)_b(?P<orbit>\d+)_c(?P<created_time>\d+)_(?P<site>[a-zA-Z0-9]+)_(?P<domain>[a-zA-Z0-9]+)\.h5')
# format string to turn it back into a filename
FMT_NPP = r'%(kind)s_%(sat)s_d%(date)s_t%(start_time)s_e%(end_time)s_b%(orbit)s_c%(created_time)s_%(site)s_%(domain)s.h5'


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
    d = finfo["date"]
    st = finfo["start_time"]
    s_us = int(st[-1])*100000
    et = finfo["end_time"]
    e_us = int(et[-1])*100000
    s_dt = datetime.strptime(d + st[:-1], "%Y%m%d%H%M%S").replace(tzinfo=UTC, microsecond=s_us)
    e_dt = datetime.strptime(d + et[:-1], "%Y%m%d%H%M%S").replace(tzinfo=UTC, microsecond=e_us)
    finfo["start_dt"] = s_dt
    finfo["end_dt"] = e_dt

def info(filename):
    """check guidebook for a given filename

    >>> _guide_info('SVM09_npp_d20111208_t1851020_e1852261_b00587_c20111209024749514346_noaa_ops.h5')
    {'ReflectanceVar': '/All_Data/VIIRS-M9-SDR_All/Reflectance', 'NavigationFilenameGlob': 'GMTCO_npp_d20111208_t1851020_e1852261_b00587_*_noaa_ops.h5', 'RadianceVar': '/All_Data/VIIRS-M9-SDR_All/Radiance'}
    >>> _guide_info('GITCO_npp_d20111208_t1851020_e1852261_b00587_c20111209023536161164_noaa_ops.h5')
    {'LatitudeVar': '/All_Data/VIIRS-IMG-GEO-TC_All/Latitude', 'AltitudeVar': '/All_Data/VIIRS-IMG-GEO-TC_All/Height', 'LongitudeVar': '/All_Data/VIIRS-IMG-GEO-TC_All/Longitude'}
    """
    for pat, nfo in VAR_GUIDE.items():
        m = re.match(pat, filename)
        if not m:
            continue
        # collect info from filename
        finfo = dict(RE_NPP.match(filename).groupdict())

        # For dnb
        minfo = m.groupdict()
        if "kind" not in minfo:
            minfo["kind"] = "DNB"
            minfo["band"] = "00"

        # merge the guide info
        finfo.update(minfo)

        if finfo["kind"] not in ["M","I","DNB"]:
            LOG.warning("Band kind not known %s" % finfo["kind"])
            finfo["data_kind"] = None
        else:
            # Figure out what type of data we want to use
            dkind = finfo["kind"] + finfo["band"]
            if dkind not in DATA_KINDS:
                LOG.info("Data kind key not known %s" % dkind)
                finfo["data_kind"] = K_RADIANCE
            else:
                finfo["data_kind"] = DATA_KINDS[dkind]

        finfo["factors"] = FACTORS_GUIDE[finfo["data_kind"]]

        eva = evaluator(GEO_GUIDE=GEO_GUIDE, **finfo)
        # Convert time information to datetime objects
        get_datetimes(finfo)
        finfo.update(**nfo)
        for k,v in finfo.items():
            if isinstance(v,str):
                finfo[k] = v % eva
        return finfo
    LOG.warning('unable to find %s in guidebook' % filename)
    return {}

if __name__=='__main__':
    from pprint import pprint
    for fn in sys.argv[1:]:
        pprint(info(os.path.split(fn)[-1]))
