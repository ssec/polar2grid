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
    numpy.multiply(img, 100.0, img)
    numpy.sqrt(img, out=img)
    numpy.multiply(img, 255, img)
    numpy.round(img, out=img)
    return img

M_SCALES = {
        1  : passive_scale,
        2  : passive_scale,
        3  : passive_scale,
        4  : passive_scale,
        5  : sqrt_scale,
        6  : passive_scale,
        7  : passive_scale,
        8  : passive_scale,
        9  : passive_scale,
        10 : passive_scale,
        11 : passive_scale,
        12 : passive_scale,
        13 : passive_scale,
        14 : passive_scale,
        15 : passive_scale,
        16 : passive_scale
        }

I_SCALES = {
        1  : passive_scale,
        2  : passive_scale,
        3  : passive_scale,
        4  : passive_scale,
        5  : passive_scale,
        }

NB_SCALES = {
        }

SCALES = {
        "M"  : M_SCALES,
        "I"  : I_SCALES,
        "NB" : NB_SCALES
        }

def rescale(img, kind="M", band=5):
    if kind not in SCALES:
        log.error("Unknown kind %s, only know %r" % (kind, SCALES.keys()))
        return -1

    kind_scale = SCALES[kind]

    if band not in kind_scale:
        log.error("Unknown band %s for kind %s, only know %r" % (band, kind, kind_scale.keys()))
        return -1

    scale_func = kind_scale[band]
    img = scale_func(img, kind=kind, band=band)
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

