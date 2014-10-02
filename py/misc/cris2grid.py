#!/usr/bin/env python# -*- coding: utf-8 -*-
"""
cris2grid
~~~~~~~~~~~~~~


Read swaths for CrIS data, including geolocation.
Write out swath flat binary files for channel-like slices.
Imitate VIIRS M13, M15, M16, I05. Eventually use a spectral response function to do so.
Eventually this will be used as a front end or wrapper to Polar2Grid


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""


__author__ = 'R.K.Garcia <rayg@ssec.wisc.edu>'
__revision__ = '$Id:$'
__docformat__ = 'reStructuredText'




import os, sys
import logging, unittest
import numpy as np

# import polar2grid.core.constants as pcc
from ql_cris_sdr import cris_swath, wnLW, wnMW, wnSW   # from CSPP
from .swath import *
#from ifg.rsh2dpl.bt_swath import BTCHAN, BT_CHANNEL_NAMES, bt_swaths   # from SHIS
from ifg.core.rad2bt import rad2bt # from SHIS


# FUTURE: realistic spectral response functions are needed
VIIRS_BTCHAN = ( (800.641, 866.551),  # M16 in LW
                 (888.099, 974.659),  # M15 in LW
                 (2421.308, 2518.892), # M13 in SW
                 (806.452, 952.381)    # I05 in LW
               )

VIIRS_BT_CHANNEL_NAMES = ('cris_M16', 'cris_M15', 'cris_M13', 'cris_I05')



# from poster_cris_sdr
def cris_bt_swaths_for_band(wn, rad, channels = tuple(BTCHAN) + VIIRS_BTCHAN, names=tuple(BT_CHANNEL_NAMES) + VIIRS_BT_CHANNEL_NAMES):
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


def cris_bt_swaths(rad_lw, rad_mw, rad_sw):
    zult = dict()
    zult.update(cris_bt_swaths_for_band(wnLW, rad_lw))
    zult.update(cris_bt_swaths_for_band(wnMW, rad_mw))
    zult.update(cris_bt_swaths_for_band(wnSW, rad_sw))
    return zult



LOG = logging.getLogger(__name__)

# DTYPES = {np.float32: 'real4'}

def fbf_filename(base, shape, dtype=np.float32):
    dims = '.'.join(str(d) for d in reversed(shape))
    return '%s.%s.%s' % (base, 'real4', dims)

def write_fbf(base, data):
    """
    write .real4 file with rows and columns from a
    """
    assert(2==len(data.shape))
    if data.dtype != np.float32:
        LOG.info('converting %s data to float32' % base)
        data = data.astype(np.float32)
    filename = fbf_filename(base, data.shape, data.dtype)
    LOG.debug('writing %s' % filename)
    with file(filename, 'wb') as fp:
        data.tofile(fp)
    return filename


# KIND2DKIND = {  'bt': pcc.DKIND_BTEMP,
#                 'rad': pcc.DKIND_RADIANCE,
#                 'refl': pcc.DKIND_REFLECTANCE}

# def _info(name, kind, data, filename):
#     """
#     return key, value pair for bands dictionary in swath metadata
#     """
#     return (None, None) # FIXME


def swath_to_fbf(swath):
    """
    write flat binary files of BT swaths and lat/lon to CWD
    """
    lat_filename = write_fbf('cris_lat', swath.lat)
    lon_filename = write_fbf('cris_lon', swath.lon)
    LOG.info('computing BT slices')
    btdict = cris_bt_swaths(swath.rad_lw, swath.rad_mw, swath.rad_sw)
    for name,data in btdict.items():
        write_fbf(name, data.squeeze())






# def create_swath_files(lat, lon, start_time, **swaths):
#     """
#     export CrIS swath as a flat binary workspace compatible with P2G
#     return dictionary of metadata as desribed in http://www.ssec.wisc.edu/software/polar2grid/dev/dev_guide.html#data-frontends
#     swaths is a mapping of name -> (kind, swath-array)
#     kind is "bt", "rad", "refl"
#     swath-array is a 2D array matching dimensions of lat and lon
#     name is an identifier
#     """
#     lat_filename = write_fbf('cris_lat', lat)
#     lon_filename = write_fbf('cris_lon', lon)
#     swath_rows, swath_cols = lat.shape
#     bands = dict( _info(name, kind, data, write_fbf(name, data)) for (name, (kind, data)) in swaths.items())
#     return dict(
#             sat = pcc.SAT_NPP,
#             instrument = 'cris', # pcc.INST_CRIS, FIXME
#             start_time = start_time,
#             fbf_lat = lat_filename,
#             fbf_lon = lon_filename,
#             #lat_min =
#             #lon_min =
#             #lat_max =
#             #lon_max =
#             swath_rows = swath_rows,
#             swath_cols = swath_cols,
#             swath_scans = swath_rows / 3,  # 3x3 detector
#             rows_per_scan = 3,
#             bands = bands
#         )






def main():
    import optparse
    usage = """
%prog [options] ...


"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests")
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    # parser.add_option('-o', '--output', dest='output',
    #                 help='location to store output')
    # parser.add_option('-I', '--include-path', dest="includes",
    #                 action="append", help="include path")
    (options, args) = parser.parse_args()


    # make options a globally accessible structure, e.g. OPTS.
    global OPTS
    OPTS = options


    if options.self_test:
        unittest.main()
        return 0


    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3,options.verbosity)])


    if not args:
        parser.error( 'incorrect arguments, try -h or --help.' )
        return 1


    LOG.info('reading in swath')
    swath = cris_swath(*args)
    swath_to_fbf(swath)


    return 0




if __name__=='__main__':
    sys.exit(main())
