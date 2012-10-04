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

from polar2grid.core import K_REFLECTANCE,K_RADIANCE,K_BTEMP,K_FOG

import os
import sys
import logging
import numpy

log = logging.getLogger(__name__)

PERSISTENT_CONFIGS = {}
KNOWN_DATA_KINDS = {
        'reflectance' : K_REFLECTANCE,
        'radiance' : K_RADIANCE,
        'btemp' : K_BTEMP,
        'fog' : K_FOG
        }
# See KNOWN_RESCALE_KINDS below
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
    numpy.clip(img, 0, 255, out=img)
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
        K_REFLECTANCE : sqrt_scale,
        K_RADIANCE    : post_rescale_dnb,
        K_BTEMP       : bt_scale,
        K_FOG         : fog_scale
        }

PRESCALES = {
        K_REFLECTANCE : passive_scale,
        K_RADIANCE    : dnb_scale,
        K_BTEMP       : passive_scale,
        K_FOG         : passive_scale
        }

def prescale(img, kind="DNB", band="00", data_kind=K_REFLECTANCE, **kwargs):
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

def rescale_old(img, kind="I", band="01", data_kind=K_REFLECTANCE, **kwargs):
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

# Needs to be declared after all of the scaling functions
KNOWN_RESCALE_KINDS = {
        'sqrt' : sqrt_scale,
        'linear' : linear_scale, # TODO: Get from merge with ninjo
        'raw' : passive_scale,
        'btemp' : bt_scale
        }

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
            # Make sure we know the data_kind
            if parts[4] not in KNOWN_DATA_KINDS:
                log.error("Rescaling doesn't know the data kind '%s'" % parts[4])
                raise ValueError("Rescaling doesn't know the data kind '%s'" % parts[4])
            # Make sure we know the scale kind
            if parts[5] not in KNOWN_RESCALE_KINDS:
                log.error("Rescaling doesn't know the rescaling kind '%s'" % parts[5])
                raise ValueError("Rescaling doesn't know the rescaling kind '%s'" % parts[5])
            # TODO: Check argument lengths and maybe values per rescale kind 

            # Enter the information into the configs dict
            line_id = "_".join(x.lower() for x in parts[:5])
            config_entry = (KNOWN_RESCALE_KINDS[parts[5]], tuple(parts[6:]))
            PERSISTENT_CONFIGS[name][line_id] = config_entry
    except StandardError:
        # Clear out the bad config
        del PERSISTENT_CONFIGS[name]
        raise

    return True

def load_config(config_filename):
    """Load a rescaling configuration file for later use by the `rescale`
    function.
    """
    config_filename = os.path.realpath(config_filename)
    if config_filename in PERSISTENT_CONFIGS:
        return True

    config_file = open(config_filename, 'r')
    config_str = config_file.read()
    return load_config_str(config_filename, config_str)

def rescale(sat, instrument, kind, band, data_kind, data, config=None):
    """Function that uses previously loaded configuration files to choose
    how to rescale the provided data.  If the `config` keyword is not provided
    then a best guess will be made on how to rescale the data.  Usually this
    best guess is a 0-255 scaling based on the `data_kind`.
    """
    band_id = "_".join([sat, instrument, kind, band, data_kind])
    if config is not None and config not in PERSISTENT_CONFIGS:
        log.error("'rescale' was passed a configuration file that wasn't loaded yet")
        raise ValueError("'rescale' was passed a configuration file that wasn't loaded yet")
    if config is not None and band_id not in PERSISTENT_CONFIGS[config]:
        # TODO run default scaling functions
        pass
    else:
        # We know how to rescale using the onfiguration file
        pass

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

