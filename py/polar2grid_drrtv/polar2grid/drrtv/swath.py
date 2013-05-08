#!/usr/bin/env python
# encoding: utf-8
"""
CrIS EDR front end for polar2grid, which extracts band-pass slices of brightness temperature data.

:author:       Ray Garcia (rayg)
:contact:      rayg@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Mar 2013
:license:      GNU GPLv3

Note that Dual Regression products are indexed strangely:
  [in-track, cross-track] for 2D variables
  [level, in-track, cross-track] for 3D variables

Example:
[(u'CAPE', (84, 60)),
 (u'CO2_Amount', (84, 60)),
 (u'COT', (84, 60)),
 (u'CTP', (84, 60)),
 (u'CTT', (84, 60)),
 (u'Channel_Index', (7021,)),
 (u'CldEmis', (84, 60)),
 (u'Cmask', (84, 60)),
 (u'Dewpnt', (101, 84, 60)),
 (u'GDAS_RelHum', (101, 84, 60)),
 (u'GDAS_TAir', (101, 84, 60)),
 (u'H2OMMR', (101, 84, 60)),
 (u'H2Ohigh', (84, 60)),
 (u'H2Olow', (84, 60)),
 (u'H2Omid', (84, 60)),
 (u'Latitude', (84, 60)),
 (u'Lifted_Index', (84, 60)),
 (u'Longitude', (84, 60)),
 (u'O3VMR', (101, 84, 60)),
 (u'Plevs', (101,)),
 (u'Qflag1', (84, 60)),
 (u'Qflag2', (84, 60)),
 (u'Qflag3', (84, 60)),
 (u'RelHum', (101, 84, 60)),
 (u'SurfEmis', (8461, 84, 60)),
 (u'SurfEmis_Wavenumbers', (8461,)),
 (u'SurfPres', (84, 60)),
 (u'TAir', (101, 84, 60)),
 (u'TSurf', (84, 60)),
 (u'totH2O', (84, 60)),
 (u'totO3', (84, 60))]


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

import h5py
import numpy as np
import os
import sys
import logging
import re
import uuid
from datetime import datetime
from collections import namedtuple
from functools import partial

from polar2grid.core.roles import FrontendRole
from polar2grid.core.fbf import dtype2fbf, str_to_dtype
from polar2grid.core.dtype import dtype2np
from polar2grid.core.constants import SAT_METOPA, SAT_METOPB, INST_IASI, NOT_APPLICABLE, \
    DKIND_OPTICAL_THICKNESS, DKIND_PRESSURE, DKIND_LIFTED_INDEX, DKIND_LATITUDE, DKIND_LONGITUDE, \
    DKIND_CAPE, DKIND_CATEGORY, DKIND_EMISSIVITY, DKIND_MIXING_RATIO, DKIND_PERCENT, DKIND_TEMPERATURE, \
    DEFAULT_FILL_VALUE, BKIND_IR, BKIND_I, BKIND_M, BID_13, BID_15, BID_16, STATUS_SUCCESS, STATUS_FRONTEND_FAIL

LOG = logging.getLogger(__name__)

# from adl_geo_ref.py in CSPP
# e.g. IASI_d20130310_t152624_M02.atm_prof_rtv.h5
RE_DRRTV = re.compile(r'(?P<inst>[A-Za-z0-9]+)_d(?P<date>\d+)_t(?P<start_time>\d+)_(?P<sat>[A-Za-z0-9]+).*?\.h5')

# GUIDEBOOK
# FUTURE: move this to another file when it grows large enough
# (sat, inst) => (p2g_sat, p2g_inst, rows_per_swath)
SAT_INST_TABLE = {
    ('M02', 'IASI'): (SAT_METOPA, INST_IASI, 2),
    ('M01', 'IASI'): (SAT_METOPB, INST_IASI, 2),
    ('g195', 'AIRS'): (None, None),  # FIXME this needs work
}

# pressure levels at which to extract swaths
# Plev array is binsearched to make indices
PRESSURE_LEVELS = ()

VAR_TABLE = {
     'CAPE': (DKIND_CAPE, ),
     'CO2_Amount': (None, ),
     'COT': (DKIND_TEMPERATURE, ),
     'CTP': (DKIND_PRESSURE, ),
     'CTT': (DKIND_TEMPERATURE, ),
     'Channel_Index': (None, ),
     'CldEmis': (DKIND_EMISSIVITY, ),
     'Cmask': (DKIND_CATEGORY, ),
     'Dewpnt': (None, ),
     'GDAS_RelHum': (DKIND_PERCENT, ),
     'GDAS_TAir': (DKIND_TEMPERATURE, ),
     'H2OMMR': (DKIND_MIXING_RATIO, ),
     'H2Ohigh': (None, ),
     'H2Olow': (None, ),
     'H2Omid': (None, ),
     'Latitude': (DKIND_LATITUDE, ),
     'Lifted_Index': (None, ),
     'Longitude': (DKIND_LONGITUDE, ),
     'O3VMR': (DKIND_MIXING_RATIO, ),
     'Plevs': (DKIND_PRESSURE, ),
     'Qflag1': (None, ),
     'Qflag2': (None, ),
     'Qflag3': (None, ),
     'RelHum': (DKIND_PERCENT, ),
     'SurfEmis': (DKIND_EMISSIVITY, ),
     'SurfEmis_Wavenumbers': (None, ),
     'SurfPres': (DKIND_PRESSURE, ),
     'TAir': (DKIND_TEMPERATURE, ),
     'TSurf': (DKIND_TEMPERATURE, ),
     'totH2O': (None, ),
     'totO3': (None, ),
     }


# END GUIDEBOOK


def _filename_info(pathname):
    """
    return a dictionary of metadata found in the filename
    :param pathname: dual retrieval HDF output file path
    :return: dictionary of polar2grid information found in the filename
    """
    m = RE_DRRTV.match(os.path.split(pathname)[-1])
    if not m:
        raise ValueError('%s does not parse' % pathname)
    mgd = m.groupdict()
    when = datetime.strptime('%(date)s %(start_time)s' % mgd, '%Y%m%d %H%M%S')
    sat, inst, rps = SAT_INST_TABLE[(mgd['sat'], mgd['inst'])]
    return { 'start_time': when,
             'nav_set_uid': "%s_%s" % (sat, inst),
             'sat': sat,
             'instrument': inst,    # why is this not 'inst'? or 'sat' 'satellite'?
             'rows_per_scan': rps
             }

def _swath_shape(*h5s):
    """
    determine the shape of the retrieval swath
    :param h5s: list of hdf5 objects
    :return: (layers, rows, cols)
    """
    layers, rows, cols = 0, 0, 0
    for h5 in h5s:
        rh = h5['RelHum']
        l, r, c = rh.shape
        if layers == 0:
            layers = l
        if cols == 0:
            cols = c
        rows += r
    return layers, rows, cols


def _swath_info(*h5s):
    """
    return FrontEnd metadata found in attributes
    :param h5: hdf5 object
    :return: dictionary of metadata extracted from attributes, including extra '_plev' pressure variable
    """
    fn_info = _filename_info(h5s[0].filename)
    LOG.debug(repr(fn_info))
    layers, rows, cols = _swath_shape(*h5s)
    rps = fn_info['rows_per_scan']
    zult = {'swath_rows': rows,
            'swath_cols': cols,
            'swath_scans': rows / rps,
            '_plev': h5s[0]['Plevs'][:].squeeze()

            }
    zult.update(fn_info)
    return zult


def swath_from_var(var_name, h5_var, tool=None):
    """
    given a variable by name, and its hdf5 variable object,
    return a normalized numpy masked_array with corrected indexing order
    :param var_name: variable name, used to consult internal guidebook
    :param h5_var: hdf5 object
    :return: numpy masked_array with missing data properly masked and dimensions corrected to
            [in-track, cross-track, layer] for 3D variables
    """
    if tool is not None:
        data = tool(h5_var)
    else:
        data = h5_var[:]
    shape = data.shape

    if len(shape) == 3:
        # roll the layer axis to the back, eg (101, 84, 60) -> (84, 60, 101)
        LOG.debug('rolling %s layer axis to last position' % var_name)
        data = np.rollaxis(data, 0, 3)

    if 'missing_value' in h5_var.attrs:
        mv = h5_var.attrs['missing_value']
        data = np.ma.masked_array(data, data==mv)
    else:
        LOG.warning('no missing_value attribute in %s' % var_name)
        data = np.ma.masked_array(data)
    
    return data


def swaths_from_h5s(h5s, var_tools=None):
    """
    from a series of Dual Regression output files, return a series of (name, data) swaths concatenating the data
     Assumes all variables present in the first file is present in the rest of the files
    :param h5s: sequence of hdf5 objects, order is preserved in output swaths; assumes valid HDF5 file
    :param var_tools: list of (variable-name, data-extraction-tool)
    :param h5_pathnames: sequence of hdf5 pathnames, order is preserved in output swaths; assumes valid HDF5 files
    :return: sequence of (name, raw-swath-array) pairs
    """
    if not h5s:
        return
    # get variable names
    first = h5s[0]
    if var_tools is None:
        var_tools = [(x, None) for x in first.iterkeys()]
    LOG.info('variables desired: %r' % [x[0] for x in var_tools])
    for vn, tool in var_tools:
        swath = np.concatenate([swath_from_var(vn, h5[vn], tool) for h5 in h5s], axis=0)
        yield vn, swath


def _dict_reverse(D):
    return dict((v,k) for (k,v) in D.items())


nptype_to_suffix = _dict_reverse(str_to_dtype)


def write_array_to_fbf(name, data):
    """
    write a swath to a flat binary file, including mapping missing values to DEFAULT_FILL_VALUE
    :param name: variable name
    :param data: data array, typically a numpy.masked_array
    :return:
    """
    if len(data.shape) != 2:
        LOG.warning('data %r shape is %r, ignoring' % (name, data.shape))
        return None
    if hasattr(data, 'mask'):
        mask = data.mask
        data = np.array(data, dtype=data.dtype)
        data[mask] = DEFAULT_FILL_VALUE
    rows, cols = data.shape
    dts = nptype_to_suffix[data.dtype.type]
    suffix = '.%s.%d.%d' % (dts, cols, rows)
    fn = name + suffix
    LOG.debug('writing to %s...' % fn)
    if data.dtype != np.float32:
        data = data.astype(np.float32)
    with file(fn, 'wb') as fp:
        data.tofile(fp)
    return fn


def write_arrays_to_fbf(nditer):
    """
    write derived swaths to CWD from an iterable yielding (name, data) pairs
    """
    for name,data in nditer:
        fn = write_array_to_fbf(name, data)
        if fn is not None:
            yield name, fn


# def _layer(layer_num):
#     return lambda h5v: h5v[layer_num,:,:].squeeze()

def _layer_at_pressure(h5v, plev=None, p=None):
    """
    extract a layer of a variable assuming (layer, rows, cols) indexing and plev lists layer pressures
    this is used to construct slicing tools that are built into the manifest list
    :param h5v: hdf5 variable object
    :param plev: pressure array corresponding to layer dimension
    :param p: pressure level value to find
    :return: data slice from h5v
    """
    # dex = np.searchsorted(plev, p)
    dex = np.abs(plev - p).argmin()

    try:
        LOG.debug('using level %d=%f near %r as %f' % (dex, plev[dex], plev[dex-1:dex+2], p))
    except IndexError:
        pass
    return h5v[dex,:]


manifest_entry = namedtuple("manifest_entry", 'h5_var_name tool bkind dkind bid')


def _var_manifest(sat, inst, plev):
    """
    return set of variable extraction info given satellite, instrument pair, its manifest destiny
    :param sat: const SAT_NPP, SAT_METOPA, etc
    :param inst: INST_IASI, INST_CRIS
    :param plev: pressure level array assumed consistent between files
    :return: yields sequence of (variable-name, (h5_var_name, extraction-tool, DKIND, BID))
    """
    yield "RelHum_500mb", manifest_entry(h5_var_name='RelHum',
                                  tool = partial(_layer_at_pressure, plev=plev, p=500.0),
                                  bkind = NOT_APPLICABLE,
                                  dkind = DKIND_PERCENT,
                                  bid = NOT_APPLICABLE)


def swathbuckler(*h5_pathnames):
    """
    return swath metadata after reading all the files in and writing out fbf files
    :param h5_pathnames:
    :return: fully formed metadata describing swath written to current working directory
    """
    h5s = [h5py.File(pn, 'r') for pn in h5_pathnames]
    if not h5s:
        return {}
    nfo = _swath_info(*h5s)
    bands = nfo['bands'] = {}
    # get list of output "bands", their characteristics, and an extraction tool
    manifest = dict(_var_manifest(nfo['sat'], nfo['instrument'], nfo['_plev']))
    LOG.debug('manifest to extract: %r' % manifest)

    def _gobble(name, h5_var_name, tool, h5s=h5s):
        sections = [swath_from_var(h5_var_name, h5[h5_var_name], tool) for h5 in h5s]
        swath = np.concatenate(sections, axis=0)
        return write_array_to_fbf(name, swath)

    nfo['fbf_lat'] = _gobble('swath_latitude', 'Latitude', None)
    nfo['fbf_lon'] = _gobble('swath_longitude', 'Longitude', None)

    for name, guide in manifest.items():
        LOG.debug("extracting %s from variable %s" % (name, guide.h5_var_name))
        filename = _gobble(name, guide.h5_var_name, guide.tool)
        band = {
            "data_kind": guide.dkind,
            "remap_data_as": guide.dkind,
            "kind": guide.bkind,
            "fbf_img": filename,
            "swath_rows": nfo['swath_rows'],
            "swath_cols": nfo['swath_cols'],
            "swath_scans": nfo['swath_scans'],
            "rows_per_scan": nfo['rows_per_scan']
        }
        bands[name] = band
    return nfo





def test_swath2fbf(pathnames = ['test/input/case1/IASI_d20130310_t152624_M02.atm_prof_rtv.h5']):
    write_arrays_to_fbf(swaths_from_h5s(pathnames))


def _load_meta_data (file_objects) :
    """
    load meta-data from the given list of FileInfoObject's

    Note: this method will eventually support concatinating multiple files,
    for now it only supports processing one file at a time! TODO FUTURE
    """

    # TODO, this is only temporary
    if len(file_objects) != 1 :
        raise ValueError("One file was expected for processing in _load_meta_data_and_image_data and more were given.")
    file_object = file_objects[0]

    nfo = _filename_info(file_object.file_name)

    # set up the base dictionaries
    meta_data = {
                 "sat": SAT_METOPA,
                 "instrument": INST_IASI,
                 "start_time": nfo['start_date'],
                 "bands" : { },

                 # TO FILL IN LATER
                 "rows_per_scan": None,
                 "lon_fill_value": None,
                 "lat_fill_value": None,
                 "fbf_lat":        None,
                 "fbf_lon":        None,
                 # these have been changed to north, south, east, west
                 #"lat_min":        None,
                 #"lon_min":        None,
                 #"lat_max":        None,
                 #"lon_max":        None,
                 "swath_rows":     None,
                 "swath_cols":     None,
                 "swath_scans":    None,
                }

    # # pull information on the data that should be in this file
    # file_contents_guide = modis_guidebook.FILE_CONTENTS_GUIDE[file_object.matching_re]
    #
    # # based on the list of bands/band IDs that should be in the file, load up the meta data and image data
    # for band_kind in file_contents_guide.keys() :
    #
    #     for band_number in file_contents_guide[band_kind] :
    #
    #         data_kind_const = modis_guidebook.DATA_KINDS[(band_kind, band_number)]
    #
    #         # TODO, when there are multiple files, this will algorithm will need to change
    #         meta_data["bands"][(band_kind, band_number)] = {
    #                                                         "data_kind": data_kind_const,
    #                                                         "remap_data_as": data_kind_const,
    #                                                         "kind": band_kind,
    #                                                         "band": band_number,
    #
    #                                                         # TO FILL IN LATER
    #                                                         "rows_per_scan": None,
    #                                                         "fill_value":    None,
    #                                                         "fbf_img":       None,
    #                                                         "swath_rows":    None,
    #                                                         "swath_cols":    None,
    #                                                         "swath_scans":   None,
    #
    #                                                         # this is temporary so it will be easier to load the data later
    #                                                         "file_obj":      file_object # TODO, strategy won't work with multiple files!
    #                                                        }


# def _load_geonav_data (meta_data_to_update, file_info_objects, nav_uid=None, cut_bad=False) :
#     """
#     load the geonav data and save it in flat binary files; update the given meta_data_to_update
#     with information on where the files are and what the shape and range of the nav data are
#
#     TODO, cut_bad currently does nothing
#     FUTURE nav_uid will need to be passed once we are using more types of navigation
#     """
#
#     list_of_geo_files = [ ]
#     for file_info in file_info_objects :
#         list_of_geo_files.append(file_info.get_geo_file())
#
#     # Check if the navigation will need to be interpolated to a better
#     # resolution
#     # FUTURE: 500m geo nav key will have to be added along with the proper
#     # interpolation function
#     interpolate_data = False
#     if nav_uid in modis_guidebook.NAV_SETS_TO_INTERPOLATE_GEO:
#         interpolate_data = True
#
#     # FUTURE, if the longitude and latitude ever have different variable names, this will need refactoring
#     lat_temp_file_name, lat_stats = _load_data_to_flat_file (list_of_geo_files, "lat_" + nav_uid,
#                                                              modis_guidebook.LATITUDE_GEO_VARIABLE_NAME,
#                                                              missing_attribute_name=modis_guidebook.LON_LAT_FILL_VALUE_NAMES[nav_uid],
#                                                              interpolate_data=interpolate_data)
#     lon_temp_file_name, lon_stats = _load_data_to_flat_file (list_of_geo_files, "lon_" + nav_uid,
#                                                              modis_guidebook.LONGITUDE_GEO_VARIABLE_NAME,
#                                                              missing_attribute_name=modis_guidebook.LON_LAT_FILL_VALUE_NAMES[nav_uid],
#                                                              interpolate_data=interpolate_data)
#
#     # rename the flat file to a more descriptive name
#     shape_temp = lat_stats["shape"]
#     suffix = '.real4.' + '.'.join(str(x) for x in reversed(shape_temp))
#     new_lat_file_name = "latitude_"  + str(nav_uid) + suffix
#     new_lon_file_name = "longitude_" + str(nav_uid) + suffix
#     os.rename(lat_temp_file_name, new_lat_file_name)
#     os.rename(lon_temp_file_name, new_lon_file_name)
#
#     # based on our statistics, save some meta data to our meta data dictionary
#     rows, cols = shape_temp
#     meta_data_to_update["lon_fill_value"] = lon_stats["fill_value"]
#     meta_data_to_update["lat_fill_value"] = lat_stats["fill_value"]
#     meta_data_to_update["fbf_lat"]        = new_lat_file_name
#     meta_data_to_update["fbf_lon"]        = new_lon_file_name
#     meta_data_to_update["nav_set_uid"]    = nav_uid
#     meta_data_to_update["swath_rows"]     = rows
#     meta_data_to_update["swath_cols"]     = cols
#     meta_data_to_update["rows_per_scan"]  = modis_guidebook.ROWS_PER_SCAN[nav_uid]
#     meta_data_to_update["swath_scans"]    = rows / meta_data_to_update["rows_per_scan"]
#
#     """ # these have been changed to north, south, east, west and the backend will calculate them anyway
#     meta_data_to_update["lat_min"]        = lat_stats["min"]
#     meta_data_to_update["lat_max"]        = lat_stats["max"]
#     meta_data_to_update["lon_min"]        = lon_stats["min"]
#     meta_data_to_update["lon_max"]        = lon_stats["max"]
#     """


