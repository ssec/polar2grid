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
from datetime import datetime

from polar2grid.core.roles import FrontendRole
from polar2grid.core.fbf import dtype2fbf
from polar2grid.core.constants import SAT_NPP, BKIND_IR, BKIND_I, BKIND_M, BID_13, BID_15, BID_16, BID_5, STATUS_SUCCESS, STATUS_FRONTEND_FAIL

LOG = logging.getLogger(__name__)

# from adl_geo_ref.py in CSPP
# e.g. IASI_d20130310_t152624_M02.atm_prof_rtv.h5
RE_DRRTV = re.compile('(?P<inst>[A-Za-z0-9]+)_d(?P<date>\d+)_t(?P<start_time>\d+)_(?P<sat>[A-Za-z0-9]+)\.h5')

# GUIDEBOOK
# FUTURE: move this to another file when it grows large enough

SAT_INST_TABLE = {
    ('M02', 'IASI'): (SAT_METOPA, INST_IASI),
    ('M01', 'IASI'): (SAT_METOPB, INST_IASI),
    ('g195', 'AIRS'): (None, None),  # FIXME this needs work
    ('')
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
        return {}
    when = datetime.strptime('%(date)s %(start_time)s' % m.groupdict(), '%Y%m%d %H%M%S')
    return { 'start_time': when,
             }


def swath_from_var(var_name, h5_var):
    """
    given a variable by name, and its hdf5 variable object,
    return a normalized numpy masked_array with corrected indexing order
    :param var_name: variable name, used to consult internal guidebook
    :param h5_var: hdf5 object
    :return: numpy masked_array with missing data properly masked and dimensions corrected to
            [in-track, cross-track, layer] for 3D variables
    """
    shape = h5_var.shape
    data = h5_var[:]

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


def swaths_from_h5s(h5_pathnames, var_names=None):
    """
    from a series of Dual Regression output files, return a series of (name, data) swaths concatenating the data
     Assumes all variables present in the first file is present in the rest of the files
    :param h5_pathnames: sequence of hdf5 pathnames, order is preserved in output swaths; assumes valid HDF5 files
    :return: sequence of (name, raw-swath-array) pairs
    """
    h5s = [h5py.File(pn) for pn in h5_pathnames]
    if not h5s:
        return
    # get variable names
    first = h5s[0]
    if var_names is None:
        var_names = list(first.iterkeys())
    else:
        var_names = list(var_names)
    LOG.info('variables found: %s' % repr(var_names))
    for vn in var_names:
        swath = np.concatenate([swath_from_var(vn, h5[vn]) for h5 in h5s], axis=0)
        yield vn, swath


def write_arrays_to_fbf(nditer):
    """
    write derived BT slices to CWD from an iterable yielding (name, data) pairs
    FIXME: promote this upstream??
    FIXME: handle masked arrays properly
    """
    for name,data in nditer:
        rows,cols = data.shape
        dts = dtype2fbf[data.dtype]
        suffix = '.%s.%d.%d' % (dts, cols, rows)
        fn = name + suffix
        LOG.debug('writing to %s...' % fn)
        if data.dtype != np.float32:
            data = data.astype(np.float32)
        with file(fn, 'wb') as fp:
            data.tofile(fp)


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

    # set up the base dictionaries
    meta_data = {
                 "sat": SAT_NPP,
                 "instrument": INST_CRIS,
                 "start_time": modis_guidebook.parse_datetime_from_filename(file_object.file_name),
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

    # pull information on the data that should be in this file
    file_contents_guide = modis_guidebook.FILE_CONTENTS_GUIDE[file_object.matching_re]

    # based on the list of bands/band IDs that should be in the file, load up the meta data and image data
    for band_kind in file_contents_guide.keys() :

        for band_number in file_contents_guide[band_kind] :

            data_kind_const = modis_guidebook.DATA_KINDS[(band_kind, band_number)]

            # TODO, when there are multiple files, this will algorithm will need to change
            meta_data["bands"][(band_kind, band_number)] = {
                                                            "data_kind": data_kind_const,
                                                            "remap_data_as": data_kind_const,
                                                            "kind": band_kind,
                                                            "band": band_number,

                                                            # TO FILL IN LATER
                                                            "rows_per_scan": None,
                                                            "fill_value":    None,
                                                            "fbf_img":       None,
                                                            "swath_rows":    None,
                                                            "swath_cols":    None,
                                                            "swath_scans":   None,

                                                            # this is temporary so it will be easier to load the data later
                                                            "file_obj":      file_object # TODO, strategy won't work with multiple files!
                                                           }



def _load_geonav_data (meta_data_to_update, file_info_objects, nav_uid=None, cut_bad=False) :
    """
    load the geonav data and save it in flat binary files; update the given meta_data_to_update
    with information on where the files are and what the shape and range of the nav data are

    TODO, cut_bad currently does nothing
    FUTURE nav_uid will need to be passed once we are using more types of navigation
    """

    list_of_geo_files = [ ]
    for file_info in file_info_objects :
        list_of_geo_files.append(file_info.get_geo_file())

    # Check if the navigation will need to be interpolated to a better
    # resolution
    # FUTURE: 500m geo nav key will have to be added along with the proper
    # interpolation function
    interpolate_data = False
    if nav_uid in modis_guidebook.NAV_SETS_TO_INTERPOLATE_GEO:
        interpolate_data = True

    # FUTURE, if the longitude and latitude ever have different variable names, this will need refactoring
    lat_temp_file_name, lat_stats = _load_data_to_flat_file (list_of_geo_files, "lat_" + nav_uid,
                                                             modis_guidebook.LATITUDE_GEO_VARIABLE_NAME,
                                                             missing_attribute_name=modis_guidebook.LON_LAT_FILL_VALUE_NAMES[nav_uid],
                                                             interpolate_data=interpolate_data)
    lon_temp_file_name, lon_stats = _load_data_to_flat_file (list_of_geo_files, "lon_" + nav_uid,
                                                             modis_guidebook.LONGITUDE_GEO_VARIABLE_NAME,
                                                             missing_attribute_name=modis_guidebook.LON_LAT_FILL_VALUE_NAMES[nav_uid],
                                                             interpolate_data=interpolate_data)

    # rename the flat file to a more descriptive name
    shape_temp = lat_stats["shape"]
    suffix = '.real4.' + '.'.join(str(x) for x in reversed(shape_temp))
    new_lat_file_name = "latitude_"  + str(nav_uid) + suffix
    new_lon_file_name = "longitude_" + str(nav_uid) + suffix
    os.rename(lat_temp_file_name, new_lat_file_name)
    os.rename(lon_temp_file_name, new_lon_file_name)

    # based on our statistics, save some meta data to our meta data dictionary
    rows, cols = shape_temp
    meta_data_to_update["lon_fill_value"] = lon_stats["fill_value"]
    meta_data_to_update["lat_fill_value"] = lat_stats["fill_value"]
    meta_data_to_update["fbf_lat"]        = new_lat_file_name
    meta_data_to_update["fbf_lon"]        = new_lon_file_name
    meta_data_to_update["nav_set_uid"]    = nav_uid
    meta_data_to_update["swath_rows"]     = rows
    meta_data_to_update["swath_cols"]     = cols
    meta_data_to_update["rows_per_scan"]  = modis_guidebook.ROWS_PER_SCAN[nav_uid]
    meta_data_to_update["swath_scans"]    = rows / meta_data_to_update["rows_per_scan"]

    """ # these have been changed to north, south, east, west and the backend will calculate them anyway
    meta_data_to_update["lat_min"]        = lat_stats["min"]
    meta_data_to_update["lat_max"]        = lat_stats["max"]
    meta_data_to_update["lon_min"]        = lon_stats["min"]
    meta_data_to_update["lon_max"]        = lon_stats["max"]
    """


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
        swath = cris_swath(*filepaths, **kwargs)
        bands = cris_bt_slices(swath.rad_lw, swath.rad_mw, swath.rad_sw)
        bands.update({ 'Latitude': swath.lat, 'Longitude': swath.lon })
        write_arrays_to_fbf(latlon.items())
        write_arrays_to_fbf(bands.items())
        self.info = generate_metadata(swath, bands)
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

