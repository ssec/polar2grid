#!/usr/bin/env python
# encoding: utf-8
"""
Read one or more contiguous in-order HDF4 MODIS granules
Write out Swath binary files used by ms2gt tools.

:author:       Eva Schiffer (evas)
:author:       David Hoese (davidh)
:contact:      evas@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
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

    Written by David Hoese    January 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

import modis_guidebook
from polar2grid.core.constants import *
from polar2grid.core import roles
from polar2grid.core.fbf import file_appender
from .modis_filters  import convert_radiance_to_bt, make_data_category_cleared, create_fog_band
from .modis_geo_interp_250 import interpolate_geolocation

import numpy
from pyhdf.SD import SD,SDC, SDS, HDF4Error

import os
import re
import sys
import logging

log = logging.getLogger(__name__)

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

    def get_geo_path(self):
        return os.path.join(os.path.split(self.full_path)[0], self.geo_file_name)
    
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
    
    return meta_data

def _load_geonav_data(nav_uid, meta_data_to_update, file_info_objects, cut_bad=False) :
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

def _load_data_to_flat_file (file_objects, descriptive_string, variable_name,
                             missing_attribute_name=None, fill_value_default=DEFAULT_FILL_VALUE,
                             variable_idx=None, scale_name=None, offset_name=None,
                             interpolate_data=False,
                             min_fn=numpy.min, max_fn=numpy.max,
                             valid_range_attribute_name=None) :
    """
    given a list of file info objects, load the requested variable and append it into a single flat
    binary file with a temporary name based on the descriptive string
    
    the name of the new flat binary file and dictionary of statistics about the data will be returned
    """
    
    # a couple of temporaries to hold some stats
    minimum_value = None
    maximum_value = None
    fill_value    = None
    
    # open the file with a temporary name and set up a file appender
    temp_id        = str(os.getpid())
    temp_file_name = temp_id + "." + descriptive_string
    temp_flat_file = file(temp_file_name, 'wb')
    temp_appender  = file_appender(temp_flat_file, dtype=numpy.float32) # set to float32 to keep everything consistent
    
    # append in data from each file
    # TODO, these files aren't currently sorted by date
    for file_object in file_objects :
        
        # get the appropriate file and variable object
        temp_var_object = file_object.select(variable_name)
        
        # extract the variable data
        temp_var_data   = temp_var_object[:].astype(numpy.float32) if variable_idx is None else temp_var_object[variable_idx].astype(numpy.float32)
        
        # figure out where the missing values are
        temp_fill_value = None
        # if we have an attribute name for the fill value then load it, otherwise use the default
        if missing_attribute_name is not None :
            temp_fill_value = temp_var_object.attributes()[missing_attribute_name]
        else :
            temp_fill_value = fill_value_default
        # if we already have a fill value and it's not the same as the one we just loaded, fix our data
        if (fill_value is not None) and (temp_fill_value != fill_value) :
            temp_var_data[temp_var_data == temp_fill_value] = fill_value
            temp_fill_value = fill_value
        fill_value      = temp_fill_value
        not_fill_mask   = temp_var_data != fill_value
        
        # some bands have a value that means saturation of the sensor or that they could not be aggregated
        if valid_range_attribute_name is not None:
            valid_min,valid_max = temp_var_object.attributes()[valid_range_attribute_name]
        else:
            valid_min,valid_max = None,None
        # Mask out saturation or couldn't aggregate to 1km values
        # XXX: I don't think there is a way to get these values from the hdf files
        saturation_value = modis_guidebook.SATURATION_VALUE
        cant_aggr_value  = modis_guidebook.CANT_AGGR_VALUE
        if valid_max is not None:
            # XXX: This may be a waste of time to perform on other bands, but I'm not sure
            log.debug("Clipping saturation values")
            temp_var_data[ (temp_var_data == saturation_value) | (temp_var_data == cant_aggr_value) ] = valid_max

        # if there's a scale and/or offset load them
        scale_value  = None
        if scale_name  is not None :
            scale_value  = temp_var_object.attributes()[scale_name] if variable_idx  is None else temp_var_object.attributes()[scale_name][variable_idx]
            scale_value  = float(scale_value)  if scale_value  is not None else scale_value
        offset_value = None
        if offset_name is not None :
            offset_value = temp_var_object.attributes()[offset_name] if variable_idx is None else temp_var_object.attributes()[offset_name][variable_idx]
            offset_value = float(offset_value) if offset_value is not None else offset_value
        
        log.debug ("Variable " + str(variable_name) + " is using scale value " + str(scale_value) + " and offset value " + str(offset_value))
        
        # abstractly the formula for scaling is:
        #           data_to_return = (data_from_file - offset_value) * scale_value
        
        # if we found an offset use it to offset the data
        if offset_value is not None :
            temp_var_data[not_fill_mask] -= offset_value
        # if we found a scale use it to scale the data
        if scale_value  is not None :
            temp_var_data[not_fill_mask] *= scale_value
        
        # Special case: if we are handling 250m or 500m data we need to interpolate
        # the navigation lat/lon data only exists for 1km resolutions
        if interpolate_data:
            log.debug("Interpolating to higher resolution: %s" % (variable_name,))
            temp_var_data = interpolate_geolocation(temp_var_data)

        # append the file data to the flat file
        temp_appender.append(temp_var_data)
        
        # at this point we need to calculate some statistics based on the data we're saving
        to_use_temp   = numpy.append(temp_var_data[not_fill_mask], minimum_value) if minimum_value is not None else temp_var_data[not_fill_mask]
        minimum_value = min_fn(to_use_temp) if to_use_temp.size > 0 else minimum_value
        to_use_temp   = numpy.append(temp_var_data[not_fill_mask], maximum_value) if maximum_value is not None else temp_var_data[not_fill_mask]
        maximum_value = max_fn(to_use_temp) if to_use_temp.size > 0 else maximum_value
        
        log.debug ("After loading, variable " + str(variable_name) + " has fill value " + str(fill_value) + " and data range " + str(minimum_value) + " to " + str(maximum_value))
    
    # save some statistics to a dictionary
    stats = {
             "shape": temp_appender.shape,
             "min":         minimum_value,
             "max":         maximum_value,
             "fill_value":     fill_value,
            }
    
    # close the flat binary file object (insuring that all appends are flushed to disk)
    temp_flat_file.close()
    
    return temp_file_name, stats

def _load_image_data (nav_uid, meta_data_to_update, cut_bad=False) :
    """
    load image data into binary flat files based on the meta data provided
    """
    
    # process each of the band kind / id sets
    for band_kind, band_id in meta_data_to_update["bands"] :
        
        # load the data into a flat file
        (scale_name, offset_name) = modis_guidebook.RESCALING_ATTRS[(band_kind, band_id)]
        matching_file_pattern = meta_data_to_update["bands"][(band_kind, band_id)]["file_obj"].matching_re
        var_name = modis_guidebook.VAR_NAMES[matching_file_pattern][(band_kind,band_id)]
        var_idx  = modis_guidebook.VAR_IDX[matching_file_pattern][(band_kind,band_id)]
        valid_range_attribute_name = modis_guidebook.VALID_RANGE_ATTR_NAMES[(band_kind, band_id)]
        temp_image_file_name, image_stats = _load_data_to_flat_file ([meta_data_to_update["bands"][(band_kind, band_id)]["file_obj"].file_object],
                                                                     "%s_%s_%s" % (str(nav_uid),str(band_kind),str(band_id)),
                                                                     var_name,
                                                                     missing_attribute_name=modis_guidebook.FILL_VALUE_ATTR_NAMES[(band_kind, band_id)],
                                                                     variable_idx=var_idx,
                                                                     scale_name=scale_name, offset_name=offset_name,
                                                                     valid_range_attribute_name=valid_range_attribute_name)
        
        # we don't need this entry with the file object anymore, so remove it
        del meta_data_to_update["bands"][(band_kind, band_id)]["file_obj"]
        
        # rename the file with a more descriptive name
        shape_temp = image_stats["shape"]
        suffix = '.real4.' + '.'.join(str(x) for x in reversed(shape_temp))
        new_img_file_stem = "image_%s_%s_%s" % (str(nav_uid),str(band_kind),str(band_id))
        new_img_file_name = new_img_file_stem + suffix
        os.rename(temp_image_file_name, new_img_file_name)
        
        # based on our statistics, save some meta data to our meta data dictionary
        rows, cols = shape_temp
        meta_data_to_update["bands"][(band_kind, band_id)]["fill_value"]  = image_stats["fill_value"]
        meta_data_to_update["bands"][(band_kind, band_id)]["fbf_img"]     = new_img_file_name
        meta_data_to_update["bands"][(band_kind, band_id)]["swath_rows"]  = rows
        meta_data_to_update["bands"][(band_kind, band_id)]["swath_cols"]  = cols
        meta_data_to_update["bands"][(band_kind, band_id)]["rows_per_scan"] = rows_per_scan = meta_data_to_update["rows_per_scan"]
        meta_data_to_update["bands"][(band_kind, band_id)]["swath_scans"] = rows / rows_per_scan
        
        if rows != meta_data_to_update["swath_rows"] or cols != meta_data_to_update["swath_cols"]:
            msg = ("Expected %d rows and %d cols, but band %s %s had %d rows and %d cols"
                   % (meta_data_to_update["swath_rows"], meta_data_to_update["swath_cols"], band_kind, band_id, rows, cols))
            log.error(msg)
            raise ValueError(msg)

class Frontend(roles.FrontendRole):
    removable_file_patterns = [
            "*.*_infrared_20",
            "*.*_infrared_27",
            "*.*_infrared_31",
            "*.*_visible_01",
            "*.*_visible_02",
            "*.*_visible_07",
            "*.*_visible_26",
            "*.*_cloud_mask_None",
            "*.*_land_sea_mask_None",
            "*.*_solar_zenith_angle_None",
            "*.*_land_surface_temperature_None",
            "*.*_summer_land_surface_temp_None",
            "*.*_ice_surface_temperature_None",
            "*.*_inversion_strength_None",
            "*.*_inversion_depth_None",
            "*.*_ice_concentration_None",
            "*.*_cloud_top_temperature_None",
            "*.*_total_precipitable_water",
            "*.*_ndvi_None",
            "*.lat_*",
            "*.lon_*",
            "image*.real4.*",
            "btimage*.real4.*",
            "bt_prescale*.real4.*",
            "cloud_cleared*.real4.*",
            "latitude*.real4.*",
            "longitude*.real4.*"
            ]

    def __init__(self):
        pass

    def make_swaths(self, nav_set_uid, filepaths, **kwargs):
        
        create_fog = kwargs.pop("create_fog", False)
        cut_bad    = kwargs.pop("cut_bad", False)
        remove_aux = kwargs.pop("remove_aux", True)
        
        # load up all the meta data
        meta_data = { }
        for file_pattern_key in filepaths.keys() :
            temp_filepaths = sorted(filepaths[file_pattern_key])
            
            if len(temp_filepaths) > 0 :
                # TODO, for now this method only handles one file, eventually it will need to handle more
                if len(temp_filepaths) != 1 :
                    log.error("Swath creation failed")
                    log.debug("Swath creation error: One file was expected for processing in make_swaths and more were given.")
                    continue
                
                # make sure the file exists and get minimal info on it
                assert(os.path.exists(temp_filepaths[0]))
                file_info = FileInfoObject(temp_filepaths[0])
                
                # get the initial meta data information and raw image data
                log.info("Getting data file info...")
                temp_meta_data = _load_meta_data ([file_info])
                temp_bands     = { } if "bands" not in meta_data else meta_data["bands"]
                meta_data.update(temp_meta_data)
                meta_data["bands"].update(temp_bands)

        # Load the actual data
        try:
            # Get file objects for one file pattern
            one_patterns_file_objects = [ FileInfoObject(fp) for fp in filepaths[ filepaths.keys()[0] ] ]

            log.info("Creating binary files for latitude and longitude data")
            _load_geonav_data(nav_set_uid, meta_data, one_patterns_file_objects, cut_bad=cut_bad)

            # load up all the image data
            log.info("Creating binary files for image data")
            _load_image_data(nav_set_uid, meta_data, cut_bad=cut_bad)
        except StandardError:
            log.error("Swath creation failed")
            log.debug("Swath creation error:", exc_info=1)

        # if we weren't able to load any of the swaths... stop now
        if len(meta_data.keys()) <= 0 :
            log.error("Unable to load basic swaths, quitting...")
            return meta_data
        
        # pull out some information for ease of use
        band_info = meta_data["bands"]
        sat       = meta_data["sat"]
        
        # cloud clear some of our bands if we have the cloud mask
        for band_kind, band_id in band_info.keys() :
            
            # only do the clearing if it's appropriate for this band
            if modis_guidebook.IS_CLOUD_CLEARED[(band_kind, band_id)] :
                
                # we can only cloud clear if we have a cloud mask
                if (BKIND_CMASK, NOT_APPLICABLE) in band_info :
                    
                    file_to_use = band_info[band_kind, band_id]["fbf_swath"] if "fbf_swath" in band_info[band_kind, band_id] else band_info[band_kind, band_id]["fbf_img"]
                    try:
                        new_path = make_data_category_cleared (file_to_use, band_info[(BKIND_CMASK, NOT_APPLICABLE)]["fbf_img"],
                                                               list_of_category_values_to_clear=modis_guidebook.CLOUDS_VALUES_TO_CLEAR,
                                                               data_fill_value=band_info[band_kind, band_id]["fill_value"],
                                                               prefix_for_file="cloud_cleared_%s")
                        band_info[band_kind, band_id]["fbf_swath"] = new_path
                    except StandardError:
                        log.error("Unexpected error while cloud clearing " + str(band_kind) + " " + str(band_id) + ", removing...")
                        log.debug("Error:", exc_info=1)
                        del band_info[(band_kind, band_id)]
                
                # if we don't have the cloud mask to clear this product, we can't produce it
                else :
                    log.error("Cloud mask unavailable to cloud clear " + str(band_kind) + " " + str(band_id) + ", removing...")
                    del band_info[(band_kind, band_id)]
        
        # clear some data based on the land sea mask
        for band_kind, band_id in band_info.keys() :
            
            clearing_key = modis_guidebook.CLEAR_ALL_LANDSEA_VALUES_EXCEPT[(band_kind, band_id)]
            
            # only do the clearing if it's appropriate for this band
            if clearing_key is not None :
                
                # we can only clear if we have a land sea mask
                if (BKIND_LSMSK, NOT_APPLICABLE) in band_info :
                    
                    file_to_use = band_info[band_kind, band_id]["fbf_swath"] if "fbf_swath" in band_info[band_kind, band_id] else band_info[band_kind, band_id]["fbf_img"]
                    try:
                        new_path = make_data_category_cleared (file_to_use, band_info[(BKIND_LSMSK, NOT_APPLICABLE)]["fbf_img"],
                                                               list_of_category_values_to_preserve=clearing_key,
                                                               data_fill_value=band_info[band_kind, band_id]["fill_value"],
                                                               prefix_for_file="landsea_cleared_%s")
                        band_info[band_kind, band_id]["fbf_swath"] = new_path
                    except StandardError:
                        log.error("Unexpected error while land sea clearing " + str(band_kind) + " " + str(band_id) + ", removing...")
                        log.debug("Error:", exc_info=1)
                        del band_info[(band_kind, band_id)]
                
                # if we don't have the cloud mask to clear this product, we can't produce it
                else :
                    log.error("Land sea mask unavailable to clear parts of " + str(band_kind) + " " + str(band_id) + ", removing...")
                    del band_info[(band_kind, band_id)]
        
        # convert some of our bands to brightness temperature
        for band_kind, band_id in band_info.keys() :
            
            # only do the conversion if it's appropriate for this band
            if modis_guidebook.SHOULD_CONVERT_TO_BT[(band_kind, band_id)] :
                
                file_to_use = band_info[band_kind, band_id]["fbf_swath"] if "fbf_swath" in band_info[band_kind, band_id] else band_info[band_kind, band_id]["fbf_img"]
                
                try :
                    # convert the data and change the associated meta data to reflect the change
                    new_path = convert_radiance_to_bt (file_to_use, sat, band_id, fill_value=band_info[band_kind, band_id]["fill_value"])
                    band_info[band_kind, band_id]["fbf_swath"] = new_path
                    band_info[band_kind, band_id]["data_kind"] = DKIND_BTEMP
                except StandardError :
                    log.error("Unexpected error prescaling " + str(band_kind) + " " + str(band_id) + ", removing...")
                    log.debug("Prescaling error:", exc_info=1)
                    del band_info[(band_kind, band_id)]
        
        # the fog band must be calculated after the other bands are converted to brightness temperatures
        
        # if we have what we need, we want to build the fog band
        if create_fog :
            have_bands_needed_for_fog = True
            for band_kind, band_id in modis_guidebook.BANDS_REQUIRED_TO_CALCULATE_FOG_BAND :
                have_bands_needed_for_fog = False if (band_kind, band_id) not in band_info else have_bands_needed_for_fog
            if have_bands_needed_for_fog :
                try :
                    fog_meta_data = create_fog_band (band_info[(BKIND_IR, BID_20)], band_info[(BKIND_IR, BID_31)],
                                                     sza_meta_data=band_info[(BKIND_SZA, NOT_APPLICABLE)],
                                                     fog_fill_value=band_info[(BKIND_IR, BID_20)]['fill_value']) # for now, use one of the fill values
                    band_info[(fog_meta_data["kind"], fog_meta_data["band"])] = fog_meta_data
                except StandardError :
                    log.warning("Error while creating fog band; fog will not be created...")
                    log.debug("Fog creation error:", exc_info=1)
        
        # We don't want to give solar zenith angle to the rest of polar2grid, so we'll remove it
        if remove_aux:
            for band_kind,band_id in modis_guidebook.AUX_BANDS:
                if (band_kind,band_id) in band_info:
                    del band_info[(band_kind, band_id)]

        return meta_data
    
    @classmethod
    def sort_files_by_nav_uid(cls, filepaths):
        """
        sort the filepaths by which navigation they use
        """
        
        return modis_guidebook.sort_files_by_nav_uid(filepaths)
    
    @classmethod
    def parse_datetimes_from_filepaths(cls, filepaths):
        """
        given a list of filepaths, return the associated datetimes
        """
        
        all_datetimes = [ ]
        
        # figure out each datetime
        for filepath in filepaths :
            # Guidebook's function ignores bad files
            datetime_temp = modis_guidebook.parse_datetime_from_filename(os.path.split(filepath)[-1])
            all_datetimes.append(datetime_temp) if datetime_temp is not None else log.debug("Discarding None datetime.") # TODO, fix the datetime generator so this doesn't happen
        
        return all_datetimes

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
