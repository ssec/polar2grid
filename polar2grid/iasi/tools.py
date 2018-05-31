#!/usr/bin/env python3
# encoding: utf-8
"""
Iasi SDR front end for polar2grid, which extracts band-pass slices of brightness temperature data.

:author:       Ray Garcia (rayg)
:contact:      rayg@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Mar 2013
:license:      GNU GPLv3

Copyright (C) 2013 Space Science and Engineering Center (SSEC),
 University of Wisconsin-Madison.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

This file is part of the polar2grid software package. Polar2grid takes
satellite observation data, remaps it, and writes it to a file format for
input into another program.
Documentation: http://www.ssec.wisc.edu/software/polar2grid/
"""

__docformat__ = "restructuredtext en"

VCSID = '$Id$'

# Much of this is from metahoard.iasi.tools

import numpy as np, glob, os, sys, logging
from collections import namedtuple
import calendar, re
from datetime import datetime
from pprint import pformat
from numpy import array,arange,empty,float32,float64,int8,concatenate,repeat,reshape,rollaxis


LOG = logging.getLogger(__name__)
# format string for printing out information about an iasi_record
IASI_RECORD_FMT = """<IASI Sounding record %(record_name)s scan %(scan_number)d detector %(detector_number)d time %(time)s latitude %(latitude)f longitude %(longitude)s>"""


class iasi_record(object):
    """ Simple data holder for IASI sounder records, i.e. a struct.
    Used as a return data container by generate_ functions.
    """
    record_name = None
    scan_number = None
    detector_number = None

    spectralFreq = None # array
    radiances = None # array
    time = None     # datetime.datetime
    epoch = None    # double precision, unix epoch time
    latitude = None # float
    longitude = None # float
    scanAng = None # float

    metop_zenith_angle = None # degrees
    metop_aziumth_angle = None
    sun_zenith_angle = None
    sun_azimuth_angle = None

    landFrac = None # float
    elevation = None # float

    def __repr__(self):
        return IASI_RECORD_FMT % vars(self)

    def __str__(self):
        return pformat(vars(self))


class iasi_profile(object):
    """ Simple data holder for IASI retrieval records.
    Not currently used.
    """
    record_name = None
    scan_number = None
    detector_number = None

class iasi_image(object):
    """a container object for map data
    """
    latitude = None
    longitude = None



def epoch_from_datetime(x):
    """Convert datetime.datetime object to double precision UNIX epoch time in seconds.
    """
    if isinstance(x,datetime):
        return calendar.timegm( x.utctimetuple() )
    else:
        return [float(calendar.timegm( q.utctimetuple() )) + float(q.microsecond)/1e6 for q in x]


class iis_tiles(object):
    """image tiles from IIS
    """
    pass


CLOUD_MASK_PRODUCTS = [ 'GCcsRadAnalNbClass', 'GCcsRadAnalWgt', 'GCcsRadAnalY', 'GCcsRadAnalZ', 'GCcsRadAnalMean', 'GCcsRadAnalStd' ]

def scale_scanline(prod, spectra=None, factor_table = None):
    """Apply scaling factors for IASI L1B spectra (spectra[spectrumnumber][wavenumber] indexed).
    Returns factor_table which can be used to speed up subsequent calls.
    Output spectra are in mW/m2 sr cm-1
    """
    if not factor_table:
        scaling = prod.get('giadr-scalefactors')
        nscales = scaling.IDefScaleSondNbScale
        offset = scaling.IDefScaleSondNsfirst[0]
        factor_table = zip( range(nscales),
                            array(scaling.IDefScaleSondNsfirst)-offset,
                            array(scaling.IDefScaleSondNslast)-offset+1,
                            array(scaling.IDefScaleSondScaleFactor)
                            )
    if spectra is not None:
        for _,start,end,factor in factor_table:
            spectra[:,start:end] *= 10.**(-factor+5)  # UW scaling preferred has a 1e5 difference : nets us mW/m2 sr cm-1
    return factor_table

def sounder_wavenumber_interval(prod):
    """ Return (vmin, dv, npts) wavenumber interval tuple in cm-1
    """
    IDefNsfirst1b = prod.get("mdr-1c[0].IDefNsfirst1b")
    IDefSpectDWn1b = prod.get("mdr-1c[0].IDefSpectDWn1b")
    IDefNslast1b = prod.get("mdr-1c[0].IDefNslast1b")
    delta = IDefSpectDWn1b / 100. # convert to cm-1
    return delta * (IDefNsfirst1b-1), delta, IDefNslast1b - IDefNsfirst1b + 1

def sounder_wavenumbers(prod):
    """Return sounder wavenumber scale as an array and a delta
    for sample #k: wavenumber(k) = IDefSpectDWn1b * (IDefNsfirst1b + k -2)
    FUTURE: account for any variation that probably doesn't exist between records
    Currently, only the first record's values are being returned.
    Also note that the wavenumber array is shorter than the 8700-wide spectrum
    """
    IDefNsfirst1b = prod.get("mdr-1c[0].IDefNsfirst1b")
    IDefSpectDWn1b = prod.get("mdr-1c[0].IDefSpectDWn1b")
    IDefNslast1b = prod.get("mdr-1c[0].IDefNslast1b")
    delta = IDefSpectDWn1b / 100. # convert to cm-1
    return arange(IDefNsfirst1b-1,IDefNslast1b,dtype=float64) * delta, delta

