#!/usr/bin/env python
# encoding: utf-8
"""
Read one or more contiguous in-order HDF4 MODIS granules
Write out Swath binary files used by ms2gt tools.

:author:       Eva Schiffer (evas)
:contact:      evas@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Sept 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

import modis_guidebook
from polar2grid.core.constants import *


import numpy
from pyhdf.SD import SD,SDC, SDS, HDF4Error

import os
import re
import sys
import logging
from glob import glob

log = logging.getLogger(__name__)

class array_appender(object):
    """wrapper for a numpy array object which gives it a binary data append usable with "catenate"
    """
    A = None
    shape = (0,0)
    def __init__(self, nparray = None):
        if nparray:
            self.A = nparray
            self.shape = nparray.shape

    def append(self, data):
        # append new rows to the data
        if self.A is None:
            self.A = numpy.array(data)
            self.shape = data.shape
        else:
            self.A = numpy.concatenate((self.A, data))
            self.shape = self.A.shape
        log.debug('array shape is now %s' % repr(self.A.shape))


class file_appender(object):
    """wrapper for a file object which gives it a binary data append usable with "catenate"
    """
    F = None
    shape = (0,0)
    def __init__(self, file_obj, dtype):
        self.F = file_obj
        self.dtype = dtype

    def append(self, data):
        # append new rows to the data
        if data is None:
            return
        inform = data.astype(self.dtype) if self.dtype != data.dtype else data
        inform.tofile(self.F)
        self.shape = (self.shape[0] + inform.shape[0], ) + data.shape[1:]
        log.debug('%d rows in output file' % self.shape[0])

class FileInfoObject (object) :
    """
    An object that will automatically compile some info on our file.
    """
    
    def __init__ (self, file_path, load_file=True) :
        """
        Figure out some per-file information.
        """
        
        self.full_path     = file_path
        self.file_name     = os.path.split(file_path)[1]
        self.matching_re   = _get_matching_re(self.file_name)
        self.datetime      = modis_guidebook.parse_datetime_from_filename(self.file_name)
        self.geo_file_name = modis_guidebook.get_equivalent_geolocation_filename(self.file_name)
        self.geo_file_obj  = None
        
        self.file_object   = None
        if load_file :
            self.file_object = SD(self.full_path, SDC.READ)
        
    
    def get_geo_file (self) :
        """
        get the geonavigation file as an opened file object, open it if needed
        """
        
        if self.geo_file_obj is None :
            self.geo_file_obj = SD(os.path.join(os.path.split(self.full_path)[0], self.geo_file_name), SDC.READ)
        
        return self.geo_file_obj
    
    def close_files (self) :
        """
        close the various files when we're done with them
        """
        
        self.file_object.close()
        if self.geo_file_obj is not None :
            self.geo_file_obj.close()

def _get_matching_re (file_name) :
    """
    given a file, figure out what regular expression matches it in
    the modis_guidebook.FILE_CONTENTS_GUIDE
    
    WARNING: if the file somehow matches multiple expressions,
    only the last will be returned
    """
    matched_re = None
    
    for file_expression in modis_guidebook.FILE_CONTENTS_GUIDE :
        
        if re.match(file_expression, file_name) :
            matched_re = file_expression
    
    return matched_re

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
                 "sat": modis_guidebook.get_satellite_from_filename(file_object.file_name),
                 "instrument": INST_MODIS,
                 "start_time": modis_guidebook.parse_datetime_from_filename(file_object.file_name),
                 "bands" : { },
                 "rows_per_scan": modis_guidebook.ROWS_PER_SCAN,
                 
                 # TO FILL IN LATER
                 "fbf_lat":       None,
                 "fbf_lon":       None,
                 "lat_min":       None,
                 "lon_min":       None,
                 "lat_max":       None,
                 "lon_max":       None,
                 "swath_rows":    None,
                 "swath_cols":    None,
                 "swath_scans":   None,
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
                                                            "rows_per_scan": modis_guidebook.ROWS_PER_SCAN,
                                                            
                                                            # TO FILL IN LATER
                                                            "fbf_img":       None,
                                                            "swath_rows":    None,
                                                            "swath_cols":    None,
                                                            "swath_scans":   None,
                                                            
                                                            # this is temporary so it will be easier to load the data later
                                                            "file_obj":      file_object # TODO, strategy won't work with multiple files!
                                                           }
    
    return meta_data

def _load_geonav_data (meta_data_to_update, file_info_objects, cut_bad=False) :
    """
    load the geonav data and save it in flat binary files; update the given meta_data_to_update
    with information on where the files are and what the shape and range of the nav data are
    
    TODO, cut_bad currently does nothing
    """
    
    list_of_geo_files = [ ]
    for file_info in file_info_objects :
        list_of_geo_files.append(file_info.get_geo_file())
    
    lat_temp_file_name, lat_stats = _load_data_to_flat_file (list_of_geo_files, "lat",
                                                             modis_guidebook.LATITUDE_GEO_VARIABLE_NAME,
                                                             "_FillValue")
    lon_temp_file_name, lon_stats = _load_data_to_flat_file (list_of_geo_files, "lon",
                                                             modis_guidebook.LONGITUDE_GEO_VARIABLE_NAME,
                                                             "_FillValue")
    
    # rename the flat file to a more descriptive name
    shape_temp = lat_stats["shape"]
    suffix = '.real4.' + '.'.join(str(x) for x in reversed(shape_temp))
    new_lat_file_name = "latitude"  + suffix # TODO, when we have multiple sources, this will break down!
    new_lon_file_name = "longitude" + suffix # TODO, when we have multiple sources, this will break down!
    os.rename(lat_temp_file_name, new_lat_file_name)
    os.rename(lon_temp_file_name, new_lon_file_name)
    
    # based on our statistics, save some meta data to our meta data dictionary
    rows, cols = shape_temp
    meta_data_to_update["fbf_lat"]     = new_lat_file_name
    meta_data_to_update["fbf_lon"]     = new_lon_file_name
    meta_data_to_update["swath_rows"]  = rows
    meta_data_to_update["swath_cols"]  = cols
    meta_data_to_update["swath_scans"] = rows / modis_guidebook.ROWS_PER_SCAN
    meta_data_to_update["lat_min"]     = lat_stats["min"]
    meta_data_to_update["lat_max"]     = lat_stats["max"]
    meta_data_to_update["lon_min"]     = lon_stats["min"]
    meta_data_to_update["lon_max"]     = lon_stats["max"]
    
    """ TODO, talk to Dave about these; will need to sub for the min_fn and max_fn to get the right behavior at discontinuities
    "lat_min":       None,
    "lon_min":       None,
    "lat_max":       None,
    "lon_max":       None,
    """

def _load_data_to_flat_file (file_objects, descriptive_string, variable_name, missing_attribute_name,
                             variable_idx=None, scale_name=None, offset_name=None,
                             min_fn=numpy.min, max_fn=numpy.max) :
    """
    given a list of file info objects, load the requested variable and append it into a single flat
    binary file with a temporary name based on the descriptive string
    
    the name of the new flat binary file and dictionary of statistics about the data will be returned
    """
    
    # a couple of temporaries to hold some stats
    minimum_value = None
    maximum_value = None
    
    # open the file with a temporary name and set up a file appender
    temp_id        = str(os.getpid())
    temp_file_name = temp_id + "." + descriptive_string
    temp_flat_file = file(temp_file_name, 'wb')
    temp_appender  = file_appender(temp_flat_file, dtype=numpy.float32) # TODO does this need to be a particular dtype?
    
    # append in data from each file
    # TODO, these files aren't currently sorted by date?
    for file_object in file_objects :
        
        # get the appropriate file and variable object
        #print ("variable name: " + str(variable_name))
        temp_var_object = file_object.select(variable_name)
        
        # extract the variable data
        temp_var_data   = temp_var_object[:] if variable_idx is None else temp_var_object[variable_idx]
        
        # figure out where the missing values are
        #log.debug("attributes: " + str(temp_var_object.attributes()))
        fill_value      = temp_var_object.attributes()[missing_attribute_name]
        not_fill_mask   = temp_var_data != fill_value
        
        # if there's a scale and/or offset load them
        scale_value  = None
        if scale_name  is not None :
            scale_value  = temp_var_object.attributes()[scale_name] if variable_idx  is None else temp_var_object.attributes()[scale_name][variable_idx]
        offset_value = None
        if offset_name is not None :
            offset_value = temp_var_object.attributes()[offset_name] if variable_idx is None else temp_var_object.attributes()[offset_name][variable_idx]
        
        # abstractly the formula for scaling is:
        #           scaled_data = (unscaled_data * scale_value) + offset_value
        
        # if we found a scale use it to scale the data
        if scale_value  is not None :
            temp_var_data[not_fill_mask] *= scale_value
        # if we found an offset use it to offset the data
        if offset_value is not None :
            temp_var_data[not_fill_mask] += offset_value
        
        # append the file data to the flat file
        temp_appender.append(temp_var_data)
        
        # at this point we need to calculate some statistics based on the data we're saving
        minimum_value = min_fn(numpy.append(temp_var_data[not_fill_mask], minimum_value))
        maximum_value = max_fn(numpy.append(temp_var_data[not_fill_mask], maximum_value))
    
    # save some statistics to a dictionary TODO, more statistics are still needed here
    stats = {
             "shape": temp_appender.shape,
             "min":         minimum_value,
             "max":         maximum_value,
            }
    
    # close the flat binary file object (insuring that all appends are flushed to disk)
    temp_flat_file.close()
    
    return temp_file_name, stats

def _load_image_data (meta_data_to_update, cut_bad=False) :
    """
    load image data into binary flat files based on the meta data provided
    """
    
    # process each of the band kind / id sets
    for band_kind, band_id in meta_data_to_update["bands"] :
        
        # load the data into a flat file
        (scale_name, offset_name) = modis_guidebook.RESCALING_ATTRS[(band_kind, band_id)]
        temp_image_file_name, image_stats = _load_data_to_flat_file ([meta_data_to_update["bands"][(band_kind, band_id)]["file_obj"].file_object],
                                                                     str(band_kind) + str(band_id),
                                                                     modis_guidebook.VAR_NAMES[(band_kind, band_id)],
                                                                     "_FillValue",
                                                                     variable_idx=modis_guidebook.VAR_IDX[(band_kind, band_id)],
                                                                     scale_name=scale_name, offset_name=offset_name)
        
        # we don't need this entry with the file object anymore, so remove it
        #del meta_data_to_update["bands"][(band_kind, band_id)]["file_obj"] # TODO, make sure this is the right syntax
        
        # rename the file with a more descriptive name
        shape_temp = image_stats["shape"]
        suffix = '.real4.' + '.'.join(str(x) for x in reversed(shape_temp))
        new_img_file_name = "image_" + str(band_kind) + "_" + str(band_id) + suffix
        os.rename(temp_image_file_name, new_img_file_name)
        
        # based on our statistics, save some meta data to our meta data dictionary
        rows, cols = shape_temp
        meta_data_to_update["bands"][(band_kind, band_id)]["fbf_img"]     = new_img_file_name
        meta_data_to_update["bands"][(band_kind, band_id)]["swath_rows"]  = rows
        meta_data_to_update["bands"][(band_kind, band_id)]["swath_cols"]  = cols
        meta_data_to_update["bands"][(band_kind, band_id)]["swath_scans"] = rows / modis_guidebook.ROWS_PER_SCAN
        
        if rows != meta_data_to_update["swath_rows"] or cols != meta_data_to_update["swath_cols"]:
            msg = ("Expected %d rows and %d cols, but band %s %s had %d rows and %d cols"
                   % (meta_data_to_update["swath_rows"], meta_data_to_update["swath_cols"], band_kind, band_id, rows, cols))
            log.error(msg)
            raise ValueError(msg)

def make_swaths(ifilepaths, cut_bad=False):
    """Takes MODIS hdf files and creates flat binary files for the information
    required to do further processing.

    :Parameters:
        ifilepaths : list
            List of image data filepaths ('*.hdf') of one kind of band that are
            to be concatenated into a swath. These paths should already be user
            expanded absolute paths.
            TODO, This code does not yet handle concatination of multiple files.
            TODO, For now only one file will be accepted.
    :Keywords:
        cut_bad : bool
            Specify whether or not to delete/cut out entire scans of data
            when navigation data is bad.  This is done because the ms2gt
            utilities used for remapping can't handle incorrect navigation data
            TODO, for now this doesn't really do anything!
    """
    
    # TODO, for now this method only handles one file, eventually it will need to handle more
    if len(ifilepaths) != 1 :
        raise ValueError("One file was expected for processing in make_swaths and more were given.")
    
    # make sure the file exists and get minimal info on it
    assert(os.path.exists(ifilepaths[0]))
    file_info = FileInfoObject(ifilepaths[0])
    
    # get the initial meta data information and raw image data
    log.info("Getting data file info...")
    meta_data = _load_meta_data ([file_info])
    
    # load the geonav data and put it in flat binary files
    log.info("Creating binary files for latitude and longitude data")
    _load_geonav_data (meta_data, [file_info], cut_bad=cut_bad)
    
    # load the image data and put it in flat binary files
    log.info("Creating binary files for image data")
    _load_image_data (meta_data, cut_bad=cut_bad)
    
    return meta_data

def main():
    import optparse
    usage = """
%prog [options] filename1.h,filename2.h,filename3.h,... struct1,struct2,struct3,...

"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests")
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    # parser.add_option('-o', '--output', dest='output',
    #                 help='location to store output')
    # parser.add_option('-I', '--include-path', dest="includes",
    #                 action="append", help="include path to append to GCCXML call")
    (options, args) = parser.parse_args()

    # make options a globally accessible structure, e.g. OPTS.
    global OPTS
    OPTS = options

    if options.self_test:
        import doctest
        doctest.testmod()
        sys.exit(0)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])

    if not args:
        parser.error( 'incorrect arguments, try -h or --help.' )
        return 9

    import json
    meta_data = make_swaths(args[:])
    print json.dumps(meta_data)
    return 0

if __name__=='__main__':
    sys.exit(main())
