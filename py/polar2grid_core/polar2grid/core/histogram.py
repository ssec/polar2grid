#!/usr/bin/env python
# encoding: utf-8
"""
Functions related to histogram equalization. This is a scaling function like the
others found in rescale.py, but has so much support infrastructure it's been moved
to it's own module.

:attention:
    A scaling function is not guarenteed to not change the
    original data array passed.  If fact, it is faster in most cases
    to change the array in place.


:author:       Eva Schiffer (evas)
:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

import sys
import logging
import numpy

log = logging.getLogger(__name__)

def histogram_equalization (data, mask_to_equalize,
                            number_of_bins=1000,
                            std_mult_cutoff=4.0,
                            do_zerotoone_normalization=True,
                            valid_data_mask=None,
                            
                            # these are theoretically hooked up, but not useful with only one equalization
                            clip_limit=None,
                            slope_limit=None,
                            
                            # these parameters don't do anything, they're just here to mirror those in the other call
                            do_log_scale=False,
                            log_offset=None,
                            local_radius_px=None,
                            out=None) :
    """
    Perform a histogram equalization on the data selected by mask_to_equalize.
    The data will be separated into number_of_bins levels for equalization and
    outliers beyond +/- std_mult_cutoff*std will be ignored.
    
    If do_zerotoone_normalization is True the data selected by mask_to_equalize
    will be returned in the 0 to 1 range. Otherwise the data selected by
    mask_to_equalize will be returned in the 0 to number_of_bins range.
    
    Note: the data will be changed in place.
    """

    out = out if out is not None else data.copy()
    mask_to_use = mask_to_equalize if valid_data_mask is None else valid_data_mask
    
    log.debug("    determining DNB data range for histogram equalization")
    avg = numpy.mean(data[mask_to_use])
    std = numpy.std (data[mask_to_use])
    # limit our range to +/- std_mult_cutoff*std; e.g. the default std_mult_cutoff is 4.0 so about 99.8% of the data
    concervative_mask = (data < (avg + std*std_mult_cutoff)) & (data > (avg - std*std_mult_cutoff)) & mask_to_use
    
    log.debug("    running histogram equalization")
    cumulative_dist_function, temp_bins = _histogram_equalization_helper (data[concervative_mask], number_of_bins, clip_limit=clip_limit, slope_limit=slope_limit)
    
    # linearly interpolate using the distribution function to get the new values
    out[mask_to_equalize] = numpy.interp(data[mask_to_equalize], temp_bins[:-1], cumulative_dist_function)
    
    # if we were asked to, normalize our data to be between zero and one, rather than zero and number_of_bins
    if do_zerotoone_normalization :
        _linear_normalization_from_0to1 (out, mask_to_equalize, number_of_bins)
    
    return out

def local_histogram_equalization (data, mask_to_equalize, valid_data_mask=None, number_of_bins=1000,
                                  std_mult_cutoff=3.0,
                                  do_zerotoone_normalization=True,
                                  local_radius_px=300,
                                  clip_limit=60.0, #20.0,
                                  slope_limit=3.0, #0.5,
                                  do_log_scale=True,
                                  log_offset=0.00001, # can't take the log of zero, so the offset may be needed; pass 0.0 if your data doesn't need it
                                  out=None
                                  ) :
    """
    equalize the provided data (in the mask_to_equalize) using adaptive histogram equalization
    tiles of width/height (2 * local_radius_px + 1) will be calculated and results for each pixel will be bilinerarly interpolated from the nearest 4 tiles
    when pixels fall near the edge of the image (there is no adjacent tile) the resultant interpolated sum from the available tiles will be multipled to
    account for the weight of any missing tiles (pixel total interpolated value = pixel available interpolated value / (1 - missing interpolation weight))
    
    if do_zerotoone_normalization is True the data will be scaled so that all data in the mask_to_equalize falls between 0 and 1; otherwise the data
    in mask_to_equalize will all fall between 0 and number_of_bins
    
    returns the equalized data
    """

    out = out if out is not None else numpy.zeros_like(data)
    # if we don't have a valid mask, use the mask of what we should be equalizing
    if valid_data_mask is None:
        valid_data_mask = mask_to_equalize
    
    # calculate some useful numbers for our tile math
    total_rows = data.shape[0]
    total_cols = data.shape[1]
    tile_size = int((local_radius_px * 2.0) + 1.0)
    row_tiles = int(total_rows / tile_size) if (total_rows % tile_size is 0) else int(total_rows / tile_size) + 1
    col_tiles = int(total_cols / tile_size) if (total_cols % tile_size is 0) else int(total_cols / tile_size) + 1
    
    # an array of our distribution functions for equalization
    all_cumulative_dist_functions = [ [ ] ]
    # an array of our bin information for equalization
    all_bin_information           = [ [ ] ]
    
    # loop through our tiles and create the histogram equalizations for each one
    for num_row_tile in range(row_tiles) :
        
        # make sure we have enough rows available to store info on this next row of tiles
        if len(all_cumulative_dist_functions) <= num_row_tile :
            all_cumulative_dist_functions.append( [ ] )
        if len(all_bin_information)           <= num_row_tile :
            all_bin_information          .append( [ ] )
        
        # go through each tile in this row and calculate the equalization
        for num_col_tile in range(col_tiles) :
            
            # calculate the range for this tile (min is inclusive, max is exclusive)
            min_row = num_row_tile * tile_size
            max_row = min_row + tile_size
            min_col = num_col_tile * tile_size
            max_col = min_col + tile_size
            
            # for speed of calculation, pull out the mask of pixels that should be used to calculate the histogram
            mask_valid_data_in_tile  = valid_data_mask[min_row:max_row, min_col:max_col]
            
            # if we have any valid data in this tile, calculate a histogram equalization for this tile
            # (note: even if this tile does no fall in the mask_to_equalize, it's histogram may be used by other tiles)
            cumulative_dist_function, temp_bins = None, None
            if mask_valid_data_in_tile.any():
                
                # use all valid data in the tile, so separate sections will blend cleanly
                temp_valid_data = data[min_row:max_row, min_col:max_col][mask_valid_data_in_tile]
                temp_valid_data = temp_valid_data[temp_valid_data >= 0] # TEMP, testing to see if negative data is messing everything up
                # limit the contrast by only considering data within a certain range of the average
                if std_mult_cutoff is not None :
                    avg               = numpy.mean(temp_valid_data)
                    std               = numpy.std (temp_valid_data)
                    # limit our range to avg +/- std_mult_cutoff*std; e.g. the default std_mult_cutoff is 4.0 so about 99.8% of the data
                    concervative_mask = (temp_valid_data < (avg + std*std_mult_cutoff)) & (temp_valid_data > (avg - std*std_mult_cutoff))
                    temp_valid_data   = temp_valid_data[concervative_mask]
                
                # if we are taking the log of our data, do so now
                if do_log_scale :
                    temp_valid_data = numpy.log(temp_valid_data + log_offset)
                
                # do the histogram equalization and get the resulting distribution function and bin information
                if temp_valid_data.size > 0 :
                    cumulative_dist_function, temp_bins = _histogram_equalization_helper (temp_valid_data, number_of_bins, clip_limit=clip_limit, slope_limit=slope_limit)
            
            # hang on to our equalization related information for use later
            all_cumulative_dist_functions[num_row_tile].append(cumulative_dist_function)
            all_bin_information          [num_row_tile].append(temp_bins)
    
    # get the tile weight array so we can use it to interpolate our data
    tile_weights = _calculate_weights(tile_size)
    
    # now loop through our tiles and linearly interpolate the equalized versions of the data
    for num_row_tile in range(row_tiles) :
        for num_col_tile in range(col_tiles) :
            
            # calculate the range for this tile (min is inclusive, max is exclusive)
            min_row = num_row_tile * tile_size
            max_row = min_row + tile_size
            min_col = num_col_tile * tile_size
            max_col = min_col + tile_size
            
            # for convenience, pull some of these tile sized chunks out
            temp_all_data = data[min_row:max_row, min_col:max_col].copy()
            temp_mask_to_equalize = mask_to_equalize[min_row:max_row, min_col:max_col]
            temp_all_valid_data_mask = valid_data_mask[min_row:max_row, min_col:max_col]

            # if we have any data in this tile, calculate our weighted sum
            if temp_mask_to_equalize.any():
                if do_log_scale:
                    temp_all_data[temp_all_valid_data_mask] = numpy.log(temp_all_data[temp_all_valid_data_mask] + log_offset)
                temp_data_to_equalize = temp_all_data[temp_mask_to_equalize]
                temp_all_valid_data = temp_all_data[temp_all_valid_data_mask]

                # a place to hold our weighted sum that represents the interpolated contributions
                # of the histogram equalizations from the surrounding tiles
                temp_sum = numpy.zeros_like(temp_data_to_equalize)

                # how much weight were we unable to use because those tiles fell off the edge of the image?
                unused_weight = numpy.zeros(temp_data_to_equalize.shape, dtype=tile_weights.dtype)

                # loop through all the surrounding tiles and process their contributions to this tile
                for weight_row in range(3):
                    for weight_col in range(3):
                        # figure out which adjacent tile we're processing (in overall tile coordinates instead of relative to our current tile)
                        calculated_row = num_row_tile - 1 + weight_row
                        calculated_col = num_col_tile - 1 + weight_col
                        tmp_tile_weights = tile_weights[weight_row, weight_col][numpy.where(temp_mask_to_equalize)]
                        
                        # if we're inside the tile array and the tile we're processing has a histogram equalization for us to use, process it
                        if ( (calculated_row >= 0) and (calculated_row < row_tiles) and
                             (calculated_col >= 0) and (calculated_col < col_tiles) and
                             (all_bin_information[calculated_row][calculated_col] is not None) and
                             (all_cumulative_dist_functions[calculated_row][calculated_col] is not None)) :
                            
                            # equalize our current tile using the histogram equalization from the tile we're processing
                            temp_equalized_data = numpy.interp(temp_all_valid_data,
                                                               all_bin_information[calculated_row][calculated_col][:-1],
                                                               all_cumulative_dist_functions[calculated_row][calculated_col])
                            temp_equalized_data = temp_equalized_data[numpy.where(temp_mask_to_equalize[temp_all_valid_data_mask])]
                            
                            # add the contribution for the tile we're processing to our weighted sum
                            temp_sum += (temp_equalized_data * tmp_tile_weights)
                            
                        else : # if the tile we're processing doesn't exist, hang onto the weight we would have used for it so we can correct that later
                            unused_weight -= tmp_tile_weights

                # if we have unused weights, scale our values to correct for that
                if unused_weight.any():
                    # TODO, if the mask masks everything out this will be a zero!
                    temp_sum /= unused_weight + 1

                # now that we've calculated the weighted sum for this tile, set it in our data array
                out[min_row:max_row, min_col:max_col][temp_mask_to_equalize] = temp_sum
                
                """
                # TEMP, test without using weights
                data[min_row:max_row, min_col:max_col][temp_mask_to_equalize] = numpy.interp(temp_data_to_equalize,
                                                                                             all_bin_information          [num_row_tile  ][num_col_tile][:-1],
                                                                                             all_cumulative_dist_functions[num_row_tile  ][num_col_tile])
                """

    # if we were asked to, normalize our data to be between zero and one, rather than zero and number_of_bins
    if do_zerotoone_normalization :
        _linear_normalization_from_0to1 (out, mask_to_equalize, number_of_bins)
    
    return out

def _histogram_equalization_helper (valid_data, number_of_bins, clip_limit=None, slope_limit=None) :
    """
    calculate the simplest possible histogram equalization, using only valid data
    
    returns the cumulative distribution function and bin information
    """
    
    # bucket all the selected data using numpy's histogram function
    temp_histogram, temp_bins = numpy.histogram(valid_data, number_of_bins)
    
    # if we have a clip limit and we should do our clipping before building the cumulative distribution function, clip off our histogram
    if (clip_limit is not None) :
        
        # clip our histogram and remember how much we removed
        pixels_to_clip_at            = int(clip_limit * (valid_data.size / float(number_of_bins)))
        mask_to_clip                 = temp_histogram > clip_limit
        num_bins_clipped             = sum(mask_to_clip)
        num_pixels_clipped           = sum(temp_histogram[mask_to_clip]) - (num_bins_clipped * pixels_to_clip_at)
        temp_histogram[mask_to_clip] = pixels_to_clip_at
    
    # calculate the cumulative distribution function
    cumulative_dist_function  = temp_histogram.cumsum()
    
    # if we have a clip limit and we should do our clipping after building the cumulative distribution function, clip off our cdf
    if (slope_limit is not None) :
        
        # clip our cdf and remember how much we removed
        pixel_height_limit       = int(slope_limit * (valid_data.size / float(number_of_bins)))
        cumulative_excess_height = 0
        num_clipped_pixels       = 0
        weight_metric            = numpy.zeros(cumulative_dist_function.shape, dtype=float)
        
        for pixel_index in range(1, cumulative_dist_function.size) :
            
            current_pixel_count = cumulative_dist_function[pixel_index]
            
            diff_from_acceptable      = (current_pixel_count - cumulative_dist_function[pixel_index-1] -
                                              pixel_height_limit - cumulative_excess_height)
            if diff_from_acceptable < 0:
                weight_metric[pixel_index] = abs(diff_from_acceptable)
            cumulative_excess_height += max( diff_from_acceptable, 0)
            cumulative_dist_function[pixel_index] = current_pixel_count - cumulative_excess_height
            num_clipped_pixels = num_clipped_pixels + cumulative_excess_height
    
    # now normalize the overall distribution function
    cumulative_dist_function  = (number_of_bins - 1) * cumulative_dist_function / cumulative_dist_function[-1]
    
    # return what someone else will need in order to apply the equalization later
    return cumulative_dist_function, temp_bins

def _calculate_weights (tile_size) :
    """
    calculate a weight array that will be used to quickly bilinearly-interpolate the histogram equalizations
    tile size should be the width and height of a tile in pixels
    
    returns a 4D weight array, where the first 2 dimensions correspond to the grid of where the tiles are
    relative to the tile being interpolated
    """
    
    # we are essentially making a set of weight masks for an ideal center tile that has all 8 surrounding tiles available
    
    # create our empty template tiles
    template_tile = numpy.zeros((3, 3, tile_size, tile_size), dtype=numpy.float32)
    
    """
    # TEMP FOR TESTING, create a weight tile that does no interpolation
    template_tile[1,1] = template_tile[1,1] + 1.0
    """
    
    # for ease of calculation, figure out the index of the center pixel in a tile
    # and how far that pixel is from the edge of the tile (in pixel units)
    center_index = int(tile_size / 2)
    center_dist  =     tile_size / 2.0
    
    # loop through each pixel in the tile and calculate the 9 weights for that pixel
    # were weights for a pixel are 0.0 they are not set (since the template_tile
    # starts out as all zeros)
    for row in range(tile_size) :
        for col in range(tile_size) :
            
            vertical_dist   = abs(center_dist - row) # the distance from our pixel to the center of our tile, vertically
            horizontal_dist = abs(center_dist - col) # the distance from our pixel to the center of our tile, horizontally
            
            # pre-calculate which 3 adjacent tiles will affect our tile
            # (note: these calculations aren't quite right if center_index equals the row or col)
            horizontal_index = 0 if col < center_index else 2
            vertical_index   = 0 if row < center_index else 2
            
            # if this is the center pixel, we only need to use it's own tile for it
            if (row is center_index) and (col is center_index) :
                
                # all of the weight for this pixel comes from it's own tile
                template_tile[1,1][row, col] = 1.0
                
            # if this pixel is in the center row, but is not the center pixel
            # we're going to need to linearly interpolate it's tile and the
            # tile that is horizontally nearest to it
            elif (row is     center_index)    and (col is not center_index) :
                
                # linear interp horizontally
                
                beside_weight = horizontal_dist / tile_size               # the weight from the adjacent tile
                local_weight  = (tile_size - horizontal_dist) / tile_size # the weight from this tile
                
                # set the weights for the two relevant tiles
                template_tile[1, 1]               [row, col] = local_weight
                template_tile[1, horizontal_index][row, col] = beside_weight
                
            # if this pixel is in the center column, but is not the center pixel
            # we're going to need to linearly interpolate it's tile and the
            # tile that is vertically nearest to it
            elif (row is not center_index)    and (col is     center_index) :
                
                # linear interp vertical
                
                beside_weight = vertical_dist / tile_size               # the weight from the adjacent tile
                local_weight  = (tile_size - vertical_dist) / tile_size # the weight from this tile
                
                # set the weights for the two relevant tiles
                template_tile[1,              1][row, col]   = local_weight
                template_tile[vertical_index, 1][row, col]   = beside_weight
                
            # if the pixel is in one of the four quadrants that are above or below the center
            # row and column, we need to bilinearly interpolate it between the nearest four tiles
            else:
                
                # bilinear interpolation
                
                local_weight      = ((tile_size - vertical_dist) / tile_size) * ((tile_size - horizontal_dist) / tile_size) # the weight from this tile
                vertical_weight   = ((            vertical_dist) / tile_size) * ((tile_size - horizontal_dist) / tile_size) # the weight from the vertically   adjacent tile
                horizontal_weight = ((tile_size - vertical_dist) / tile_size) * ((            horizontal_dist) / tile_size) # the weight from the horizontally adjacent tile
                diagonal_weight   = ((            vertical_dist) / tile_size) * ((            horizontal_dist) / tile_size) # the weight from the diagonally   adjacent tile
                
                # set the weights for the four relevant tiles
                template_tile[1,              1,                row, col] = local_weight
                template_tile[vertical_index, 1,                row, col] = vertical_weight
                template_tile[1,              horizontal_index, row, col] = horizontal_weight
                template_tile[vertical_index, horizontal_index, row, col] = diagonal_weight
    
    
    # return the weights for an ideal center tile
    return template_tile

def _linear_normalization_from_0to1 (data, mask, theoretical_max, theoretical_min=0, message="    normalizing equalized data to fit in 0 to 1 range") :
                                                                                            #"    normalizing DNB data into 0 to 1 range") :
    """
    do a linear normalization so all data is in the 0 to 1 range. This is a sloppy but fast calculation that relies on parameters
    giving it the correct theoretical current max and min so it can scale the data accordingly.
    """
    
    log.debug(message)
    if (theoretical_min is not 0) :
        data[mask]      = data[mask]      - theoretical_min
        theoretical_max = theoretical_max - theoretical_min
    data[mask] = data[mask] / theoretical_max

def main():
    print "Command line interface not implemented. If you wish to rescale from the command line use rescale.py."

if __name__ == "__main__":
    sys.exit(main())