def ifov_remap(n_snd):
    """ Map the 4 PXs within each IASI IFOV into the 2d array
    input[records][scans][detectors]{other} -> output[2*records][2*scans]{other}
    swapping 0..3 third dimension with doubling of first two dimensions
    returns a new array
    """
    dims = n_snd.shape
    redims = (dims[0]*2, dims[1]*2) + dims[3:]
    snd = empty(redims, n_snd.dtype)
    snd[0::2,1::2] = n_snd[:,:,0] # PX1
    snd[1::2,1::2] = n_snd[:,:,1] # PX2
    snd[1::2,0::2] = n_snd[:,:,2] # PX3
    snd[0::2,0::2] = n_snd[:,:,3] # PX3
    return snd

def ifov_pseudoscan(n_snd):
    """turn one scan-line variable with four detectors into two pseudo-scanlines
    input[scans,detectors,{other}] -> output[2*scans,2,{other}]
    """
    re_snd = n_snd.reshape((1,) + n_snd.shape)
    return ifov_remap( re_snd )

def _convert_image(detector_number):
    "array-construction functions for eugene working with or without detector selection. mildly tricky"
    if None==detector_number:
        return '',lambda A: ifov_remap(array(A))
    else:
        return '%d' % detector_number, array

def _convert_scanline(detector_number):
    if None==detector_number:
        return '',lambda A: ifov_pseudoscan(array(A))
    else:
        return '%d' % detector_number, array

RE_RECORD_INDEX = re.compile('\[(\d+)\]') # extract record number from 'mdr-1c[NNN]'

def _sounder_scanlines_all(prod, line_indices = None, only_geotemporal = False, cloud_dict = None):
    """iterate all the records in a file, returning blocks of scans as iasi_record objects.
    detector number is 0..3
    line_indices is optional parameter listing which scan lines to use, default is all
    """
    crib = None
    scans = [int(x) for x in repeat( range(30), 2 )]  # repeat() will give us numpy.int32 by default
    # create an array of corresponding detector numbers and rearrange them the same as the input data
    dnums = [[0,1,2,3]] * 30
    rearrange = lambda A: ifov_pseudoscan(array(A))
    wnum,dwn = sounder_wavenumbers(prod)
    detector_number = rearrange(dnums)
    if line_indices is not None:
        lines = ['mdr-1c[%d]' % x for x in line_indices]
    else:
        lines = prod._records_['mdr-1c']
    for record_name in lines:
        GGeoSondAnglesMETOP_zen = rearrange(prod.get('%s.GGeoSondAnglesMETOP[][][0]' % (record_name,)))
        GGeoSondAnglesMETOP_az = rearrange(prod.get('%s.GGeoSondAnglesMETOP[][][1]' % (record_name,)))
        GGeoSondAnglesSUN_zen = rearrange(prod.get('%s.GGeoSondAnglesSUN[][][0]' % (record_name,)))
        GGeoSondAnglesSUN_az = rearrange(prod.get('%s.GGeoSondAnglesSUN[][][1]' % (record_name,)))
        GGeoSondLoc_lon = rearrange(prod.get('%s.GGeoSondLoc[][][0]' % (record_name,)))
        GGeoSondLoc_lat = rearrange(prod.get('%s.GGeoSondLoc[][][1]' % (record_name,)))
        scanline = None if only_geotemporal else ifov_pseudoscan(array(prod.get('%s.GS1cSpect[][][]' % (record_name,)),float64))
        GQisFlagQual = None if only_geotemporal else ifov_pseudoscan(array(prod.get('%s.GQisFlagQual[][]' % (record_name,)),int8))
        #GQisFlagQualDetailed = None if only_geotemporal else ifov_pseudoscan(array(prod.get('%s.GQisFlagQualDetailed[][]' % (record_name)),int8))
        OnboardUTC = array(prod.get( '%s.OnboardUTC' % (record_name,)))
        CMP = {}
        if not only_geotemporal:
            for name in CLOUD_MASK_PRODUCTS:
                CMP[name] = rearrange(prod.get( '%s.%s[][]' % (record_name,name)))
        for row in [0,1]:
            if not only_geotemporal:
                pseudoscan = array(scanline[row])
                crib = scale_scanline(prod,pseudoscan,crib)
                #prGQisFlagQualDetailed = array(GQisFlagQualDetailed[row])
                prGQisFlagQual = array(GQisFlagQual[row])
            R = iasi_record()
            R.wavenumbers = wnum
            R.record_index = int( *RE_RECORD_INDEX.findall(record_name) )
            R.record_name = record_name
            R.scan_number = scans   # NOTE: really is field of regard number, 0..29
            R.detector_number = detector_number[row] # 0..3
            R.time = OnboardUTC.repeat(2)
            R.epoch = array(epoch_from_datetime(OnboardUTC)).repeat(2)
            R.radiances = None if only_geotemporal else pseudoscan
            #R.quality_flag_detailed = None if only_geotemporal else prGQisFlagQualDetailed
            R.quality_flag = None if only_geotemporal else prGQisFlagQual
            R.longitude = GGeoSondLoc_lon[row]
            R.latitude = GGeoSondLoc_lat[row]
            R.metop_zenith_angle = GGeoSondAnglesMETOP_zen[row]
            R.metop_azimuth_angle = GGeoSondAnglesMETOP_az[row]
            R.sun_zenith_angle = GGeoSondAnglesSUN_zen[row]
            R.sun_azimuth_angle = GGeoSondAnglesSUN_az[row]
            if not only_geotemporal:
                for name in CLOUD_MASK_PRODUCTS:
                    setattr( R, name, CMP[name][row] )
            if cloud_dict:
                clod = {}
                for k in cloud_dict[(0,0,0)].keys():
                    clod[k] = array([ cloud_dict[(R.record_index,field,det)][k] for field,det in zip(R.scan_number,R.detector_number) ])
                vars(R).update(clod)
            yield R

