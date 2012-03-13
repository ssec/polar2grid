"""Functions and mappings for taking rempapped VIIRS data and
rescaling it to a useable range from 0 to 255 to be compatible
and "pretty" with AWIPS.

WARNING: A scaling function is not guarenteed to not change the
original data array passed.  If fact, it is faster in most cases
to change the array in place.

Author: David Hoese,davidh,SSEC
"""
import os
import sys
import logging
import numpy

from adl_guidebook import K_REFLECTANCE,K_RADIANCE,K_BTEMP

log = logging.getLogger(__name__)

def _make_lin_scale(m, b):
    def linear_scale(img, *args, **kwargs):
        log.debug("Running 'linear_scale' with (m: %f, b: %f)..." % (m,b))
        # Faster than assigning
        numpy.multiply(img, m, img)
        numpy.add(img, b, img)
        return img
    return linear_scale

def passive_scale(img, *args, **kwargs):
    """When there is no rescaling necessary or it hasn't
    been determined yet, use this function.
    """
    log.debug("Running 'passive_scale'...")
    return img

def sqrt_scale(img, *args, **kwargs):
    log.debug("Running 'sqrt_scale'...")
    mask = img == -999
    img[mask] = 0 # For invalids because < 0 cant be sqrted
    print img.min(), img.max()
    numpy.multiply(img, 100.0, img)
    print img.min(), img.max()
    numpy.sqrt(img, out=img)
    print img.min(), img.max()
    numpy.multiply(img, 25.5, img)
    print img.min(), img.max()
    numpy.round(img, out=img)
    print img.min(), img.max()
    img[mask] = -999
    print img.min(), img.max()
    return img

def bt_scale(img, *args, **kwargs):
    log.debug("Running 'bt_scale'...")
    print img.min(),img.max()
    high_idx = img >= 242.0
    low_idx = img < 242.0
    z_idx = img == -999
    img[high_idx] = 660 - (2*img[high_idx])
    img[low_idx] = 418 - img[low_idx]
    img[z_idx] = -999
    print img.min(),img.max()
    return img

def dnb_scale(img, *args, **kwargs):
    """
    This scaling method uses histogram equalization to flatten the image levels across the day and night masks.
    The masks are expected to be passed as "day_mask" and "night_mask" in the kwargs for this method. 
    
    A histogram equalization will be performed separately for each of the two masks that's present in the kwargs.
    """

    log.debug("Running 'dnb_scale'...")
    
    if ("day_mask"   in kwargs) and (numpy.sum(kwargs["day_mask"])   > 0) :
        _histogram_equalization(img, kwargs["day_mask"  ])
    
    if ("night_mask" in kwargs) and (numpy.sum(kwargs["night_mask"]) > 0) :
        _histogram_equalization(img, kwargs["night_mask"])
    
    return img

def _histogram_equalization (data, mask_to_equalize, number_of_bins=256) :
    """
    Perform a histogram equalization on the data selected by mask_to_equalize.
    The data will be separated into number_of_bins levels of discrete values.
    
    Note: the data will be changed in place.
    """
    
    # bucket all the selected data using numpy's histogram function
    temp_histogram, temp_bins = numpy.histogram(data[mask_to_equalize], number_of_bins, normed=True)
    # calculate the cumulative distribution function
    cumulative_dist_function  = temp_histogram.cumsum()
    # now normalize the overall distribution function
    cumulative_dist_function  = (number_of_bins - 1) * cumulative_dist_function / cumulative_dist_function[-1]
    
    # linearly interpolate using the distribution function to get the new values
    data[mask_to_equalize] = numpy.interp(data[mask_to_equalize], temp_bins[:-1], cumulative_dist_function)
    
    return data

M_SCALES = {
        1  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        2  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        3  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        4  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        5  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        6  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        7  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        8  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        9  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        10 : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        11 : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        12 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale, K_BTEMP:bt_scale},
        13 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale, K_BTEMP:bt_scale},
        14 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale, K_BTEMP:bt_scale},
        15 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale, K_BTEMP:bt_scale},
        16 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale, K_BTEMP:bt_scale}
        }

I_SCALES = {
        1  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        2  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        3  : {K_REFLECTANCE:sqrt_scale, K_RADIANCE:passive_scale, K_BTEMP:passive_scale},
        4  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale, K_BTEMP:bt_scale},
        5  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale, K_BTEMP:bt_scale}
        }

DNB_SCALES = {
        0 : {K_REFLECTANCE:passive_scale, K_RADIANCE:dnb_scale, K_BTEMP:passive_scale}
        }

SCALES = {
        "M"  : M_SCALES,
        "I"  : I_SCALES,
        "DNB" : DNB_SCALES
        }

def rescale(img, kind="M", band=5, data_kind=K_RADIANCE, **kwargs):
    band = int(band) # If it came from a filename, it was a string

    if kind not in SCALES:
        log.error("Unknown kind %s, only know %r" % (kind, SCALES.keys()))
        raise ValueError("Unknown kind %s, only know %r" % (kind, SCALES.keys()))

    kind_scale = SCALES[kind]

    if band not in kind_scale:
        log.error("Unknown band %s for kind %s, only know %r" % (band, kind, kind_scale.keys()))
        raise ValueError("Unknown band %s for kind %s, only know %r" % (band, kind, kind_scale.keys()))

    dkind_scale = kind_scale[band]

    if data_kind not in dkind_scale:
        log.error("Unknown data kind %s for kind %s band %s" % (data_kind, kind, band))
        raise ValueError("Unknown data kind %s for kind %s band %s" % (data_kind, kind, band))

    scale_func = dkind_scale[data_kind]
    img = scale_func(img, kind=kind, band=band, data_kind=data_kind, **kwargs)
    return img

def rescale_and_write(img_file, output_file, *args, **kwargs):
    # TODO: Open img file
    img = None
    new_img = rescale(img, *args, **kwargs)
    # TODO: Write new_img to output_file

def main():
    import optparse
    usage = """%prog [options] <input.fbf_format> <output.fbf_format> <band>"""
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    options,args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])

    return rescale_and_write(*args)

if __name__ == "__main__":
    sys.exit(main())