def generate_metadata(swath, bands):
    """
    return metadata dictionary summarizing the granule and generated bands, compatible with frontend output
    """
    raise NotImplementedError('generate_metadata not implemented')


# FUTURE: add a way to configure which slices to produce, or all by default
class CrisSdrFrontend(FrontendRole):
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
        # swath = cris_swath(*filepaths, **kwargs)
        # bands = cris_bt_slices(swath.rad_lw, swath.rad_mw, swath.rad_sw)
        # bands.update({ 'Latitude': swath.lat, 'Longitude': swath.lon })
        # write_arrays_to_fbf(latlon.items())
        # write_arrays_to_fbf(bands.items())
        # self.info = generate_metadata(swath, bands)
        # return self.info


def test_swath(test_data='test/input/case1/IASI_d20130310_t152624_M02.atm_prof_rtv.h5'):
    swath = swaths_from_h5s([test_data])
    return swath


# def test_frontend(test_data='test/input/case1/IASI_d20130310_t152624_M02.atm_prof_rtv.h5'):
#     fe = CrisSdrFrontend()
#     fe.make_swaths([test_data])


def console(banner="enjoy delicious python"):
    from IPython.config.loader import Config
    cfg = Config()
    prompt_config = cfg.PromptManager
    prompt_config.in_template = 'In <\\#>: '
    prompt_config.in2_template = '   .\\D.: '
    prompt_config.out_template = 'Out<\\#>: '

    # First import the embeddable shell class
    from IPython.frontend.terminal.embed import InteractiveShellEmbed

    # Now create an instance of the embeddable shell. The first argument is a
    # string with options exactly as you would type them if you were starting
    # IPython at the system command line. Any parameters you want to define for
    # configuration can thus be specified here.
    ipshell = InteractiveShellEmbed(config=cfg,
                           banner1 = 'Welcome to IPython\n%s\n' % banner,
                           exit_msg = 'Leaving Interpreter, buh-bye.')
    ipshell()



def main():
    import optparse
    usage = """
%prog [options] ...

"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests")
    parser.add_option('-I', '--interactive', dest="interactive",
                    action="store_true", default=False, help="create swaths and interact with metadata")
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    # parser.add_option('-o', '--output', dest='output', default='.',
    #                  help='directory in which to store output')
    # # parser.add_option('-F', '--format', dest='format', default=DEFAULT_PNG_FMT,
    #                  help='format string for output filenames')
    # parser.add_option('-L', '--label', dest='label', default=DEFAULT_LABEL_FMT,
    #                  help='format string for labels')

    (options, args) = parser.parse_args()

    # FUTURE: validating the format strings is advisable

    # make options a globally accessible structure, e.g. OPTS.
    global OPTS
    OPTS = options

    if options.self_test:
        # import doctest
        # doctest.testmod()
        import nose
        nose.run()
        sys.exit(2)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(3, options.verbosity)])

    if not args:
        parser.error('incorrect arguments, try -h or --help.')
        return 9

    m = swathbuckler(*args)
    if options.interactive:
        console("'m' is metadata")
    else:
        from pprint import pprint
        pprint(m)


    return 0



if __name__=='__main__':
    sys.exit(main())