def _sounder_scanlines_one(prod, detector_number, line_indices = None, only_geotemporal = False, cloud_dict = None):
    """iterate all the records in a file, returning blocks of scans as iasi_record objects.
    detector number is 0..3
    line_indices is optional parameter listing which scan lines to use, default is all
    cloud_dict is an optional dictionary of {(scan#,for#,detector#) : dictionary} additional fields to merge
    """
    crib = None
    scans = range(0,30)
    wnum,dwn = sounder_wavenumbers(prod)
    if line_indices is not None:
        lines = ['mdr-1c[%d]' % x for x in line_indices]
    else:
        lines = prod._records_['mdr-1c']
    for record_name in lines:
        GGeoSondAnglesMETOP = array(prod.get('%s.GGeoSondAnglesMETOP[][%d][]' % (record_name,detector_number)))
        GGeoSondAnglesSUN = array(prod.get('%s.GGeoSondAnglesSUN[][%d][]' % (record_name,detector_number)))
        OnboardUTC = array(prod.get( '%s.OnboardUTC' % record_name))
        GGeoSondLoc = array(prod.get('%s.GGeoSondLoc[][%d][]' % (record_name,detector_number)))
        GQisFlagQual = None if only_geotemporal else array(prod.get('%s.GQisFlagQual[][]' % (record_name)),int8)
        #GQisFlagQualDetailed = None if only_geotemporal else array(prod.get('%s.GQisFlagQualDetailed[][]' % (record_name)),int8)
        if not only_geotemporal:
            scanline = array(prod.get( '%s.GS1cSpect[][%d][]' % (record_name, detector_number)),float64)
            crib = scale_scanline(prod,scanline,crib)
        R = iasi_record()
        R.wavenumbers = wnum
        R.record_name = record_name
        R.record_index = int( *RE_RECORD_INDEX.findall(record_name) )
        R.scan_number = scans
        R.detector_number = detector_number
        R.time = OnboardUTC
        R.radiances = None if only_geotemporal else scanline
        #R.quality_flag_detailed = None if only_geotemporal else GQisFlagQualDetailed
        R.quality_flag = None if only_geotemporal else GQisFlagQual
        R.longitude = GGeoSondLoc[:,0].squeeze()
        R.latitude = GGeoSondLoc[:,1].squeeze()
        R.metop_zenith_angle = GGeoSondAnglesMETOP[:,0].squeeze()
        R.metop_azimuth_angle = GGeoSondAnglesMETOP[:,1].squeeze()
        R.sun_zenith_angle = GGeoSondAnglesSUN[:,0].squeeze()
        R.sun_azimuth_angle = GGeoSondAnglesSUN[:,1].squeeze()
        if not only_geotemporal:
            for name in CLOUD_MASK_PRODUCTS:
                q = array(prod.get( '%s.%s[][%d]' % (record_name,name,detector_number)))
                setattr( R, name, q )
        if cloud_dict:
            clod = {}
            for k in cloud_dict[(0,0,0)].keys():
                clod[k] = array([ cloud_dict[(R.record_index,field,detector_number)][k] for field in R.scan_number ])
            vars(R).update(clod)
        yield R

def sounder_scanlines(prod, detector_number=None, line_indices = None, only_geotemporal = False, cloud_dict = None):
    """iterate all the records in a file, returning blocks of scans as iasi_record objects.
    detector number is 0..3
    line_indices optionally is a list of scan lines e.g. 0..150 (corresponds to the number of records in the file)
    only_geotemporal flag suppresses cloud mask and radiance data
    cloud_dict is an optional dictionary of {(scan#,for#,detector#) : dictionary} additional fields to merge
    FIXME: drop inconsistent use of "scan" in favor of "scan line", "field of regard", "field of view"
    """
    if detector_number is None: return _sounder_scanlines_all(prod,line_indices,only_geotemporal,cloud_dict=cloud_dict)
    else: return _sounder_scanlines_one(prod,detector_number,line_indices,only_geotemporal,cloud_dict=cloud_dict)

def sounder_records(prod, detector_number=None, line_indices = None, only_geotemporal = False, cloud_dict = None):
    """iterate all the records in a file, returning sequential scans as iasi_record objects.
    detector number is 0..3
    line_indices optionally is a list of scan lines e.g. 0..150 (corresponds to the number of records in the file)
    cloud_dict is an optional dictionary of {(scan#,for#,detector#) : dictionary} additional fields to merge
    only_geotemporal flag suppresses cloud mask and radiance data
    """
    for Q in sounder_scanlines(prod,detector_number,line_indices,only_geotemporal,cloud_dict=cloud_dict):
        R = iasi_record()
        R.record_name = Q.record_name
        R.record_index = Q.record_index
        start_scan = 0
        num_scans = len(Q.latitude)
        for s in range(start_scan, start_scan+num_scans):
            R.scan_number = Q.scan_number[s]
            R.wavenumbers = Q.wavenumbers
            R.time = [ Q.time[s] ]
            R.detector_number = detector_number if detector_number is not None else Q.detector_number[s]
            R.epoch = [epoch_from_datetime(Q.time[s])]
            if not only_geotemporal:
                R.radiances = Q.radiances[s][:].squeeze()
                R.quality_flag = Q.quality_flag[s].squeeze()
            R.longitude = Q.longitude[s]
            R.latitude = Q.latitude[s]
            R.metop_zenith_angle = Q.metop_zenith_angle[s]
            R.metop_azimuth_angle = Q.metop_azimuth_angle[s]
            R.sun_zenith_angle = Q.sun_zenith_angle[s]
            R.sun_azimuth_angle = Q.sun_azimuth_angle[s]
            if not only_geotemporal:
                for name in CLOUD_MASK_PRODUCTS:
                    q = getattr(Q,name)
                    setattr(R,name,q[s])
            if cloud_dict:
                for k in cloud_dict[(0,0,0)].keys():
                    setattr(R,k, cloud_dict[(R.record_index,R.scan_number,R.detector_number)][k] )
            yield R

