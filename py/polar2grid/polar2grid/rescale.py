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

from polar2grid.core.constants import DKIND_REFLECTANCE,DKIND_RADIANCE, \
        DKIND_BTEMP,DKIND_FOG,NOT_APPLICABLE,DEFAULT_FILL_VALUE

import os
import sys
import logging
import numpy

log = logging.getLogger(__name__)

# See KNOWN_RESCALE_KINDS below
DEFAULT_CONFIG_DIR = os.path.split(os.path.realpath(__file__))[0]
PERSISTENT_CONFIGS = {}

# FIXME: If we can require numpy 1.7 we can use the mask keyword in ufuncs
DEFAULT_FILL_IN  = DEFAULT_FILL_VALUE
DEFAULT_FILL_OUT = DEFAULT_FILL_VALUE

def _make_lin_scale(m, b):
    """Factory function to make a static linear scaling function
    """
    def linear_scale(img, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT):
        log.debug("Running 'linear_scale' with (m: %f, b: %f)..." % (m,b))
        # Faster than assigning
        numpy.multiply(img, m, img)
        numpy.add(img, b, img)
        return img
    return linear_scale

def ubyte_filter(img):
    """Convert image data to a numpy array with dtype `numpy.uint8` and set
    values below zero to zero and values above 255 to 255.
    """
    numpy.clip(img, 0, 255, out=img)
    img = img.astype(numpy.uint8)
    return img

def uint16_filter(img):
    """Convert image data to a numpy array with dtype `numpy.uint16` and set
    values below zero to zero and values above 65535 to 65535.
    """
    numpy.clip(img, 0, 65535, out=img)
    img = img.astype(numpy.uint16)
    return img

def linear_scale(img, m, b, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT):
    log.debug("Running 'linear_scale' with (m: %f, b: %f)..." % (m,b))

    fill_mask = numpy.nonzero(img == fill_in)

    numpy.multiply(img, m, img)
    numpy.add(img, b, img)

    img[fill_mask] = fill_out

    return img

def unlinear_scale(img, m, b, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT):
    log.debug("Running 'unlinear_scale' with (m: %f, b: %f)..." % (m,b))
    fill_mask = numpy.nonzero(img == fill_in)

    # Faster than assigning
    numpy.subtract(img, b, img)
    numpy.divide(img, m, img)

    img[fill_mask] = fill_out

    return img

def passive_scale(img, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT):
    """When there is no rescaling necessary or it hasn't
    been determined yet, use this function.
    """
    log.debug("Running 'passive_scale'...")
    return img

def sqrt_scale(img, inner_mult, outer_mult, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT):
    log.debug("Running 'sqrt_scale'...")
    mask = img == fill_in
    img[mask] = 0 # For invalids because < 0 cant be sqrted
    numpy.multiply(img, inner_mult, img)
    numpy.sqrt(img, out=img)
    numpy.multiply(img, outer_mult, img)
    numpy.round(img, out=img)
    img[mask] = fill_out
    return img

def bt_scale_c(img, threshold, high_max, high_mult, low_max, low_mult, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT):
    """
    this is a version of the brightness temperature scaling that is intended to work for data in celsius
    """
    log.debug("Converting image data to Kelvin...")
    
    not_fill_mask = img != fill_in
    img[not_fill_mask] = img[not_fill_mask] + 273.15
    
    return bt_scale (img, threshold, high_max, high_mult, low_max, low_mult, fill_in=fill_in, fill_out=fill_out)
    

# this method is intended to work on brightness temperatures in Kelvin
def bt_scale(img, threshold, high_max, high_mult, low_max, low_mult, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT):
    log.debug("Running 'bt_scale'...")
    high_idx = img >= threshold
    low_idx = img < threshold
    z_idx = img == fill_in
    img[high_idx] = high_max - (high_mult*img[high_idx])
    img[low_idx] = low_max - (low_mult*img[low_idx])
    img[z_idx] = fill_out
    return img

