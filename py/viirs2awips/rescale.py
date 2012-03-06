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

from adl_guidebook import K_REFLECTANCE,K_RADIANCE#,K_TEMPERATURE

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
    print img.min(), img.max()
    # FIXME: Remove this line when unscaled stuff works
    #numpy.divide(img, 65536.0, img)
    print img.min(), img.max()
    numpy.multiply(img, 100.0, img)
    print img.min(), img.max()
    numpy.sqrt(img, out=img)
    print img.min(), img.max()
    numpy.multiply(img, 25.5, img)
    print img.min(), img.max()
    numpy.round(img, out=img)
    print img.min(), img.max()
    return img

M_SCALES = {
        1  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        2  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        3  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        4  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        5  : {K_REFLECTANCE:passive_scale, K_RADIANCE:sqrt_scale},
        6  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        7  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        8  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        9  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        10 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        11 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        12 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        13 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        14 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        15 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        16 : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale}
        }

I_SCALES = {
        1  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        2  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        3  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        4  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale},
        5  : {K_REFLECTANCE:passive_scale, K_RADIANCE:passive_scale}
        }

NB_SCALES = {
        }

SCALES = {
        "M"  : M_SCALES,
        "I"  : I_SCALES,
        "NB" : NB_SCALES
        }

def rescale(img, kind="M", band=5, data_kind=K_RADIANCE):
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
    img = scale_func(img, kind=kind, band=band, data_kind=data_kind)
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