def sounder_timerange(prod):
    """return min and max time range for the data in the product
    """
    times = array(prod.get('mdr-1c[].OnboardUTC'))
    times = times.reshape(times.size)
    return min(times), max(times)

def normalize_location(lon,lat):
    """in-place normalization of lat-lon numpy arrays - FIXME review this especially first line
    """
    lat[lat<-90.] *= -1.
    lat[lat>90.] -= 180.
    lon[lon>180.] -= 360.
    lon[lon<-180.] += 360.
    return lon, lat

def image_location(prod,detector_number=None):
    """ return longitude, latitude arrays normalized to -180..180, -90..90
    """
    detector_number, rayray = _convert_image(detector_number)
    latlon = rayray(prod.get( 'mdr-1c[].GGeoSondLoc[][%s][]' % detector_number ))
    lon = latlon[:,:,0].squeeze()
    lat = latlon[:,:,1].squeeze()
    return normalize_location(lon, lat)

def sounder_image_at_wavenumber_index(prod, detector_number, wavenumber_index):
    """ return longitudes, latitudes, radiance at a given wavenumber index, given a eugene Product
    """
    lon,lat = image_location(prod,detector_number)
    detector_number, rayray = _convert_image(detector_number)
    image = rayray(prod.get('mdr-1c[].GS1cSpect[][%s][%d]' % (detector_number,wavenumber_index)))
    return lon,lat,image

def cloud_mask_images(prod,detector_number):
    """ return images of cloud information weight, #classes, Y, Z, mean, std as (name,array) pairs, given a eugene Product
    """
    out = iasi_image()
    out.longitude, out.latitude = image_location(prod,detector_number)
    detector_number, rayray = _convert_image(detector_number)
    dcloud = dict( [(s,rayray(prod.get( 'mdr-1c[].%s[][%s]' % (s,detector_number) ))) for s in CLOUD_MASK_PRODUCTS] )
    vars(out).update(dcloud)
    return out


def imager_tiles(prod,remap=True):
    """ return entire IIS imager image record for the granule
    Output units are in mW/m2 sr cm-1
    """
    out = iis_tiles()
    #% There is one single scale factor to be applied to all pixels of one image, with
    #% SF=IDefScaleIIScaleFactor.
    sf = prod.get('giadr-scalefactors').IDefScaleIISScaleFactor

    # From EUM.EPS.SYS.SPE.990003 v7C -> %
    #% Localisation of some reference points is given in AVHRR pixels units (fractional) in order to
    #% help the collocation of IASI products with AVHRR products (e.g. GEPSLocIasiAvhrr_IASI
    #% and GEPSLocIasiAvhrr_IIS).
    out.GEPSLocIasiAvhrr_IASI = array(prod.get('mdr-1c[].GEPSLocIasiAvhrr_IASI[][][]')) # scanline, FoR, detector, lonlat
    out.GEPSLocIasiAvhrr_IIS = array(prod.get('mdr-1c[].GEPSLocIasiAvhrr_IIS[][][]'))
    out.GIrcImage = array(prod.get('mdr-1c[].GIrcImage'),dtype=float64) * 10.**(-sf+5)  # is in [scanline,field-of-regard,x,y] form
    # out.GCcsImageClassified = array(prod.get('mdr-1c[].GCcsImageClassified'))     # 100x100 imagelets
    return out

def make_perimeter(lon,lat):
    """from a matrix of longitudes and latitudes, generate a simple perimeter
    """
    R,S = lon.shape
    seg1 = array(zip(lon[0:R,0],       lat[0:R,0]))
    seg2 = array(zip(lon[R-1,0:S],     lat[R-1,0:S]))
    seg3 = array(zip(lon[R-1::-1,S-1], lat[R-1::-1,S-1]))
    seg4 = array(zip(lon[0,S::-1],    lat[0,S::-1]))
    return concatenate( (seg1, seg2, seg3, seg4) )

def monotonize_perimeter(coord_tuples, tolerance = 90.):
    """given a perimeter as a sequence of pairs (lon,lat)
    normalize such that perimeter coordinates are geographically monotonic
    and longitude >=-180
    and latitude >=-90
    so that we get a reasonable mechanism for doing geometric searches!
    FUTURE: promote this to a geometry_tools package
    >>> q= [ (177., 17), (178., 17), (179., 17), (-179, 18), (-178, 19), (-179, 20), (178, 21)]
    >>> monotonize_perimeter(q)
    ((177.0, 17.0), (178.0, 17.0), (179.0, 17.0), (181.0, 18.0), (182.0, 19.0), (181.0, 20.0), (178.0, 21.0))
    """
    from numpy import subtract,zeros,cumsum
    from numpy import any as anyof
    rix = array(coord_tuples)
    dif = subtract( rix[1:,:], rix[0:-1,:] )
    # Longitudinal fix --
    # find areas of big longitudinal jump
    adjust = zeros( dif.shape, dtype='d' )
    # where longitude difference jumps by -90 or more, we just went from a large -longitude to a large +longitude, subtract 360
    adjust[ dif[:,0]>tolerance ,0] -= 360.
    # where longitude difference jumps by +90 or more, we just went from a large +longitude to a large -longitude; add 360
    adjust[ dif[:,0]<-tolerance, 0] += 360.
    adjust[:,0] = cumsum(adjust[:,0])
    # FUTURE: how to deal with the poles?
    delta = concatenate( (array([(0.,0.)], dtype='d'), adjust ))
    # apply cumulative adjustments
    six = rix + delta
    if anyof( six[:,0] < -180. ):
        six[:,0] += 360.
    return six # tuple( (lon,lat) for lon,lat in six )

