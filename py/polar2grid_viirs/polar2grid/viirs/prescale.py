#!/usr/bin/env python
# encoding: utf-8
"""Functions for prescaling data.  Scaling that occurs after the raw
data is loaded, but before the data is provided to the user.  These
functions should not create any new bands (see `polar2grid.viirs.pseudo`),
but only modify data.

There is no interface currently defined for these functions; arguments and
returned values are up to the rest of the VIIRs frontend calling them.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2012
:license:      GNU GPLv3
"""

import numpy
from polar2grid.core.rescale import _local_histogram_equalization,_histogram_equalization
from polar2grid.core.constants import DEFAULT_FILL_VALUE
from polar2grid.core import Workspace

import os
import sys
import glob
import logging

log = logging.getLogger(__name__)

def dnb_scale(img, day_mask=None, mixed_mask=None, night_mask=None,
        new_dnb=False):
    """
    This scaling method uses histogram equalization to flatten the image
    levels across the day and night masks.  The masks are expected to be
    passed as `day_mask`, `mixed_mask`, and `night_mask` keyword arguments.
    They should be `None` if not used. 

    `mixed_mask` should be a python list of masks for any number of desired
    'levels' of distinction in the mixed data region.  Each mask in
    `mixed_mask` should have the same shape as the data and day and night
    masks.
    
    A histogram equalization will be performed separately for each of the
    three masks that's present (not `None`).
    """

    #log.debug("Running 'dnb_scale'...")
    if new_dnb:
        log.debug("Running NEW DNB scaling...")
    else:
        log.debug("Running OLD DNB scaling...")
    
    # a way to hang onto our result
    # because the equalization is done in place, this is needed so the input data isn't corrupted
    img_result = img.copy()
    
    # build a mask of all the valid data in the image
    allValidData = numpy.zeros(img.shape, dtype=bool) # by default we don't believe any data is good
    allValidData = allValidData | day_mask   if day_mask   is not None else allValidData
    allValidData = allValidData | night_mask if night_mask is not None else allValidData
    if mixed_mask is not None :
        for mixed in mixed_mask :
            allValidData = allValidData | mixed
    
    """
    # TEMP, this is for testing tiled histogram equalization across the whole image
    _local_histogram_equalization(img, allValidData, local_radius_px=200)
    """
    
    if day_mask is not None and (numpy.sum(day_mask)   > 0) :
        log.debug("  scaling DNB in day mask")
        temp_image = img.copy()
        if new_dnb:
            _local_histogram_equalization(temp_image, day_mask, valid_data_mask=allValidData, local_radius_px=200)
        else:
            _histogram_equalization(temp_image, day_mask)
        img_result[day_mask] = temp_image[day_mask]
    
    if mixed_mask is not None and (len(mixed_mask)     > 0) :
        log.debug("  scaling DNB in twilight mask")
        for mask in mixed_mask:
            temp_image = img.copy()
            if new_dnb:
                _local_histogram_equalization(temp_image, mask, valid_data_mask=allValidData, local_radius_px=100)
            else:
                _histogram_equalization(temp_image, mask)
            img_result[mask] = temp_image[mask]
    
    if night_mask is not None and (numpy.sum(night_mask) > 0) :
        log.debug("  scaling DNB in night mask")
        temp_image = img.copy()
        if new_dnb:
            _local_histogram_equalization(temp_image, night_mask, valid_data_mask=allValidData, local_radius_px=200)
        else:
            _histogram_equalization(temp_image, night_mask)
        img_result[night_mask] = temp_image[night_mask]
    
    return img_result

# XXX: Remove new_dnb when a method has been decided on
# XXX: It is just temporary
def run_dnb_scale(img_filepath, mode_filepath,
        new_dnb=False, fill_value=DEFAULT_FILL_VALUE):
    """A wrapper function for calling the prescaling function for dnb.
    This function will read the binary image data from ``img_filepath``
    as well as any other data that may be required to prescale the data
    correctly, such as day/night/twilight masks.

    :Parameters:
        img_filepath : str
            Filepath to the binary image swath data in FBF format
            (ex. ``image_I01.real4.6400.10176``).
        mode_filepath : str
            Filepath to the binary mode swath data in FBF format
            (ex. ``mode_I01.real4.6400.10176``).
    """
        
    img_attr = os.path.split(img_filepath)[1].split('.')[0]
    mode_attr = os.path.split(mode_filepath)[1].split('.')[0]

    # Rescale the image
    try:
        W = Workspace('.')
        img = getattr(W, img_attr)
        data = img.copy()
        log.debug("Data min: %f, Data max: %f" % (data.min(),data.max()))
    except StandardError:
        log.error("Could not open img file %s" % img_filepath)
        log.debug("Files matching %r" % glob(img_attr + "*"))
        raise

    scale_kwargs = {
            'new_dnb':new_dnb # XXX
            }
    try:
        mode_mask = getattr(W, mode_attr)
        # Only add parameters if they're useful
        if mode_mask.shape == data.shape:
            log.debug("Adding mode mask to rescaling arguments")
            HIGH = 100
            LOW = 88
            MIXED_STEP = HIGH - LOW
            good_mask = ~((img == fill_value) | (mode_mask == fill_value))
            scale_kwargs["night_mask"]    = (mode_mask >= HIGH) & good_mask
            scale_kwargs["day_mask"]      = (mode_mask <= LOW ) & good_mask
            scale_kwargs["mixed_mask"] = []
            steps = range(LOW, HIGH+1, MIXED_STEP)
            if steps[-1] >= HIGH: steps[-1] = HIGH
            steps = zip(steps, steps[1:])
            for i,j in steps:
                log.debug("Processing step %d to %d" % (i,j))
                tmp = (mode_mask >  i) & (mode_mask < j) & good_mask
                if numpy.sum(tmp) > 0:
                    log.debug("Adding step %d to %d" % (i,j))
                    scale_kwargs["mixed_mask"].append(tmp)
                del tmp
            del good_mask

        else:
            log.error("Mode shape is different than the data's shape (%s) vs (%s)" % (mode_mask.shape, data.shape))
            raise ValueError("Mode shape is different than the data's shape (%s) vs (%s)" % (mode_mask.shape, data.shape))
    except StandardError:
        log.error("Could not open mode mask file %s" % mode_filepath)
        log.debug("Files matching %r" % glob(mode_attr + "*"))
        raise

    try:
        rescaled_data = dnb_scale(data,
                **scale_kwargs)
        if (logging.getLogger('').handlers[0].level or 0) <= logging.DEBUG:
            log.debug("Data min: %f, Data max: %f" % (
                rescaled_data[ rescaled_data != fill_value ].min(),
                rescaled_data[ rescaled_data != fill_value ].max()
                ))
        rows,cols = rescaled_data.shape
        fbf_swath_var = "prescale_dnb"
        fbf_swath = "./%s.real4.%d.%d" % (fbf_swath_var, cols, rows)
        rescaled_data.tofile(fbf_swath)
    except StandardError:
        log.error("Unexpected error while rescaling data")
        log.debug("Rescaling error:", exc_info=1)
        raise

    return fbf_swath

