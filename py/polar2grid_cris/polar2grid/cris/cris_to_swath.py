#!/usr/bin/env python
# encoding: utf-8
"""
CrIS SDR front end for polar2grid, which extracts band-pass slices of brightness temperature data.

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

import h5py, numpy as np, glob, os, sys, logging
from collections import namedtuple

from polar2grid.core.roles import FrontendRole
from polar2grid.core.constants import SAT_NPP, BKIND_IR, BKIND_I, BKIND_M, BID_13, BID_15, BID_16, BID_5, STATUS_SUCCESS, STATUS_FRONTEND_FAIL

LOG = logging.getLogger(__name__)


# reshape 4d array of rad into a 3d array by unpacking the FOV dimension (9 detectors)
def reshape_rad(rad_4d):
    shape_4d = rad_4d.shape
    shape_3d = (shape_4d[0] * 3, shape_4d[1] * 3, shape_4d[3])  # same size
    rad_3d = np.zeros(shape=shape_3d, dtype=rad_4d.dtype)

    for j in range(0, shape_4d[0]):  # 0:4
        for i in range(0, shape_4d[1]):  # 0:30
            rad_3d[ j*3:j*3+3, i*3:i*3+3, : ] = rad_4d[j,i,:,:].reshape((3,3,shape_4d[3]))

    return rad_3d

def reshape_geo(geo_3d):
    shape_3d = geo_3d.shape
    shape_2d = (shape_3d[0] * 3, shape_3d[1] * 3)  # same size
    geo_2d = np.zeros(shape=shape_2d, dtype=geo_3d.dtype)

    for j in range(0, shape_3d[0]):  # 0:4
        for i in range(0, shape_3d[1]):  # 0:30
            geo_2d[ j*3:j*3+3, i*3:i*3+3] = geo_3d[j,i,:].reshape((3,3))

    return geo_2d

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
        LOG.warn( "No inputs")
        return None

    sdrs = [h5py.File(filename,'r') for filename in sdr_filenames]

    imre = 'ES_Imag' if kwargs.get('imaginary',None) else 'ES_Real'

    # read all unscaled BTs, and their scaling slope and intercept
    rad_lw = np.concatenate([reshape_rad(f['All_Data']['CrIS-SDR_All'][imre+'LW'][:,:,:,:]) for f in sdrs])
    rad_mw = np.concatenate([reshape_rad(f['All_Data']['CrIS-SDR_All'][imre+'MW'][:,:,:,:]) for f in sdrs])
    rad_sw = np.concatenate([reshape_rad(f['All_Data']['CrIS-SDR_All'][imre+'SW'][:,:,:,:]) for f in sdrs])

    # FUTURE: handle masking off missing values

    # load latitude and longitude arrays
    def _(pn,hp):
        dirname = os.path.split(pn)[0]
        LOG.debug('reading N_GEO_Ref from %s' % pn)
        return os.path.join(dirname, hp.attrs['N_GEO_Ref'][0][0])
    geo_filenames = [_(pn,hp) for pn,hp in zip(sdr_filenames,sdrs)]
    geos = [h5py.File(filename, 'r') for filename in list(geo_filenames)]

    lat = np.concatenate([reshape_geo(f['All_Data']['CrIS-SDR-GEO_All']['Latitude'][:,:,:]) for f in geos])
    lon = np.concatenate([reshape_geo(f['All_Data']['CrIS-SDR-GEO_All']['Longitude'][:,:,:]) for f in geos])

    rad_lw[rad_lw <= -999] = np.nan
    rad_mw[rad_mw <= -999] = np.nan
    rad_sw[rad_sw <= -999] = np.nan
    lat[lat <= -999] = np.nan
    lon[lon <= -999] = np.nan

    return CrisSwath(lat=lat, lon=lon, rad_lw = rad_lw, rad_mw = rad_mw, rad_sw = rad_sw, paths=sdr_filenames)



DEFAULT_PNG_FMT = 'cris_%(channel)s.png'
DEFAULT_LABEL_FMT = 'CrIS BT %(channel)s %(date)s.%(start_time)s-%(end_time)s'

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
wnLW = np.linspace(650-0.625*2,1095+0.625*2,717);
wnMW = np.linspace(1210-1.25*2,1750+1.25*2,437);
wnSW = np.linspace(2155-2.50*2,2550+2.50*2,163);

WN_TAB = {  'rad_lw' : wnLW,
            'rad_mw' : wnMW,
            'rad_sw' : wnSW
            }

h = 6.62606876E-34  # Planck constant in Js
c = 2.99792458E8   # photon speed in m/s
k = 1.3806503E-23   # Boltzmann constant in J/K

c1 = 2*h*c*c*1e11
c2 = h*c/k*1e2

def rad2bt(freq, radiance):
    return c2 * freq / (np.log(1.0 + c1 * (freq ** 3) / radiance))

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


# from poster_cris_sdr
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


def write_slices_to_fbf(info):
    raise NotImplementedError('write_slices_to_fbf not implemented')


# FUTURE: add a way to configure which slices to produce, or all by default
class CrisSdrFrontend(FrontendRole):
    """
    """
    info = None

    def __init__(self, **kwargs):
        self.info = {}

    @abstractmethod
    def make_swaths(self, filepaths, **kwargs):
        swath = cris_swath(*filepaths, **kwargs)
        bands = cris_bt_slices(swath.rad_lw, swath.rad_mw, swath.rad_sw)
        self.info = write_swath_to_fbf(bands)
        return self.info



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

    # make options a globally accessible structure, e.g. OPTS.
    global OPTS
    OPTS = options

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


    swath =  cris_swath(*args)
    if swath == None :
        return 1
    #cris_quicklook(options.output, swath , options.format, options.label)

    return 0



if __name__=='__main__':
    sys.exit(main())