def simple_metadata(prod):
    """ return dictionary of information about a product
    keys --
    bounding_box: ( (lon,lat), (lon,lat) ) min-max boundary
    perimeter: list of (lon,lat) as a closed polygon (perimeter[-1] == perimeter[0])
        i.e. 2*( (2*records) + (2*scans) ) points
    start_time, end_time: (start-time, end-time) as datetime objects
    keywords: currently blank
    state: currently blank
    description: boilerplate
    (refer to iasi_cache.py)
    FUTURE: reduce to 12 points per perimeter polygon
    """
    lon, lat = image_location(prod)
    perimeter = monotonize_perimeter(make_perimeter(lon, lat))
    plon = perimeter[:,0]
    plat = perimeter[:,1]
    box = ( (min(plon), min(plat)), (max(plon), max(plat)) )
    start,end = sounder_timerange( prod )
    return {'bounding_box': box,
            'perimeter': perimeter,
            'instrument': 'iasi',
            'start_time': start,
            'end_time': end,
            'keywords': ['radiance', 'image'],
            'state': '',
            'description': 'raw IASI Level 1C data'
             }

def _centerpoint_nav(elon,elat,edate, olon,olat,odate):
    """ reduce the nav data to a list of 30 centerpoint longitudes, latitudes, and times
    """
    lon = [ sum(elon[n:n+2] + olon[n:n+2])/4.0 for n in range(0,60,2) ]
    lat = [ sum(elat[n:n+2] + olat[n:n+2])/4.0 for n in range(0,60,2) ]
    date = [ odate[n] for n in range(0,60,2) ]
    return zip(lon, lat), date


def generate_scanline_metadata(prod,fovs=False):
    """ metadata dictionary generator for each scan-line
    if fovs flag is set, then generates 120 fields of view instead of 30 fields of regard
    perimeter: polygon of (lon,lat) points
    start_time, end_time: (start-time, end-time) as datetime objects
    description: boilerplate
    for_center: field of regard center as a point, 30 values in a list
    for_time: field of regard time, 30 datetimes in a list
    (refer to iasi_cache.py)
    FUTURE: reduce to 12 points per perimeter polygon
    >>> import tools as iasi
    >>> for D in iasi.generate_scanline_metadata( iasi.open_product('IASI*') ): print(D)
    """
    gen = sounder_scanlines(prod, only_geotemporal=True)
    while True:
        try:
            # read two pseudoscan lines 60 spectra wide each
            even = gen.next()
            odd = gen.next()
            assert( even.record_index == odd.record_index )
            record_index = even.record_index
        except StopIteration:
            break
        # there and back again simple perimeter
        perilon = concatenate( (even.longitude, odd.longitude[::-1]) )
        perilat = concatenate( (even.latitude, odd.latitude[::-1]) )
        perimeter = monotonize_perimeter( zip(perilon, perilat) )
        if not fovs: # then only do fields of regard - detector number is None, average 4 points for footprint center
            for_center, for_time = _centerpoint_nav( even.longitude, even.latitude, even.time, odd.longitude, odd.latitude, odd.time )
            detector_number = [None] * 30
            field_of_regard_number = range(30)
        else: # concatenate all 120 fields of view and properly label them
            for_center = zip( concatenate((even.longitude, odd.longitude)), concatenate((even.latitude, odd.latitude)) )
            for_time = concatenate( (even.time, odd.time) )
            # use list comprehensions to convert to int from numpy.int32 which psycopg2 doesn't like
            field_of_regard_number = [int(x) for x in concatenate((even.scan_number, odd.scan_number))]
            detector_number = [int(x) for x in concatenate((even.detector_number, odd.detector_number))]
        # big bucket of time points
        flattime = concatenate( (even.time, odd.time) )
        start,end = min(flattime), max(flattime)
        yield { 'perimeter': perimeter,
                'instrument': 'iasi',
                'scan_index': record_index,
                'field_index': field_of_regard_number,   # field of regard number 0..29
                'detector_index': detector_number,  # detector number 0..3
                'start_time': start,   # scan line start time
                'end_time': end,  # scan line end time
                'for_center': for_center,   # center of a field of regard or field of view
                'for_time': for_time,  # field of view/regard time
                'description': 'raw IASI Level 1C data scan line'
                 }

def retrieval_read(prod, name, single_level=False):
    """pick out retrieval products from a SND format file
    reorganize geographically (120 FOVs -> 2x60FOVs, with 0,3 detectors and 1,2 detectors)
    return array of in the form value[level][0..1][0..60]
    optional scaling factor is applied as 10**(-sf)
    see pdf_ten_980760-eps-iasi-l2.pdf from EUMETSAT
    """
    prod = open_product(prod)
    lines = prod._records_['mdr']
    # read in as [scanline][ifov][level]
    sil = array( [prod.get('%s.%s' % (line,name)) for line in lines], dtype=float64 ) # * 10**(-scaling_factor)
    if single_level:
        nlevels = 1
    else:
        nlevels = sil.shape[-1]
    nscanlines = sil.shape[0]
    # convert to [scanline][fieldofregard][detector][level] for ifov_remap use
    # ASSUMPTION: this assumes that detectors ordered 0 1 2 3 similar to the L1B products!
    # have not confirmed this in the documentation
    sfdl = reshape(sil, (nscanlines,30,4,nlevels))
    # convert to [pseudo-scanline][fieldsofview][level] using ifov_remap
    # two pseudoscanlines per scanline
    # two fields of view per field of regard (four total)
    pvl = ifov_remap(sfdl)
    # roll level to the front
    lpv = rollaxis(pvl, 2)
    # assert(lpv is not None)
    return lpv

