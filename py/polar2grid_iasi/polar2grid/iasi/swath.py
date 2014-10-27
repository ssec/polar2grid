#!/usr/bin/env python
# encoding: utf-8
"""


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
from collections import namedtuple, defaultdict
import calendar, re
from datetime import datetime
from collections import defaultdict
from pprint import pformat
from numpy import exp,log,array,arange,empty,float32,float64,sin,linspace,concatenate,repeat,reshape,rollaxis

from polar2grid.core.roles import FrontendRoleOld
# from polar2grid.core.constants import SAT_NPP, BKIND_IR, BKIND_I, BKIND_M, BID_13, BID_15, BID_16, BID_5, STATUS_SUCCESS, STATUS_FRONTEND_FAIL
import polar2grid.iasi.tools as iasi

LOG = logging.getLogger(__name__)


# conversion functions to get numpy arrays from iasi record fields
def real4sfromarray(x): return np.array(x,np.float32)
def int4sfromarray(x): return np.array(x,np.int32)
def real8sfromarray(x): return np.array(x,np.float64)
def real4fromvalue(x): return np.array([x],np.float32)
def real4sfromdatetimes(L):
    return np.array([x.hour + x.minute/60. + x.second/3600. + x.microsecond/3.6e9 for x in L],np.float32)


# FUTURE: make this into a generic fbf_writer that takes the table as a constructor parameter; add to fbf toolbox
class fbf_writer(object):
    """A class capable of writing a series of records to a flat binary directory
    """

    _base = None # directory name which we're writing
    _ignore = [] # list/set of names which we don't want written
    _files = { } # currently open file objects
    _info = { }  # info on which fields go to which files

    def __init__(self,info,output_directory_name,comment='',ignore=[]):
        if not os.path.isdir(output_directory_name): os.makedirs(output_directory_name)
        self._info = info
        self._base = output_directory_name
        self._ignore = ignore
        self._files = { }
        self._create_metadata(comment)

    def _create_metadata(self,comment):
        """ write version / tracking / log metadata to the output directory
        """
        if comment:
            fp = file(os.path.join(self._base,'README.txt'),'wt')
            print >>fp, VCSID
            print >>fp, iasi.VCSID
            print >>fp, comment

    @staticmethod
    def endian(ext):
        "change the case of the extension string based on system endianness"
        return ext.lower() if sys.byteorder=='little' else ext.upper()

    def _create(self, stem, ext, data):
        "create a binary output file if it doesnt exist -- use array shape in filename if needed"
        if hasattr(data,'shape') and getattr(data,'size',1)>1:
            dimsum = ['.%d' % x for x in data.shape]
            dimsum.reverse()
            shape = ''.join(dimsum)
        else:
            shape = ''
        filename = os.path.join(self._base, stem + self.endian(ext) + shape)
        LOG.debug("creating %s..." % filename)
        return file(filename, 'wb')

    def _append(self,key,data):
        "append a record to the named output key, creating files as needed"
        stem, ext, cvt = self._info[key]
        if not stem: stem = key
        # see if we need to open the output file
        if key not in self._files:
            fp = self._create(stem, ext, data)
            self._files[key] = fp
        else:
            fp = self._files[key]
        # reformat the data as the intended type and write the next record
        reform = cvt(data)
        LOG.debug('writing a record of %s' % key)
        reform.tofile(fp)

    def write_image(self,stem,suffix,data):
        "write a record which contains, for instance, an entire image block"
        if stem not in self._files:
            fp = self._create(stem,suffix,data)
            self._files[stem] = fp
        data.tofile( fp )

    def write_ancillary(self,stem,suffix,data):
        "write a single record to a file the first time the file is encountered"
        if stem not in self._files:
            fp = self._create(stem,suffix,data)
            self._files[stem] = fp
            data.tofile( fp )

    def __call__(self,record):
        for field_name in self._info.keys():
            if field_name not in self._ignore:
                self._append(field_name, getattr(record,field_name))


# example dictionary in cloud_dict
# (22,29,2):
# {'clear_percent': 0.0,
#  'cloudy_percent': 100.0,
#  'day_time': 0,
#  'detector_index': 2,
#  'field_index': 29,
#  'field_of_regard_time': 14216774,
#  'layer_count': 6.0,
#  'satellite_latitude': -69.090000000000003,
#  'satellite_longitude': -38.310000000000002,
#  'satellite_zenith_angle': 56.899999999999999,
#  'scan_line': 22,
#  'surface_pressure': 978.75999999999999,
#  'surface_temp': 258.38,
#  'surface_type': 0,
#  'twometer_temp': 258.23000000000002,
#  'when': datetime.datetime(2008, 6, 5, 3, 56, 56, 774000)},

class iasi_record_fbf_writer(fbf_writer):

    _detector_number = None # which detector we're writing out, if any (None implies all-detectors)

    # filename and data type table, noting that keys are common between the iasi_record and this table
    # we need the data types in order to use numpy to force the raw data into the right format
    IASI_FBF_FILENAMES = {  'radiances':    (None, '.real4', real4sfromarray), # by default None implies key is used as stem
                            'latitude':     (None, '.real4', real4fromvalue),
                            'longitude':    (None, '.real4', real4fromvalue),
                            'detector_number':    (None, '.real4', real4fromvalue),
                            'scan_number':    (None, '.real4', real4fromvalue),
                            'time':         (None, '.real4', real4sfromdatetimes),
                            'epoch':        (None, '.real8', real8sfromarray),
                            'metop_zenith_angle': (None, '.real4', real4sfromarray),
                            'metop_azimuth_angle': (None, '.real4', real4sfromarray),
                            'sun_zenith_angle': (None, '.real4', real4sfromarray),
                            'sun_azimuth_angle': (None, '.real4', real4sfromarray),
                            #'quality_flag_detailed': (None, '.int4', int4sfromarray),
                            'quality_flag': (None, '.int4', int4sfromarray),
                            }

    # data values only available when we merge in MAIA output dictionaries from secondary files
    CLOUD_FBF_FILENAMES = { 'clear_percent': (None, '.real4', real4sfromarray),
                            'cloudy_percent': (None, '.real4', real4sfromarray),
                            'day_time': (None, '.real4', real4sfromarray),
                            'surface_pressure': (None, '.real4', real4sfromarray),
                            'surface_temp': (None, '.real4', real4sfromarray),
                            'twometer_temp': (None, '.real4', real4sfromarray),
                            'surface_type': (None, '.real4', real4sfromarray)
                            }

    # data values added Nov 2009 by Hong Zhang
    # python -c "import re,sys; print '\n'.join(re.findall(r'self\.(\w+)', sys.stdin.read()))"
    # python -c "import re,sys; print '\n'.join(['\'%s\': (None, \'.real4\', real4sfromarray)'%s for s in re.findall(r'self\.(\w+)', sys.stdin.read())])" </tmp/foo
    PAR_MAIA_FBF_FILENAMES  = { 'cluster_ccsi_flag': (None, '.int4', int4sfromarray),
                                'cluster_surface_temp': (None, '.real4', real4sfromarray),
                                'cluster_skin_temp': (None, '.real4', real4sfromarray),
                                'cluster_cwv': (None, '.real4', real4sfromarray),
                                'cluster_surface_altitude': (None, '.real4', real4sfromarray),
                                'cluster_surface_type': (None, '.int4', int4sfromarray),
                                'cluster_cloud_type': (None, '.int4', int4sfromarray),
                                'cluster_blackbody_flag': (None, '.int4', int4sfromarray),
                                'cluster_blackbody_top_cloud_temp': (None, '.real4', real4sfromarray),
                                'cluster_specular_reflection': (None, '.real4', real4sfromarray),
                                'cluster_clear_cloudy_marine_flag': (None, '.int4', int4sfromarray),
                                'cluster_ts_background': (None, '.int4', int4sfromarray),
                                'cluster_wv_content': (None, '.int4', int4sfromarray),
                                'cluster_day_time': (None, '.int4', int4sfromarray),
                                'cluster_quality_flag': (None, '.int4', int4sfromarray)
                                }

    IASI_FBF_FILENAMES.update( dict( (s,(None,'.real4',real4sfromarray)) for s in iasi.CLOUD_MASK_PRODUCTS ) )

    def __init__(self,output_directory_name,detector_number,comment='',ignore=[],use_cloud=False,use_clusters=False):
        inventory = dict(self.IASI_FBF_FILENAMES)
        if use_cloud: inventory.update(self.CLOUD_FBF_FILENAMES)
        if use_clusters: inventory.update(self.PAR_MAIA_FBF_FILENAMES)
        fbf_writer.__init__(self,inventory,output_directory_name,comment,ignore)
        self._detector_number = detector_number

    def write_iis(self,iis):
        self.write_image('GIrcImage','.real4',real4sfromarray(iis.GIrcImage))

    def write_wavenumbers(self,wnums):
        self.write_ancillary('wavenumbers','.real8',wnums)




def cloud_mask_dict(cloud_list):
    "convert MAIA cloud mask list of dictionaries to a dictionary of dictionaries keyed from (scanline,fieldofregard,detector) tuples"
    keys = [(x['scan_line'], x['field_index'], x['detector_index']) for x in cloud_list]
    return dict( zip(keys,cloud_list) )

def cloud_mask_load(pathname):
    "return dictionary of cloud mask data for use in iasi_tools"
    if pathname.endswith('.txt'):
        from metahoard.iasi.cloud_extract import read_maia_file
        return cloud_mask_dict( vars(x) for x in read_maia_file(pathname) )
    else:
        from cPickle import load
        leest = load( file( pathname, 'rb' ) )
        return cloud_mask_dict(leest)

def _cloud_mask_has_clusters(cmdict):
    "return whether cloud mask includes cluster_* fields"
    for d in cmdict.values(): # FUTURE: is there a better way to do this?
        if 'par_maia' in d: return True
        return False

def extract_sounding(output_directory, detector_number=None, as_scan_lines=True, use_cloud=False, cloud_mask_pathname=None, lines=None, iis_images=False, ignore=[], *filenames):
    """ iterate through all the records for a given detector for a series of files, writing them to flat binary
    """
    LOG.info("creating %s..." % output_directory)
    rec_num = 0
    if detector_number is None:
        detector_info = "all detectors"
    else:
        detector_info = "detector %d" % detector_number
    comment = """Data extraction from %s for %s""" % (`filenames`, detector_info)
    write = None # delay creation until we have first file open

    for filename in filenames:

        filename = filename if not '*' in filename else glob.glob(filename)[0]
        LOG.info("processing %s..." % filename)

        cloud_dict = None
        has_clusters = False
        if use_cloud or cloud_mask_pathname:
            if not cloud_mask_pathname:
                dn,fn = os.path.split(filename)
                cn = os.path.join(dn,'mask_%s.pickle' % fn)
            else:
                cn = cloud_mask_pathname
                use_cloud = True
            LOG.debug("reading cloud data from %s" % cn)
            assert( os.path.exists(cn) )
            cloud_dict = cloud_mask_load(cn)
            has_clusters = _cloud_mask_has_clusters(cloud_dict) # check or extended information from par_maia

        if write is None:
            write = iasi_record_fbf_writer(output_directory, detector_number, comment, ignore=ignore, use_cloud=use_cloud, use_clusters=has_clusters)

        prod = iasi.open_product(filename)
        if not as_scan_lines:
            datagen = iasi.sounder_records(prod, detector_number, lines, cloud_dict = cloud_dict)
        else:
            datagen = iasi.sounder_scanlines(prod, detector_number, lines, cloud_dict = cloud_dict)
        if iis_images:
            tiles = iasi.imager_tiles(prod)
            LOG.debug("writing IIS tiles %s as one record" % str(tiles.GIrcImage.shape))
            write.write_iis(tiles)
        for record in datagen:
            LOG.debug(str(record))
            write( record )
            write.write_wavenumbers(record.wavenumbers) # only does it once
            rec_num += 1
            print 'wrote %5d records..   \r' % rec_num,
            sys.stdout.flush()
    print "\ndone!"




# EUGENE KEY: ( fbf-stem, fbf-type, conversion-function, scaling-factor, units, is-single-level )
FIELD_LIST={'ATMOSPHERIC_TEMPERATURE': ('T', '.real4', real4sfromarray, 2, 'K', False),
            'ATMOSPHERIC_WATER_VAPOUR': ('wv', '.real4', real4sfromarray, 6, 'kg/kg', False),
            'ATMOSPHERIC_OZONE': ('oz', '.real4', real4sfromarray, 7, 'kg m-2', False),
            'INTEGRATED_OZONE': ('integrated_oz', '.real4', real4sfromarray, 7, "kg m-2", True),
            'SURFACE_TEMPERATURE': ('surface_temp', '.real4', real4sfromarray, 2, "K", False),
            'INEGRATED_N2O': ('integrated_N2O', '.real4', real4sfromarray, 7, "kg m-2", True),
            'INTEGRATED_CO': ('integrated_CO', '.real4', real4sfromarray, 7, "kg m-2", True),
            'INTEGRATED_CH4': ('integrated_CH4', '.real4', real4sfromarray, 5, "kg m-2", True),
            'INTEGRATED_CO2': ('integrated_CO2', '.real4', real4sfromarray, 3, "kg m-2", True),
            'SURFACE_EMISSIVITY': ('surface_emiss', '.real4', real4sfromarray, 4, "ratio", False),
            'FRACTIONAL_CLOUD_COVER': ('cloud_cover_fraction', '.real4', real4sfromarray, 2, "%", False),
            'CLOUD_TOP_TEMPERATURE': ('cloud_top_temp', '.real4', real4sfromarray, 2, "K", False),
            'CLOUD_TOP_PRESSURE': ('cloud_top_press', '.real4', real4sfromarray, 0, "Pa", False),
            'CLOUD_PHASE': ('cloud_phase', '.real4', real4sfromarray, 0, "0:none 1:liquid 2:ice 3:mixed", False),
            'SURFACE_PRESSURE': ('surface_press', '.real4', real4sfromarray, 0, "Pa", True),
            'FLG_IASICLD': ('is_cloud', '.int4', int4sfromarray, 0, "boolean", True),
            'FLG_IASICLR': ('scene_type', '.int4', int4sfromarray, 0, "clear / partly cloudy / cloudy", True),
            'FLG_ITCONV': ('is_retrieval_converged', '.int4', int4sfromarray, 0, "boolean", True),
            'FLG_IASIBAD': ('is_bad_spectra', '.int4', int4sfromarray, 0, "boolean", True),
            'FLG_CLDSUM': ('instruments_seeing_clouds', '.int4', int4sfromarray, 0, "enumeration", True),
            'FLG_CLDFRM': ('cloud_formations_count', '.int4', int4sfromarray, 0, "count", True),
            }



class iasi_retrieval_fbf_writer(fbf_writer):
    # FUTURE: move this information to iasi_tools - especially units and scaling factors!

    def __init__(self, output_directory_name, comment='', ignore=[]):
        NFO = dict( (x,y[0:3]) for x,y in FIELD_LIST.items() )
        NFO['lat'] = ('latitude', '.real4', real4sfromarray)
        NFO['lon'] = ('longitude', '.real4', real4sfromarray)
        NFO['detector_number'] = ('detector_number', '.int4', int4sfromarray)
        NFO['line_number'] = ('line_number', '.int4', int4sfromarray)
        NFO['field_number']= ('field_number', '.int4', int4sfromarray)

        NFO['solzen'] = ('solar_zenith_angle', '.real4', real4sfromarray)
        NFO['solaz'] = ('solar_azimuth_angle', '.real4', real4sfromarray)
        NFO['satzen'] = ('satellite_zenith_angle', '.real4', real4sfromarray)
        NFO['sataz'] = ('satellite_azimuth_angle', '.real4', real4sfromarray)

        NFO['refTimeUsec'] = ('refTimeUsec', '.int4', int4sfromarray)
        NFO['refTimeSec'] = ('refTimeSec', '.int4', int4sfromarray)
        NFO['refTimeDay'] = ('refTimeDay', '.int4', int4sfromarray)
        NFO['refTimeMonth'] = ('refTimeMonth', '.int4', int4sfromarray)
        NFO['refTimeYear'] = ('refTimeYear', '.int4', int4sfromarray)

        fbf_writer.__init__(self,NFO,output_directory_name,comment,ignore)

    def write_levels(self,ancil):
        self.write_ancillary('T_pressure_levels','.real4',real4sfromarray(ancil['PRESSURE_LEVELS_TEMP']))
        self.write_ancillary('wv_pressure_levels','.real4',real4sfromarray(ancil['PRESSURE_LEVELS_HUMIDITY']))
        self.write_ancillary('oz_pressure_levels','.real4',real4sfromarray(ancil['PRESSURE_LEVELS_OZONE']))
        self.write_ancillary('surface_emiss_wavelengths','.real8',real8sfromarray(ancil['SURFACE_EMISSIVITY_WAVELENGTHS']))


def datetime_shatter( whens ):
    "split an array of datetime objects into component arrays of microseconds, second-of-day, day, month, year"
    whens = np.array(whens)
    shape = whens.shape
    count = whens.size

    def emptor(*junk): return np.empty( (count,), dtype=np.int32 )
    us,s,d,m,y = map( emptor, range(5) )

    for dex,when in enumerate( whens.flatten() ):
        us[dex] = when.microsecond
        s[dex] = when.second + when.minute*60 + when.hour*3600
        d[dex] = when.day
        m[dex] = when.month
        y[dex] = when.year

    return us.reshape(shape), s.reshape(shape), d.reshape(shape), m.reshape(shape), y.reshape(shape)

class retrieval_record(object):
    pass

def extract_retrieval(output_directory, ignore=[], *filenames):
    comment = """Data extraction from %s\nPressure levels are in Pa\n""" % (`filenames`)
    for (key,(stem,_,_,sf,units,_)) in FIELD_LIST.items():
        comment += '%s (%s): from %s\n' % (stem,units,key)
    write = iasi_retrieval_fbf_writer(output_directory, comment, ignore=ignore)
    for filename in filenames:
        LOG.info('processing %s...' % filename)
        prod = iasi.open_product(filename)
        ancil = iasi.retrieval_read_ancillary(prod)
        write.write_levels(ancil) # only writes for first file
        data = retrieval_record()
        for (key,(stem,_,_,sf,units,onelevel)) in FIELD_LIST.items():
            LOG.info("reading %s as %s..." % (key,stem))
            # read that field in for the whole file, noting that integrated quantities are single-level
            # note that INEGRATED_N2O is for real (dammit guys)
            # apply scaling factor
            field =  iasi.retrieval_read(prod, key, single_level=onelevel)
            setattr(data, key, field.squeeze())
        data.lat, data.lon = iasi.retrieval_read_location(prod)
        data.line_number, data.field_number, data.detector_number = iasi.retrieval_sfd(prod)
        data.solzen, data.satzen, data.solaz, data.sataz = iasi.retrieval_read_orientation(prod)
        data.refTimeUsec, data.refTimeSec, data.refTimeDay, data.refTimeMonth, data.refTimeYear = datetime_shatter(list(iasi.retrieval_read_fov_times(prod)))
        LOG.debug("writing record...")
        write(data)



#
#
# polar2grid frontend support
#
#


def generate_metadata(swath, bands):
    """
    return metadata dictionary summarizing the granule and generated bands, compatible with frontend output
    """
    raise NotImplementedError('generate_metadata not implemented')


# FUTURE: add a way to configure which slices to produce, or all by default
class IasiSdrFrontendOld(FrontendRoleOld):
    """
    """
    info = None

    def __init__(self, **kwargs):
        self.info = {}

    def make_swaths(self, filepaths, **kwargs):
        """
        load the swath from the input dir/files
        extract BT slices
        write BT slices to flat files in cwd
        write GEO arrays to flat files in cwd
        """
        swath = cris_swath(*filepaths, **kwargs)
        bands = cris_bt_slices(swath.rad_lw, swath.rad_mw, swath.rad_sw)
        bands.update({ 'Latitude': swath.lat, 'Longitude': swath.lon })
        write_arrays_to_fbf(latlon.items())
        write_arrays_to_fbf(bands.items())
        self.info = generate_metadata(swath, bands)
        return self.info



#
# default self-test main
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
    #cris_quicklook(options.output, swath , options.format, options.label)

    return 0



if __name__=='__main__':
    sys.exit(main())