def fog_scale(img, m, b, floor, floor_val, ceil, ceil_val, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT):
    """Scale data linearly. Then clip the data to `floor` and `ceil`,
    but instead of a usual clipping set the lower clipped values to
    `floor_val` and the upper clipped values to `ceil_val`.
    """
    
    # Put -10 - 10 range into 5 - 205
    log.debug("Running 'fog_scale'...")
    mask = img == fill_in
    numpy.multiply(img, m, out=img)
    numpy.add(img, b, out=img)
    img[img < floor] = floor_val
    img[img > ceil] = ceil_val
    img[mask] = fill_out
    return img

def dnb_scale(img, day_mask, mixed_mask, night_mask, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT):
    """
    This scaling method uses histogram equalization to flatten the image levels across the day and night masks.
    The masks are expected to be passed as "day_mask" and "night_mask" in the kwargs for this method. 
    
    A histogram equalization will be performed separately for each of the two masks that's present in the kwargs.
    """

    log.debug("Running 'dnb_scale'...")
    
    if day_mask is not None and (numpy.sum(day_mask)   > 0) :
        log.debug("  scaling DNB in day mask")
        _histogram_equalization(img, day_mask)
    
    if mixed_mask is not None and (len(mixed_mask)     > 0) :
        log.debug("  scaling DNB in twilight mask")
        for mask in mixed_mask:
            _histogram_equalization(img, mask)
    
    if night_mask is not None and (numpy.sum(night_mask) > 0) :
        log.debug("  scaling DNB in night mask")
        _histogram_equalization(img, night_mask)
    
    return img

# linear scale from a to b range to c to d range; if greater than b, set to d instead of scaling, if less than a, set to fill value x instead of scaling
# for winter/normal (a, b) is (233.2K, 322.0K) and (c, d) is (5, 245)
# for summer        (a, b) is (255.4K, 344.3K) and (c, d) is (5, 245)
def lst_scale (data, min_before, max_before, min_after, max_after, fill_in=DEFAULT_FILL_VALUE, fill_out=DEFAULT_FILL_VALUE) :
    """
    Given LST data with valid values in the range min_before to max_before (the data may leave this range, but all you want to keep is that range),
    linearly scale from min_before, max_before to min_after, max_after. Any values that fall below the minimum will be set to the fill value. Any values
    that fall above the maximum will be set to max_after. Values that already equal the fill value will be left as fill data.
    """
    
    # make a mask of our fill data
    not_fill_data = data != fill_in
    
    # get rid of anything below the minimum
    not_fill_data = not_fill_data & (data >= min_before)
    data[~not_fill_data] = fill_in
    
    # linearly scale the non-fill data
    data[not_fill_data] -= min_before
    data[not_fill_data] /= (max_before - min_before)
    data[not_fill_data] *= (max_after  - min_after)
    data[not_fill_data] += min_after
    
    # set values that are greater than the max down to the max
    too_high = not_fill_data & (data > max_after)
    data[too_high] = max_after
    
    # swap out the fill value
    data[data == fill_in] = fill_out
    
    return data

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

# Needs to be declared after all of the scaling functions
KNOWN_RESCALE_KINDS = {
        'sqrt' :   sqrt_scale,
        'linear' : linear_scale,
        'raw' :    passive_scale,
        'btemp' :  bt_scale,
        'btemp_c': bt_scale_c,
        'lst':     lst_scale
        }

# DEFAULTS
RESCALE_FOR_KIND = {
        DKIND_RADIANCE    : (linear_scale, (255.0,0)),
        DKIND_REFLECTANCE : (sqrt_scale,   (100.0, 25.5)),
        DKIND_BTEMP       : (bt_scale,     (242.0,660.0,2,418.0,1)),
        DKIND_FOG         : (fog_scale,    (10.0,105.0,5,4,205,206))
        }

def _create_config_id(sat, instrument, kind, band, data_kind):
    return "_".join([sat.lower(), instrument.lower(), kind.lower(), (band or "").lower(), data_kind.lower()])

def unload_config(name):
    """Shouldn't be needed, but just in case
    """
    if name not in PERSISTENT_CONFIGS:
        log.warning("'%s' rescaling config was never loaded" % name)
        return
    del PERSISTENT_CONFIGS[name]