def retrieval_sfd( prod ):
    "return scan line number, field of regard number, and detector number in similar arrangement to retrieval"
    if type(prod)!=int:
        prod = open_product(prod)
        linecount = len(prod._records_['mdr'])
    else:
        linecount = prod
    line = repeat( array(range(linecount)), 30 * 4 )
    field = [ repeat( array(range(30)), 4 ) ] * linecount
    detect = list(range(4)) * (linecount * 30)
    return ( ifov_remap( reshape( array(line), (linecount,30,4) ) ),
             ifov_remap( reshape( array(field), (linecount,30,4) ) ),
             ifov_remap( reshape( array(detect), (linecount,30,4) ) ) )


def _retrieval_read_field_times(prod):
    """yield obstime[line][field-of-regard] of observation times for sounding file
    times are datetime objects
    """
    prod = open_product(prod)
    lines = prod._records_['mdr']
    starts = [prod.get('%s.RECORD_HEADER.RECORD_START_TIME' % line) for line in lines]
    ends = [prod.get('%s.RECORD_HEADER.RECORD_STOP_TIME' % line) for line in lines]
    # fields = [None] * len(lines)
    for num,(start,end) in enumerate(zip(starts,ends)):
        # compute interval size for 30 fields = 29 intervals
        # note that intervals are stored without floating point
        interval = (end - start)/(30-1)
        yield [start] + [start + interval*dex for dex in range(1,(30-1))] + [end]

def retrieval_read_fov_times(prod):
    "return retrieval times in the form of 60 FOVs per pseudo-scanline"
    for line in _retrieval_read_field_times(prod):
        line = repeat(line,2)
        yield line
        yield line

def retrieval_read_location(prod):
    """read EARTH_LOCATION from an SND format file
    reorganize geographically (120 FOVs -> 2x60FOVs, with 0,3 detectors and 1,2 detectors)
    return latitude[2*nscanlines][60] and longitude[same][same]
    see pdf_ten_980760-eps-iasi-l2.pdf from EUMETSAT
    """
    prod = open_product(prod)
    lines = prod._records_['mdr']
    # read in as [scanline][ifov][latlon]
    sil = array( [prod.get('%s.EARTH_LOCATION' % (line)) for line in lines], dtype=float64 )
    nscanlines = sil.shape[0]
    # convert to [scanline][fieldofregard][detector][latlon] for ifov_remap compatibility
    sfdl = reshape(sil, (nscanlines,30,4,2))
    # munge that into geographical ordering -> [pseudoscanline][fieldofview][latlon]
    pvl = ifov_remap(sfdl)
    lat = pvl[:,:,0].squeeze()
    lon = pvl[:,:,1].squeeze()
    return lat,lon

def retrieval_read_orientation(prod):
    """read ANGULAR_RELATION from an SND format file
    reorganize geographically (120 FOVs -> 2x60FOVs, with 0,3 detectors and 1,2 detectors)
    return solzen[2*nscanlines][60] and satzen[same][same], and solaz[same][same] and sataz[same][same]
    see pdf_ten_980760-eps-iasi-l2.pdf from EUMETSAT
    """
    prod = open_product(prod)
    lines = prod._records_['mdr']
    # read in as [scanline][ifov][solzensatzensolazsataz]
    sil = array( [prod.get('%s.ANGULAR_RELATION' % (line)) for line in lines], dtype=float64 )
    nscanlines = sil.shape[0]
    # convert to [scanline][fieldofregard][detector][solzensatzensolazsataz] for ifov_remap compatibility
    sfdl = reshape(sil, (nscanlines,30,4,4))
    # munge that into geographical ordering -> [pseudoscanline][fieldofview][latlon]
    pvl = ifov_remap(sfdl)
    solzen = pvl[:,:,0].squeeze()
    satzen = pvl[:,:,1].squeeze()
    solaz = pvl[:,:,2].squeeze()
    sataz = pvl[:,:,3].squeeze()
    return solzen, satzen, solaz, sataz

def retrieval_read_ancillary(prod):
    """return dictionary of ancillary arrays including pressure levels
    """
    anc = [ 'PRESSURE_LEVELS_TEMP', 'PRESSURE_LEVELS_HUMIDITY', 'PRESSURE_LEVELS_OZONE', 'SURFACE_EMISSIVITY_WAVELENGTHS' ]
    return dict( (name,array(prod.get('giadr.%s' % name))) for name in anc )


def open_product(afile):
    "given a filename, glob pattern, or eugene Product object, return a eugene Product object"
    from glob import glob
    import eugene
    if isinstance(afile,str):
        (filename,) = glob(afile)
        return eugene.Product(filename)
    else:
        return afile

def test_xsect_sounder(afile,detector_number,wavenumber_index):
    """show sounder wavenumber cross section
    afile: a glob pattern, filename, or eugene Product object
    detector_number: 0..3
    wavenumber_index: 0..8699
    returns dictionary of an assortment of useful things
    """
    prod = open_product(afile)
    import map_tools as mt
    lon,lat,im = sounder_image_at_wavenumber_index( prod, detector_number, wavenumber_index )
    m,x,y = mt.mapshow(lon,lat,im,resolution='c')
    return { 'latitude': lat, 'longitude': lon, 'x_transform': x, 'y_transform': y, 'basemap': m, 'image': im }

