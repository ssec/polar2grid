#!/usr/bin/env python
# encoding: utf-8
"""Functions and mappings for taking rempapped VIIRS data and
rescaling it to a useable range from 0 to 255 to be compatible
and "pretty" with AWIPS.

:attention:
    A scaling function is not guarenteed to not change the
    original data array passed.  If fact, it is faster in most cases
    to change the array in place.

:author:       David Hoese (davidh)
:author:       Eva Schiffer (evas)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from polar2grid.core.constants import DKIND_REFLECTANCE,DKIND_RADIANCE,DKIND_BTEMP,DKIND_FOG,BKIND_I,BID_01,BKIND_DNB,NOT_APPLICABLE

import os
import sys
import logging
import numpy

log = logging.getLogger(__name__)
RESCALE_FILL = -999.0
PRESCALE_FILL = -999.0

def post_rescale_dnb(data):
    """Special case DNB rescaling that happens
    after the remapping (so just a 0-1 to 0-255 scaling.
    """
    log.debug("Running DNB rescaling from 0-1 to 0-255")
    # Don't need to worry about fills because they will be less than 0 anyway
    # XXX: Worry about fills if this is used outside of awips netcdf backend
    numpy.multiply(data, 255.0, out=data)
    return data

def _make_lin_scale(m, b):
    def linear_scale(img, *args, **kwargs):
        log.debug("Running 'linear_scale' with (m: %f, b: %f)..." % (m,b))
        # Faster than assigning
        numpy.multiply(img, m, img)
        numpy.add(img, b, img)
        return img
    return linear_scale

def ubyte_filter(img, *args, **kwargs):
    """Convert image data to a numpy array with dtype `numpy.uint8` and set
    values below zero to zero and values above 255 to 255.
    """
    large_idxs = numpy.nonzero(img > 255)
    small_idxs = numpy.nonzero(img < 0)
    img = img.astype(numpy.uint8)
    img[large_idxs] = 255
    img[small_idxs] = 0
    return img

def linear_scale(img, m, b, *args, **kwargs):
    log.debug("Running 'linear_scale' with (m: %f, b: %f)..." % (m,b))
    if "fill_in" in kwargs:
        fill_mask = numpy.nonzero(img == kwargs["fill_in"])

    numpy.multiply(img, m, img)
    numpy.add(img, b, img)

    if "fill_in" in kwargs:
        if "fill_out" in kwargs:
            img[fill_mask] = kwargs["fill_out"]
        else:
            img[fill_mask] = kwargs["fill_in"]

    return img

def unlinear_scale(img, m, b, *args, **kwargs):
    log.debug("Running 'unlinear_scale' with (m: %f, b: %f)..." % (m,b))
    if "fill_in" in kwargs:
        fill_mask = numpy.nonzero(img == kwargs["fill_in"])

    # Faster than assigning
    numpy.subtract(img, b, img)
    numpy.divide(img, m, img)

    if "fill_in" in kwargs:
        if "fill_out" in kwargs:
            img[fill_mask] = kwargs["fill_out"]
        else:
            img[fill_mask] = kwargs["fill_in"]

    return img

def passive_scale(img, *args, **kwargs):
    """When there is no rescaling necessary or it hasn't
    been determined yet, use this function.
    """
    log.debug("Running 'passive_scale'...")
    return img

def sqrt_scale(img, *args, **kwargs):
    log.debug("Running 'sqrt_scale'...")
    FILL = RESCALE_FILL
    mask = img == FILL
    img[mask] = 0 # For invalids because < 0 cant be sqrted
    numpy.multiply(img, 100.0, img)
    numpy.sqrt(img, out=img)
    numpy.multiply(img, 25.5, img)
    numpy.round(img, out=img)
    img[mask] = FILL
    return img

def bt_scale(img, *args, **kwargs):
    log.debug("Running 'bt_scale'...")
    FILL = RESCALE_FILL
    high_idx = img >= 242.0
    low_idx = img < 242.0
    z_idx = img == FILL
    img[high_idx] = 660 - (2*img[high_idx])
    img[low_idx] = 418 - img[low_idx]
    img[z_idx] = FILL
    return img

def fog_scale(img, *args, **kwargs):
    # Put -10 - 10 range into 5 - 205
    log.debug("Running 'fog_scale'...")
    FILL = RESCALE_FILL
    mask = img == FILL
    numpy.multiply(img, 10.0, out=img)
    numpy.add(img, 105.0, out=img)
    img[img < 5] = 4
    img[img > 205] = 206 
    img[mask] = FILL
    return img

def dnb_scale(img, *args, **kwargs):
    """
    This scaling method uses histogram equalization to flatten the image levels across the day and night masks.
    The masks are expected to be passed as "day_mask" and "night_mask" in the kwargs for this method. 
    
    A histogram equalization will be performed separately for each of the two masks that's present in the kwargs.
    """

    log.debug("Running 'dnb_scale'...")
    
    if ("day_mask"   in kwargs) and (numpy.sum(kwargs["day_mask"])   > 0) :
        log.debug("  scaling DNB in day mask")
        _histogram_equalization(img, kwargs["day_mask"  ])
    
    if ("mixed_mask"   in kwargs) and (len(kwargs["mixed_mask"])     > 0) :
        log.debug("  scaling DNB in twilight mask")
        for mask in kwargs["mixed_mask"]:
            _histogram_equalization(img, mask)
    
    if ("night_mask" in kwargs) and (numpy.sum(kwargs["night_mask"]) > 0) :
        log.debug("  scaling DNB in night mask")
        _histogram_equalization(img, kwargs["night_mask"])
    
    return img

def _histogram_equalization (data, mask_to_equalize, number_of_bins=1000, std_mult_cutoff=4.0, do_zerotoone_normalization=True) :
    """
    Perform a histogram equalization on the data selected by mask_to_equalize.
    The data will be separated into number_of_bins levels for equalization and
    outliers beyond +/- std_mult_cutoff*std will be ignored.
    
    If do_zerotoone_normalization is True the data selected by mask_to_equalize
    will be returned in the 0 to 1 range. Otherwise the data selected by
    mask_to_equalize will be returned in the 0 to number_of_bins range.
    
    Note: the data will be changed in place.
    """
    
    log.debug("    determining DNB data range for histogram equalization")
    avg = numpy.mean(data[mask_to_equalize])
    std = numpy.std (data[mask_to_equalize])
    # limit our range to +/- std_mult_cutoff*std; e.g. the default std_mult_cutoff is 4.0 so about 99.8% of the data
    concervative_mask = (data < (avg + std*std_mult_cutoff)) & (data > (avg - std*std_mult_cutoff)) & mask_to_equalize
    
    log.debug("    running histogram equalization")
    
    # bucket all the selected data using numpy's histogram function
    temp_histogram, temp_bins = numpy.histogram(data[concervative_mask], number_of_bins, normed=True)
    # calculate the cumulative distribution function
    cumulative_dist_function  = temp_histogram.cumsum()
    # now normalize the overall distribution function
    cumulative_dist_function  = (number_of_bins - 1) * cumulative_dist_function / cumulative_dist_function[-1]
    
    # linearly interpolate using the distribution function to get the new values
    data[mask_to_equalize] = numpy.interp(data[mask_to_equalize], temp_bins[:-1], cumulative_dist_function)
    
    # if we were asked to, normalize our data to be between zero and one, rather than zero and number_of_bins
    if do_zerotoone_normalization :
        log.debug("    normalizing DNB data into 0 to 1 range")
        data[mask_to_equalize] = data[mask_to_equalize] / number_of_bins
    
    return data

RESCALES = {
        DKIND_REFLECTANCE : sqrt_scale,
        DKIND_RADIANCE    : post_rescale_dnb,
        DKIND_BTEMP       : bt_scale,
        DKIND_FOG         : fog_scale
        }

PRESCALES = {
        DKIND_REFLECTANCE : passive_scale,
        DKIND_RADIANCE    : dnb_scale,
        DKIND_BTEMP       : passive_scale,
        DKIND_FOG         : passive_scale
        }

def prescale(img, kind=BKIND_DNB, band=NOT_APPLICABLE, data_kind=DKIND_REFLECTANCE, **kwargs):
    """Calls the appropriate scaling function based on the provided keyword
    arguments and returns the new array.

    :Parameters:
        img : numpy.ndarray
            2D Array of swath satellite imager data to be scaled
    :Keywords:
        kind : str
            Kind of band (ex. I or M or DNB)
        band : str
            Band number (ex. 01 or 00 for DNB)
        data_kind : str
            Constant from `polar2grid.core` representing the type of data
            being passed
        func : function pointer
            Specify the function to use to scale the data instead of the
            default
    """
    if "func" in kwargs:
        scale_func = kwargs["func"]
    elif data_kind not in PRESCALES:
        log.error("Unknown data kind %s for rescaling" % (data_kind))
        raise ValueError("Unknown data kind %s for rescaling" % (data_kind))
    else:
        scale_func = PRESCALES[data_kind]

    img = scale_func(img, kind=kind, band=band, data_kind=data_kind, **kwargs)
    return img

def rescale(img, kind=BKIND_I, band=BID_01, data_kind=DKIND_REFLECTANCE, **kwargs):
    """Calls the appropriate scaling function based on the provided keyword
    arguments and returns the new array.

    :Parameters:
        img : numpy.ndarray
            2D Array of remapped satellite imager data to be scaled
    :Keywords:
        kind : str
            Kind of band (ex. I or M or DNB)
        band : str
            Band number (ex. 01 or 00 for DNB)
        data_kind : str
            Constant from `polar2grid.core` representing the type of data
            being passed
        func : function pointer
            Specify the function to use to scale the data instead of the
            default
    """
    if "func" in kwargs:
        # A different scaling function was specified
        scale_func = kwargs["func"]
    else:
        if data_kind not in RESCALES:
            log.error("Unknown data kind %s for rescaling" % (data_kind))
            raise ValueError("Unknown data kind %s for rescaling" % (data_kind))
        scale_func = RESCALES[data_kind]

    img = scale_func(img, kind=kind, band=band, data_kind=data_kind, **kwargs)
    return img

def rescale_and_write(img_file, output_file, *args, **kwargs):
    from polar2grid.core import Workspace
    img_fn = os.path.split(img_file)[1]
    img_fbf_attr = img_fn.split(".")[0]
    try:
        W = Workspace(".")
        img_data = getattr(W, img_fbf_attr)
        # Need to copy the memory mapped array
        img_data = img_data.copy()
    except StandardError:
        log.error("Could not retrieve %s" % img_fbf_attr)
        raise

    log.debug("Rescaling img_file")
    rescale(img_data, *args, **kwargs)

    img_data.tofile(output_file)
    return 0

def main():
    import optparse
    usage = """%prog [options] <input.fbf_format> <output.fbf_format> <kind> <band> --datakind=DKIND_REFLECTANCE"""
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_option('--datakind', dest='data_kind', default=None,
            help="specify the data kind of the provided input file as a constant name (DKIND_REFLECTANCE, DKIND_BTEMP, DKIND_RADIANCE, DKIND_FOG)")
    options,args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])

    if options.data_kind is None or not options.data_kind.startswith("K_") or options.data_kind not in globals():
        log.error("%s is not a known constant for a data type, try DKIND_REFLECTANCE, DKIND_BTEMP, DKIND_RADIANCE, DKIND_FOG" % options.data_kind)
        return -1
    else:
        data_kind = globals()[options.data_kind]

    if len(args) != 4:
        log.error("Rescaling takes only 4 arguments")
        parser.print_help()
        return -1

    return rescale_and_write(args[0], args[1], kind=args[2], band=args[3], data_kind=data_kind)

if __name__ == "__main__":
    sys.exit(main())