def load_config_str(name, config_str):
    """Just in case I want to have a config file stored as a string in
    the future.

    >>> config_str = "#skip this comment\\nnpp,viirs,i,01,reflectance,sqrt,100.0,25.5"
    >>> load_config_str("test_config", config_str)
    True
    >>> config_bad1 = "#skip\\n\\n\\nsat,,empty_inst,field,radiance,linear,"
    >>> load_config_str("test_config", config_bad1) # should be fine because same name
    True
    >>> load_config_str("test_config_bad1", config_bad1)
    Traceback (most recent call last):
        ...
    AssertionError: Field 1 can not be empty
    >>> assert "test_config_bad1" not in PERSISTENT_CONFIGS
    >>> assert "test_config" in PERSISTENT_CONFIGS

    >>> config_bad2 = "#skip\\n\\n\\nnpp,viirs,i,01,fake,linear,"
    >>> load_config_str("test_config_bad2", config_bad2)
    Traceback (most recent call last):
        ...
    ValueError: Rescaling doesn't know the data kind 'fake'
    >>> config_bad3 = "#skip\\n\\n\\nnpp,viirs,i,01,radiance,fake,"
    >>> load_config_str("test_config_bad3", config_bad3)
    Traceback (most recent call last):
        ...
    ValueError: Rescaling doesn't know the rescaling kind 'fake'
    >>> assert "test_config_bad2" not in PERSISTENT_CONFIGS
    >>> assert "test_config_bad3" not in PERSISTENT_CONFIGS
    >>> assert "test_config" in PERSISTENT_CONFIGS
    """
    # Don't load a config twice
    if name in PERSISTENT_CONFIGS:
        return True

    # Get rid of trailing new lines and commas
    config_lines = [ line.strip(",\n") for line in config_str.split("\n") ]
    # Get rid of comment lines and blank lines
    config_lines = [ line for line in config_lines if line and not line.startswith("#") and not line.startswith("\n") ]
    # Check if we have any useful lines
    if not config_lines:
        log.warning("No non-comment lines were found in '%s'" % name)
        return False

    PERSISTENT_CONFIGS[name] = {}

    # Used in configuration reader
    KNOWN_DATA_KINDS = {
        'reflectance' : DKIND_REFLECTANCE,
        'radiance'    : DKIND_RADIANCE,
        'btemp'       : DKIND_BTEMP,
        'fog'         : DKIND_FOG,
        # if they copy the constants
        DKIND_REFLECTANCE : DKIND_REFLECTANCE,
        DKIND_RADIANCE    : DKIND_RADIANCE,
        DKIND_BTEMP       : DKIND_BTEMP,
        DKIND_FOG         : DKIND_FOG
        }
    try:
        # Parse config lines
        for line in config_lines:
            parts = line.split(",")
            if len(parts) < 6:
                log.error("Rescale config line needs at least 6 columns '%s' : '%s'" % (name,line))
                raise ValueError("Rescale config line needs at least 6 columns '%s'" % (name,line))

            # Verify that each identifying portion is valid
            for i in range(6):
                assert parts[i],"Field %d can not be empty" % i
                # polar2grid demands lowercase fields
                parts[i] = parts[i].lower()

            # Convert band if none
            if parts[3] == '' or parts[3] == "none":
                parts[3] = NOT_APPLICABLE
            # Make sure we know the data_kind
            if parts[4] not in KNOWN_DATA_KINDS:
                log.error("Rescaling doesn't know the data kind '%s'" % parts[4])
                raise ValueError("Rescaling doesn't know the data kind '%s'" % parts[4])
            parts[4] = KNOWN_DATA_KINDS[parts[4]]
            # Make sure we know the scale kind
            if parts[5] not in KNOWN_RESCALE_KINDS:
                log.error("Rescaling doesn't know the rescaling kind '%s'" % parts[5])
                raise ValueError("Rescaling doesn't know the rescaling kind '%s'" % parts[5])
            parts[5] = KNOWN_RESCALE_KINDS[parts[5]]
            # TODO: Check argument lengths and maybe values per rescale kind 

            # Enter the information into the configs dict
            line_id = _create_config_id(*parts[:5])
            config_entry = (parts[5], tuple(float(x) for x in parts[6:]))
            PERSISTENT_CONFIGS[name][line_id] = config_entry
    except StandardError:
        # Clear out the bad config
        del PERSISTENT_CONFIGS[name]
        raise

    return True