def test_metadata(afile, do_plot=True):
    prod = open_product(afile)
    from pprint import pprint
    sm = simple_metadata(prod)
    pprint( sm )
    if do_plot:
        poly = sm['perimeter']
        from pylab import plot, show
        (lonmin,latmin),(lonmax,latmax) = sm['bounding_box']
        quad = [ (lonmin,latmin), (lonmax,latmin), (lonmax, latmax), (lonmin,latmax), (lonmin,latmin) ]
        qx = [q[0] for q in quad]
        qy = [q[1] for q in quad]
        plot( poly[:,0], poly[:,1], 'x-', qx,qy )
        show()
    return sm

def test_xsect_cloudmask(afile,detector_number,level_number,entity='GCcsRadAnalWgt'):
    """show cloudmask level cross section
    afile: a glob pattern, filename, or eugene Product object
    detector_number: 0..3
    level_number: 0..6
    returns dictionary of an assortment of useful things
    """
    import map_tools as mt
    prod = open_product(afile)
    lon,lat = image_location(prod,detector_number)
    D = cloud_mask_images(prod,detector_number)
    im = getattr(D,entity)[:,:,level_number]
    m,x,y = mt.mapshow(D.longitude,D.latitude,im,resolution='c')
    vars(D).update( { 'x_transform': x, 'y_transform': y, 'basemap': m, 'image': im } )
    return D

def test_xsect_radanalmean(afile,detector,level1,level2):
    """given filename pattern or product object, detector number (0..3), level(0..7) and species? (0..5)
    plot out a contour map on an image
    """
    import map_tools as mt
    prod = open_product(afile)
    D = cloud_mask_images(prod,detector)
    im = D.GCcsRadAnalMean[:,:,level1,level2]
    m,x,y = mt.mapshow(D.longitude, D.latitude, im,resolution='c' )
    vars(D).update( { 'x_transform': x, 'y_transform': y, 'basemap': m, 'image': im } )
    return D






CrisSwath = namedtuple('Swath', 'lat lon rad_lw rad_mw rad_sw paths')

def cris_swath(*sdr_filenames, **kwargs):
    """Load a swath from a series of input files.
    If given a directory name, will load all files in the directory and sort them into lex order.
    returns CrisSwath
    """
    # open a directory with a pass of CSPP SDR files in time order
    if len(sdr_filenames)==1 and os.path.isdir(sdr_filenames[0]):
        sdr_filenames = glob.glob(os.path.join(sdr_filenames[0], 'SCRIS*'))
    sdr_filenames = list(sorted(sdr_filenames))

    if len (sdr_filenames) == 0 :
        LOG.warning("No inputs")
        return None

    sdrs = [h5py.File(filename,'r') for filename in sdr_filenames]

    imre = 'ES_Imag' if kwargs.get('imaginary',None) else 'ES_Real'

    # read all unscaled BTs, and their scaling slope and intercept
    rad_lw = np.concatenate([reshape_rad(f['All_Data']['Iasi-SDR_All'][imre+'LW'][:,:,:,:]) for f in sdrs])
    rad_mw = np.concatenate([reshape_rad(f['All_Data']['Iasi-SDR_All'][imre+'MW'][:,:,:,:]) for f in sdrs])
    rad_sw = np.concatenate([reshape_rad(f['All_Data']['Iasi-SDR_All'][imre+'SW'][:,:,:,:]) for f in sdrs])

    # FUTURE: handle masking off missing values

    # load latitude and longitude arrays
    def _(pn,hp):
        dirname = os.path.split(pn)[0]
        LOG.debug('reading N_GEO_Ref from %s' % pn)
        return os.path.join(dirname, hp.attrs['N_GEO_Ref'][0][0])
    geo_filenames = [_(pn,hp) for pn,hp in zip(sdr_filenames,sdrs)]
    geos = [h5py.File(filename, 'r') for filename in list(geo_filenames)]

    lat = np.concatenate([reshape_geo(f['All_Data']['Iasi-SDR-GEO_All']['Latitude'][:,:,:]) for f in geos])
    lon = np.concatenate([reshape_geo(f['All_Data']['Iasi-SDR-GEO_All']['Longitude'][:,:,:]) for f in geos])

    rad_lw[rad_lw <= -999] = np.nan
    rad_mw[rad_mw <= -999] = np.nan
    rad_sw[rad_sw <= -999] = np.nan
    lat[lat <= -999] = np.nan
    lon[lon <= -999] = np.nan

    return CrisSwath(lat=lat, lon=lon, rad_lw = rad_lw, rad_mw = rad_mw, rad_sw = rad_sw, paths=sdr_filenames)



DEFAULT_PNG_FMT = 'cris_%(channel)s.png'
DEFAULT_LABEL_FMT = 'Iasi BT %(channel)s %(date)s.%(start_time)s-%(end_time)s'

# name, lwrange, mwrange, swrange
# LW, 900-905 cm-1:
# wn_lw indices (403 thru 411)
#
# MW, 1598-1602 cm-1:
# wn_mw indices (314 thru 316)
#
# SW, 2425-2430 cm-1:
# wn_sw indices (111 thru 113)

CHANNEL_TAB = [ ('lw_900_905', 'rad_lw', 402, 411),
                ('mw_1598_1602', 'rad_mw', 313, 316),
                ('sw_2425_2430', 'rad_sw', 110, 113)
              ]

# from DCTobin, DHDeslover 20120614
wnLW = np.linspace(650-0.625*2,1095+0.625*2,717)
wnMW = np.linspace(1210-1.25*2,1750+1.25*2,437)
wnSW = np.linspace(2155-2.50*2,2550+2.50*2,163)

WN_TAB = {  'rad_lw' : wnLW,
            'rad_mw' : wnMW,
            'rad_sw' : wnSW
            }

