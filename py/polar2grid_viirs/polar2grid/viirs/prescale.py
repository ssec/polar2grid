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

import numpy
from polar2grid.core.histogram import local_histogram_equalization, histogram_equalization
from polar2grid.core.constants import DEFAULT_FILL_VALUE
from polar2grid.core import Workspace

# from mpl_toolkits.basemap import maskoceans

import os
import sys
from glob import glob
import logging

log = logging.getLogger(__name__)

DEFAULT_HIGH_ANGLE = 100
DEFAULT_LOW_ANGLE  = 88


def mask_helper(arr, fill_value):
    if numpy.isnan(fill_value):
        return numpy.isnan(arr)
    else:
        return arr == fill_value


def _make_day_night_masks(image, solarZenithAngle, fillValue,
                           highAngleCutoff=DEFAULT_HIGH_ANGLE, lowAngleCutoff=DEFAULT_LOW_ANGLE, stepsDegrees=None) :
    """
    given informaiton on the solarZenithAngle for each point,
    generate masks defining where the day, night, and mixed regions are
    
    optionally provide the highAngleCutoff and lowAngleCutoff that define
    the limits of the terminator region (if no cutoffs are given the
    DEFAULT_HIGH_ANGLE and DEFAULT_LOW_ANGLE will be used)
    
    optionally provide the stepsDegrees that define how many degrees each
    "mixed" mask in the terminator region should be (if no stepsDegrees is
    given, the whole terminator region will be one mask)
    """
    
    # if the caller didn't pass angle information, use the defaults
    highAngleCutoff = DEFAULT_HIGH_ANGLE if highAngleCutoff is None else highAngleCutoff
    lowAngleCutoff  = DEFAULT_LOW_ANGLE  if lowAngleCutoff  is None else lowAngleCutoff
    
    # if the caller passes None, we're only doing one step
    stepsDegrees = highAngleCutoff - lowAngleCutoff if stepsDegrees is None else stepsDegrees
    
    good_mask  = ~(mask_helper(image, fillValue) | mask_helper(solarZenithAngle, fillValue))
    night_mask = (solarZenithAngle >= highAngleCutoff) & good_mask
    day_mask   = (solarZenithAngle <= lowAngleCutoff ) & good_mask
    mixed_mask = [ ]
    steps = range(lowAngleCutoff, highAngleCutoff+1, stepsDegrees)
    if steps[-1] >= highAngleCutoff: steps[-1] = highAngleCutoff
    steps = zip(steps, steps[1:])
    for i,j in steps:
        log.debug("Processing step %d to %d" % (i,j))
        tmp = (solarZenithAngle >  i) & (solarZenithAngle < j) & good_mask
        if numpy.any(tmp):
            log.debug("Adding step %d to %d" % (i,j))
            log.debug("Points to process in this range: " + str(numpy.sum(tmp)))
            mixed_mask.append(tmp)
        del tmp
    
    return day_mask, mixed_mask, night_mask, good_mask


def _calculate_average_moon_illumination (moonIlluminatonFraction,
                                          lunarZenithAngle,
                                          goodDataMask,
                                          highAngleCutoff=None,
                                          lowAngleCutoff=None) :
    """
    This is probably not how we should handle differentiating our
    moon illumination information in the long run, but for now,
    condense the per pixel lunarZenithAngle information to an
    average moon illumination for the scene
    
    optionally give a highAngleCutoff and lowAngleCutoff to define
    the limits where the moon illumination will count for 100% value
    50% value and 0% value (if no cutoffs are given, the
    DEFAULT_HIGH_ANGLE and DEFAULT_LOW_ANGLE will be used)
    """
    
    # if the caller didn't pass angle information, use the defaults
    highAngleCutoff = DEFAULT_HIGH_ANGLE if highAngleCutoff is None else highAngleCutoff
    lowAngleCutoff  = DEFAULT_LOW_ANGLE  if lowAngleCutoff  is None else lowAngleCutoff
    
    # weight how much we count our illumination by where the moon is in the sky
    weightMask = numpy.ones(lunarZenithAngle.shape)
    weightMask[~goodDataMask] *= 0.0 # if we multiply by any invalid points they'll remain zero
    weightMask[lunarZenithAngle >= highAngleCutoff] *= 0.0 # the moon is behind the earth, these points don't see any moon
    weightMask[lunarZenithAngle <= lowAngleCutoff ] *= 1.0 # the moon is visble, so the illumination counts
    weightMask[(lunarZenithAngle < highAngleCutoff) & (lunarZenithAngle > lowAngleCutoff)] *= 0.5 # the moon is rising or setting, so count part of it
    
    # calculate our average by taking the total weighted illumination and dividing by the number of valid points
    totalWeight = numpy.sum(goodDataMask)
    totalValue  = numpy.sum(weightMask * moonIlluminatonFraction)
    avgIllum    = totalValue / totalWeight
    
    return avgIllum

# def _make_water_mask (latData, lonData, alsoMaskLakes=True) :
#     """
#     use mpl_toolkits.basemap.maskoceans to make a water mask
#
#     TODO, this is a pretty rough way to do this
#     """
#
#     temp = numpy.ones(latData.shape)
#     temp = maskoceans(lonData, latData, temp, inlands=alsoMaskLakes)
#
#     return temp.mask