def load_config(config_filename, config_name=None):
    """Load a rescaling configuration file for later use by the `rescale`
    function.

    If the config isn't an absolute path, it checks the current directory,
    and if the config can't be found there it is assumed to be relative to
    the package structure. So entering just the filename will look in the
    default rescaling configuration location (the package root) for the
    filename provided.
    """
    # the name used in the actual configuration dictionary
    if config_name is None: config_name = config_filename

    if not os.path.isabs(config_filename):
        cwd_config = os.path.join(os.path.curdir, config_filename)
        if os.path.exists(cwd_config):
            config_filename = cwd_config
        else:
            config_filename = os.path.join(DEFAULT_CONFIG_DIR, config_filename)
    config_filename = os.path.realpath(config_filename)

    log.debug("Using rescaling configuration '%s'" % (config_filename,))

    if config_filename in PERSISTENT_CONFIGS:
        return True

    config_file = open(config_filename, 'r')
    config_str = config_file.read()
    return load_config_str(config_name, config_str)

def rescale(sat, instrument, kind, band, data_kind, data, config=None,
            fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT):
    """Function that uses previously loaded configuration files to choose
    how to rescale the provided data.  If the `config` keyword is not provided
    then a best guess will be made on how to rescale the data.  Usually this
    best guess is a 0-255 scaling based on the `data_kind`.
    """
    log_level = logging.getLogger('').handlers[0].level or 0
    band_id = _create_config_id(sat, instrument, kind, band, data_kind)

    if config is not None and config not in PERSISTENT_CONFIGS:
        log.error("rescaling was passed a configuration file that wasn't loaded yet: '%s'" % (config,))
        raise ValueError("rescaling was passed a configuration file that wasn't loaded yet: '%s'" % (config,))

    if config is None or band_id not in PERSISTENT_CONFIGS[config]:
        # Run the default scaling functions
        log.debug("Config ID '%s' was not found in '%r'" % (band_id,PERSISTENT_CONFIGS[config].keys()))
        log.info("Running default rescaling method for kind: %s, band: %s" % (kind,band))
        if data_kind not in RESCALE_FOR_KIND:
            log.error("No default rescaling is set for data of kind %s" % data_kind)
            raise ValueError("No default rescaling is set for data of kind %s" % data_kind)
        rescale_func,rescale_args = RESCALE_FOR_KIND[data_kind]
    else:
        # We know how to rescale using the onfiguration file
        log.info("'%s' was found in the rescaling configuration" % (band_id))
        rescale_func,rescale_args = PERSISTENT_CONFIGS[config][band_id]
    
    # use key word args for the fill values
    kwargs = {"fill_in": fill_in, "fill_out": fill_out }
    
    log.debug("Using rescale arguments: %r" % (rescale_args,))
    data = rescale_func(data, *rescale_args, **kwargs)
    
    # Only perform this calculation if it will be shown, its very time consuming
    if log_level <= logging.DEBUG:
        log.debug("Data min: %f, max: %f" % (data.min(),data.max()))

    return data

def main():
    from argparse import ArgumentParser
    description="""
Run polar2grid rescaling via the command line.  This is not the preferred
way to do production level rescaling, but is useful for testing.
"""
    parser = ArgumentParser(description=description)
    parser.add_argument('--doctest', dest="doctest", action="store_true",
            help="run document tests")
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, args.verbosity)])

    if args.doctest:
        import doctest
        return doctest.testmod()

    print "Command line interface not implemented yet"
    parser.print_help()

if __name__ == "__main__":
    sys.exit(main())

