#!/usr/bin/env python
# encoding: utf-8
"""
$Id: ql_cris_sdr.py 974 2012-09-17 19:52:16Z scottm $

based on ql_cris_sdr.py r974 2012-09-17

Purpose: Extract CrIS Swath data

Created by R.K.Garcia & G.D.Martin , July 2012.
Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
"""

import h5py, numpy as np, glob, os, sys, logging
from collections import namedtuple

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

def _rad2bt(freq, radiance):
    return c2 * freq / (np.log(1 + c1 * (freq ** 3) / radiance))


#def cris_quicklook(output_dir, swath,
#            png_fmt=DEFAULT_PNG_FMT,
#            label_fmt = DEFAULT_LABEL_FMT,
#            channels = None,
#            dpi=150, as_radiance=False, **kwargs):
#
#
#    nfo = info(*swath.paths)
#
#
#    if not os.path.isdir(output_dir):
#        os.makedirs(output_dir)
#
#    if channels:
#        groups = [x for x in CHANNEL_TAB if x[0] in channels]
#    else:
#        groups = CHANNEL_TAB
#
#    for channel, varname, start, end in groups:
#        eva = evaluator(channel=channel, **nfo)
#        filename = os.path.join(output_dir, png_fmt % eva)
#        raw = getattr(swath,varname)
#        rad = raw[:,:,start:end]
#        if as_radiance:
#            data = np.mean(rad, axis=2)
#        else:
#            wn = WN_TAB[varname][start:end]
#            bt = _rad2bt(wn, rad)
#            data = np.mean(bt, axis=2)
#
#        fig, bmap = map_contours(filename, data.squeeze(), swath.lon, swath.lat,
#                                 label = label_fmt % eva, dpi=dpi)
#        plt.colorbar()
#        print "writing %s" % filename
#        plt.savefig(filename, dpi=dpi)
#


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
    cris_quicklook(options.output, swath , options.format, options.label)

    return 0



if __name__=='__main__':
    sys.exit(main())