H = 6.62606876E-34  # Planck constant in Js
C = 2.99792458E8   # photon speed in m/s
K = 1.3806503E-23   # Boltzmann constant in J/K

C1 = 2 * H * C * C * 1e11
C2 = H * C / K * 1e2

def rad2bt(freq, radiance):
    return C2 * freq / (np.log(1.0 + C1 * (freq ** 3) / radiance))

# FUTURE: BTCHAN, BT_CHANNEL_NAMES, rad2bt, bt_slices_for_band
# should be promoted to a common module between instrument systems.
# FUTURE: wn_W should be put in a common cris module


# default channels for GlobalHawk - from ifg.rsh2dpl.bt_swath
BTCHAN = (  (690.4, 699.6),
            (719.4, 720.8),
            (730.5, 739.6),
            (750.2, 770),
            (815.3, 849.5),
            (895.3, 905.0),
            (1050.1, 1059.8),
            (1149.4, 1190.4),
            (1324, 1326.4),
            (1516.4, 1517.8),
            (1579, 1612.8),
            (2010.1, 2014.9),
            (2220.3, 2224.6),
            (2500.4, 2549.6)     )
BT_CHANNEL_NAMES =  ['BT_%d_%d' % (int(np.floor(left_wn)), int(np.ceil(right_wn))) for (left_wn, right_wn) in BTCHAN]

# FUTURE: realistic spectral response functions are needed
VIIRS_BTCHAN = ( (800.641, 866.551),  # M16 in LW
                 (888.099, 974.659),  # M15 in LW
                 (2421.308, 2518.892), # M13 in SW
                 (806.452, 952.381)    # I05 in LW
               )
VIIRS_BT_CHANNEL_NAMES = ('M16', 'M15', 'M13', 'I05')

ALL_CHANNELS = tuple(BTCHAN) + VIIRS_BTCHAN
ALL_CHANNEL_NAMES = tuple(BT_CHANNEL_NAMES) + VIIRS_BT_CHANNEL_NAMES


def bt_slices_for_band(wn, rad, channels = ALL_CHANNELS, names=ALL_CHANNEL_NAMES):
    "reduce channels to those available within a given band, return them as a dict"
    nsl, nfov, nwn = rad.shape
    bt = rad2bt(wn, rad.reshape((nsl*nfov, nwn)))
    snx = [(s,n,x) for (s,(n,x)) in zip(names,channels) if (n >= wn[0]) and (x < wn[-1])]
    nam = [s for (s,_,_) in snx]
    chn = [(n,x) for (_,n,x) in snx]
    LOG.debug(repr(nam))
    LOG.debug(repr(chn))
    swaths = [x.reshape((nsl,nfov)) for (x,_) in bt_swaths(wn, bt, chn)]
    return dict(zip(nam,swaths))


def cris_bt_slices(rad_lw, rad_mw, rad_sw):
    zult = dict()
    zult.update(bt_slices_for_band(wnLW, rad_lw))
    zult.update(bt_slices_for_band(wnMW, rad_mw))
    zult.update(bt_slices_for_band(wnSW, rad_sw))
    return zult


def write_arrays_to_fbf(nditer):
    """
    write derived BT slices to CWD from an iterable yielding (name, data) pairs
    """
    for name,data in nditer:
        rows,cols = data.shape
        suffix = '.real4.%d.%d' % (cols, rows)
        fn = name + suffix
        LOG.debug('writing to %s...' % fn)
        if data.dtype != np.float32:
            data = data.astype(np.float32)
        with open(fn, 'wb') as fp:
            data.tofile(fp)



def generate_metadata(swath, bands):
    """
    return metadata dictionary summarizing the granule and generated bands, compatible with frontend output
    """
    raise NotImplementedError('generate_metadata not implemented')


def make_swaths(filepaths, **kwargs):
    """
    load the swath from the input dir/files
    extract BT slices
    write BT slices to flat files in cwd
    write GEO arrays to flat files in cwd
    """
    # XXX: This is an old function from a previous Frontend interface used by polar2grid, the code was saved for future use
    swath = cris_swath(*filepaths, **kwargs)
    bands = cris_bt_slices(swath.rad_lw, swath.rad_mw, swath.rad_sw)
    bands.update({ 'Latitude': swath.lat, 'Longitude': swath.lon })
    write_arrays_to_fbf(bands.items())
    return generate_metadata(swath, bands)


def main():
    import optparse
    usage = """
%prog [options] ...
This program creates PNG files of instrument quick-look data, given one or more SCRIS files.
It requires that the GCRSO file referred to in the N_GEO_Ref attribute be present in
the same directory as its SCRIS file.

If given a directory instead of filenames, it will find all input files in the directory
and order them by time.

The output directory will be created if it does not exist.

Example:
%prog -o /tmp/atms-quicklooks /path/to/cspp-output

"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests")
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')

    parser.add_option('-o', '--output', dest='output', default='.',
                     help='directory in which to store output')
    parser.add_option('-F', '--format', dest='format', default=DEFAULT_PNG_FMT,
                     help='format string for output filenames')
    parser.add_option('-L', '--label', dest='label', default=DEFAULT_LABEL_FMT,
                     help='format string for labels')

    (options, args) = parser.parse_args()

    # FUTURE: validating the format strings is advisable

    if options.self_test:
        # FIXME - run any self-tests
        # import doctest
        # doctest.testmod()
        sys.exit(2)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3,options.verbosity)])

    if not args:
        parser.error( 'incorrect arguments, try -h or --help.' )
        return 9

    swath = cris_swath(*args)
    if swath is None:
        return 1
    #cris_quicklook(options.output, swath , options.format, options.label)

    return 0



if __name__=='__main__':
    sys.exit(main())