def adaptive_dnb_scale(img, fillValue=DEFAULT_FILL_VALUE, solarZenithAngle=None, lunarZenithAngle=None,
                       moonIllumFraction=None, highAngleCutoff=None, lowAngleCutoff=None, waterMask=None, out=None):
    """This scaling method uses histogram equalization to flatten the image
    levels across the day and night regions.

    The img data will be separated into day, night, and mixed regions using the
    solarZenithAngle data. The highAngleCutoff and lowAngleCutoff define the
    points between the regions. If data points do not have a corresponding
    solarZenithAngle, they will be considered to be invalid data and set to
    fill values.

    The night region will be equalized using settings determined by the amount
    of moonlight in the scene (as determined by the moonIllumFraction and the lunarZenithAngle).

    FIXME: The below shouldn't need to be true
    If `out` is provided it must be a writable copy of the original DNB data.
    """
    if out is None:
        out = numpy.zeros_like(img)

    # build the day and night area masks
    log.debug("Generating day, night, and mixed region masks...")
    day_mask, mixed_mask, night_mask, good_mask = \
        _make_day_night_masks(img, solarZenithAngle,
                              fillValue,
                              highAngleCutoff=highAngleCutoff,
                              lowAngleCutoff=lowAngleCutoff)
    has_multi_times = (mixed_mask is not None) and (len(mixed_mask) > 0)
    night_water = None # a mask of water at night

    if day_mask is not None and (numpy.sum(day_mask)   > 0) :
        log.debug("  scaling DNB in day mask")
        if has_multi_times:
            local_histogram_equalization(img, day_mask, valid_data_mask=good_mask, local_radius_px=400, out=out)
        else:
            histogram_equalization(img, day_mask, out=out)

    if mixed_mask is not None and (len(mixed_mask)     > 0) :
        log.debug("  scaling DNB in twilight mask")
        for mask in mixed_mask:
            local_histogram_equalization(img, mask, valid_data_mask=good_mask, local_radius_px=100, out=out)

    if night_mask is not None and (numpy.sum(night_mask) > 0):
        log.debug("  scaling DNB in night mask")
        # log.debug("Moon Illumination, before angle weighting: " + str(moonIllumFraction))
        # weightedMoonIllumFract = _calculate_average_moon_illumination (moonIllumFraction,
        #                                                                lunarZenithAngle,
        #                                                                good_mask)
        # log.debug("Moon Illumination, after  angle weighting: " + str(weightedMoonIllumFract))
        #
        # # TODO, this should probably also be affected by whether or not there is a day mask
        # if weightedMoonIllumFract > 0.90 :
        #     if has_multi_times :
        #         local_histogram_equalization(img, night_mask, valid_data_mask=good_mask, local_radius_px=100, out=out)
        #     else :
        #         histogram_equalization(img, night_mask, out=out)
        # else :
        #     # FUTURE, for now we're not using the water mask
        #     #night_water = night_mask & waterMask
        #     #tmp_night_mask = night_mask & ~waterMask
        #     tmp_night_mask = night_mask
        #     if weightedMoonIllumFract > 0.25 :
        #         local_histogram_equalization(img, tmp_night_mask, valid_data_mask=good_mask, local_radius_px=200, out=out)
        #     elif weightedMoonIllumFract > 0.10 :
        #         local_histogram_equalization(img, tmp_night_mask, valid_data_mask=good_mask, local_radius_px=100, out=out)
        #     else :
        #         local_histogram_equalization(img, tmp_night_mask, valid_data_mask=good_mask, local_radius_px=50, out=out)

        histogram_equalization(img, night_mask, out=out)

    # if night_water is not None and (numpy.any(night_water)):
    #     log.debug ("  scaling DNB in night water mask")
    #     local_histogram_equalization(img, night_water, valid_data_mask=good_mask, local_radius_px=500, out=out)

    # set any data that's not in the good areas to fill
    out[~good_mask] = fillValue

    return out


def dnb_scale(img, fillValue=DEFAULT_FILL_VALUE, solarZenithAngle=None,
              highAngleCutoff=None, lowAngleCutoff=None, out=None):
    """
    This scaling method uses histogram equalization to flatten the image
    levels across the day and night regions.

    The img data will be separated into day, night, and mixed regions using the
    solarZenithAngle data. The highAngleCutoff and lowAngleCutoff define the
    points between the regions. If data points do not have a corresponding
    solarZenithAngle, they will be considered to be invalid data and set to
    fill values.
    """
    if out is None:
        out = numpy.zeros_like(img)

    # build the day and night area masks
    log.debug("Generating day, night, and mixed region masks...")
    day_mask, mixed_mask, night_mask, good_mask = \
                                       _make_day_night_masks(img, solarZenithAngle,
                                                             fillValue,
                                                             highAngleCutoff=highAngleCutoff,
                                                             lowAngleCutoff=lowAngleCutoff)
    # has_multi_times = (mixed_mask is not None) and (len(mixed_mask) > 0)

    if day_mask is not None and (numpy.sum(day_mask)   > 0) :
        log.debug("  scaling DNB in day mask")
        histogram_equalization(img, day_mask, out=out)

    if mixed_mask is not None and (len(mixed_mask)     > 0) :
        log.debug("  scaling DNB in twilight mask")
        for mask in mixed_mask:
            histogram_equalization(img, mask, out=out)

    if night_mask is not None and (numpy.sum(night_mask) > 0) :
        log.debug("  scaling DNB in night mask")
        histogram_equalization(img, night_mask, out=out)

    # set any data that's not in the good areas to fill
    out[~good_mask] = fillValue
    
    return out

