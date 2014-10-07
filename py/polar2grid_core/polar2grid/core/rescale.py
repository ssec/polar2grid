#!/usr/bin/env python
# encoding: utf-8
"""Functions and mappings for taking rempapped polar-orbitting data and
rescaling it to a useable range for the backend using the data, usually a
0-255 8-bit range or a 0-65535 16-bit range.

:attention:
    A scaling function is not guarenteed to not change the
    original data array passed.  If fact, it is faster in most cases
    to change the array in place.

:author:       David Hoese (davidh)
:author:       Eva Schiffer (evas)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2013
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

from .constants import *
from . import roles
from polar2grid.core.dtype import dtype_to_str

import os
import sys
import logging
import numpy

log = logging.getLogger(__name__)

# Default fills for individual functions, see Rescaler and RescalerRole for
# other defaults
DEFAULT_FILL_IN  = DEFAULT_FILL_VALUE
DEFAULT_FILL_OUT = DEFAULT_FILL_VALUE


def mask_helper(img, fill_value):
    if numpy.isnan(fill_value):
        return numpy.isnan(img)
    else:
        return img == fill_value


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

def linear_scale(img, m, b, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT, **kwargs):
    log.debug("Running 'linear_scale' with (m: %f, b: %f)..." % (m,b))
    
    fill_mask = numpy.nonzero(img == fill_in)
    
    numpy.multiply(img, m, img)
    numpy.add(img, b, img)
    
    img[fill_mask] = fill_out
    
    return img

def unlinear_scale(img, m, b, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT, **kwargs):
    log.debug("Running 'unlinear_scale' with (m: %f, b: %f)..." % (m,b))
    fill_mask = numpy.nonzero(img == fill_in)

    # Faster than assigning
    numpy.subtract(img, b, img)
    numpy.divide(img, m, img)

    img[fill_mask] = fill_out

    return img

def passive_scale(img, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT, **kwargs):
    """When there is no rescaling necessary or it hasn't
    been determined yet, use this function.
    """
    log.debug("Running 'passive_scale'...")
    return img


linear_flexible_scale_kwargs = dict(min_out=float, max_out=float, min_in=float, max_in=float, clip=int,
                                    fill_in=float, fill_out=float)
def linear_flexible_scale(img, min_out, max_out, min_in=None, max_in=None, clip=0, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT, **kwargs):
    """Flexible linear scaling by specifying what you want output, not the parameters of the linear equation.

    This scaling function stops humans from doing math...let the computers do it.

    - If you aren't sure what the valid limits of your data are, only specify 
        the min and max output values. The input minimum and maximum will be
        computed. Note that this could add a considerable amount of time to
        the calculation.
    - If you know the limits, specify the output and input ranges.
    - If you want to flip the data range (ex. -16 to 40 data becomes 237 to 0
        data) then specify the ranges as needed (ex. min_out=237, max_out=0,
        min_in=-16, max_in=40). The flip happens automatically.
    - If the data needs to be clipped to the output range, specify 1 or 0 for
        the "clip" keyword. Note that most backends will do this to fit the
        data type of the output format.
    """
    log.debug("Running 'linear_flexible_scale' with (min_out: %f, max_out: %f..." % (min_out,max_out))
    fill_mask = img == fill_in

    min_in = numpy.nanmin(img[~fill_mask]) if min_in is None else min_in
    max_in = numpy.nanmax(img[~fill_mask]) if max_in is None else max_in
    if min_in == max_in:
        # Data doesn't differ...at all
        log.warning("Data does not differ (min/max are the same), can not scale properly")
        max_in = min_in + 1.0
    log.debug("Input minimum: %f, Input maximum: %f" % (min_in,max_in))

    m = (max_out - min_out) / (max_in - min_in)
    b = min_out - m * min_in

    numpy.multiply(img, m, img)
    numpy.add(img, b, img)

    if clip:
        if min_out < max_out:
            numpy.clip(img, min_out, max_out, out=img)
        else:
            numpy.clip(img, max_out, min_out, out=img)

    img[fill_mask] = fill_out

    return img

def sqrt_scale(img, inner_mult, outer_mult, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT, **kwargs):
    """Square root enhancement

    Note that any values below zero are clipped to zero before calculations.
    """
    log.debug("Running 'sqrt_scale'...")
    mask = img == fill_in
    img[ img < 0 ] = 0 # because < 0 cant be sqrted
    numpy.multiply(img, inner_mult, img)
    numpy.sqrt(img, out=img)
    numpy.multiply(img, outer_mult, img)
    numpy.round(img, out=img)
    img[mask] = fill_out
    return img

pw_255_lookup_table = numpy.array([  0,   3,   7,  10,  14,  18,  21,  25,  28,  32,  36,  39,  43,
        46,  50,  54,  57,  61,  64,  68,  72,  75,  79,  82,  86,  90,
        91,  93,  95,  96,  98, 100, 101, 103, 105, 106, 108, 110, 111,
       113, 115, 116, 118, 120, 121, 123, 125, 126, 128, 130, 131, 133,
       135, 136, 138, 140, 140, 141, 142, 143, 143, 144, 145, 146, 147,
       147, 148, 149, 150, 150, 151, 152, 153, 154, 154, 155, 156, 157,
       157, 158, 159, 160, 161, 161, 162, 163, 164, 164, 165, 166, 167,
       168, 168, 169, 170, 171, 171, 172, 173, 174, 175, 175, 176, 176,
       177, 177, 178, 178, 179, 179, 180, 180, 181, 181, 182, 182, 183,
       183, 184, 184, 185, 185, 186, 186, 187, 187, 188, 188, 189, 189,
       190, 191, 191, 192, 192, 193, 193, 194, 194, 195, 195, 196, 196,
       197, 197, 198, 198, 199, 199, 200, 200, 201, 201, 202, 202, 203,
       203, 204, 204, 205, 205, 206, 207, 207, 208, 208, 209, 209, 210,
       210, 211, 211, 212, 212, 213, 213, 214, 214, 215, 215, 216, 216,
       217, 217, 218, 218, 219, 219, 220, 220, 221, 221, 222, 223, 223,
       224, 224, 225, 225, 226, 226, 227, 227, 228, 228, 229, 229, 230,
       230, 231, 231, 232, 232, 233, 233, 234, 234, 235, 235, 236, 236,
       237, 237, 238, 239, 239, 240, 240, 241, 241, 242, 242, 243, 243,
       244, 244, 245, 245, 246, 246, 247, 247, 248, 248, 249, 249, 250,
       250, 251, 251, 252, 252, 253, 253, 254, 255], dtype=numpy.float32)

lookup_tables = [pw_255_lookup_table]

def lookup_scale(img, m, b, table_idx=0, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT, **kwargs):
    log.debug("Running 'lookup_scale'...")
    lut = lookup_tables[table_idx]
    mask = img == fill_in
    img = linear_scale(img, m, b, fill_in=fill_in, fill_out=fill_out)
    numpy.clip(img, 0, lut.shape[0]-1, out=img)
    img[mask] = fill_out
    img[~mask] = lut[img[~mask].astype(numpy.uint32)]
    return img

def bt_scale_c(img, threshold, high_max, high_mult, low_max, low_mult, clip_min=None, clip_max=None, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT, **kwargs):
    """
    this is a version of the brightness temperature scaling that is intended to work for data in celsius
    """
    log.debug("Converting image data to Kelvin...")
    
    not_fill_mask = img != fill_in
    img[not_fill_mask] = img[not_fill_mask] + 273.15
    
    return bt_scale(img, threshold, high_max, high_mult, low_max, low_mult, clip_min=None, clip_max=None, fill_in=fill_in, fill_out=fill_out, **kwargs)
    

# this method is intended to work on brightness temperatures in Kelvin
bt_scale_kwargs = dict(threshold=float, high_max=float, high_mult=float, low_max=float, low_mult=float,
                       clip_min=float, clip_max=float,
                       fill_in=float, fill_out=float)
def bt_scale(img, threshold, high_max, high_mult, low_max, low_mult, clip_min=None, clip_max=None, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT, **kwargs):
    log.debug("Running 'bt_scale'...")
    bad_mask = mask_helper(img, fill_in)
    good_img = img[~bad_mask]
    # print good_img, good_img.shape, numpy.isnan(good_img).all()
    print bad_mask.shape, good_img.shape
    high_idx = good_img >= threshold
    low_idx = good_img < threshold
    good_img[high_idx] = high_max - (high_mult*good_img[high_idx])
    good_img[low_idx] = low_max - (low_mult*good_img[low_idx])
    if clip_min is not None and clip_max is not None:
        log.debug("Clipping data in 'bt_scale' to '%f' and '%f'" % (clip_min, clip_max))
        numpy.clip(good_img, clip_min, clip_max, out=good_img)
    img[~bad_mask] = good_img
    img[bad_mask] = fill_out
    return img

# this method is intended to work on brightness temperatures in Kelvin
### DEPRECATED ###
def bt_scale_linear(image,
                    max_in,      min_in,
                    min_out=1.0, max_out=255.0,
                    fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT, **kwargs):
    """
    This method scales the data, reversing range of values so that max_in becomes min_out and
    min_in becomes max_out. The scaling is otherwise linear. Any data with a value of fill_in
    in the original image will be set to fill_out in the final image.
    """
    log.debug("Running 'bt_scale_linear'...")
    log.warning("DEPRECATION: Please use 'linear_flex' instead of 'bt_linear' for rescaling")
    log.warning("Arguments for bt_linear (A,B,C,D) become (C,D,A,B) for linear_flex")

    return linear_flexible_scale(min_out, max_out, max_in, min_in, clip=1)

def fog_scale(img, m, b, floor, floor_val, ceil, ceil_val, fill_in=DEFAULT_FILL_IN, fill_out=DEFAULT_FILL_OUT, **kwargs):
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

# linear scale from a to b range to c to d range; if greater than b, set to d instead of scaling, if less than a, set to fill value x instead of scaling
# for winter/normal (a, b) is (233.2K, 322.0K) and (c, d) is (5, 245)
# for summer        (a, b) is (255.4K, 344.3K) and (c, d) is (5, 245)
def lst_scale (data, min_before, max_before, min_after, max_after, fill_in=DEFAULT_FILL_VALUE, fill_out=DEFAULT_FILL_VALUE, **kwargs):
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

def ndvi_scale (data,
                low_section_multiplier, high_section_multiplier, high_section_offset,
                min_before, max_before,
                min_after, max_after,
                fill_in=DEFAULT_FILL_VALUE, fill_out=DEFAULT_FILL_VALUE, **kwargs):
    """
    Given NDVI data,
    clip it to the range min_before to max_before,
    then scale any negative values using the equation::

                        (1.0 - abs(value)) * low_section_multiplier

    and scale anything from zero to max_before with the equation::

                        (value * high_section_multiplier) + high_section_offset

    clip it to the range min_after to max_after
    """
    
    # mask out fill data
    not_fill_data = data != fill_in
    
    # clip to the min_before max_before range
    data[(data < min_before) & not_fill_data] = min_before
    data[(data > max_before) & not_fill_data] = max_before
    
    # make two section masks
    negative_mask = (data <  0.0) & not_fill_data
    pos_zero_mask = (data >= 0.0) & not_fill_data
    
    # scale the negative values
    data[negative_mask] = (data[negative_mask] + 1.0) * low_section_multiplier
    
    # scale the rest of the values
    data[pos_zero_mask] = (data[pos_zero_mask] * high_section_multiplier) + high_section_offset
    
    # clip to the min_after to max_after range
    data[(data < min_after) & not_fill_data] = min_after
    data[(data > max_after) & not_fill_data] = max_after
    
    # swap out the fill value
    data[data == fill_in] = fill_out
    
    return data

class Rescaler2(roles.INIConfigReader):
    # Fields used to match a product object to it's correct configuration
    id_fields = (
        "product_name",
        "data_type",
        "satellite",
        "instrument",
        "grid_name",
        "inc_by_one",
    )

    rescale_methods = {
        'linear_flex': (linear_flexible_scale, linear_flexible_scale_kwargs),
        'btemp': (bt_scale, bt_scale_kwargs),
        'sqrt'     : sqrt_scale,
        'linear'   : linear_scale,
        'unlinear' : unlinear_scale,
        'raw'      : passive_scale,
        'btemp_enh': linear_scale, # TODO, this probably shouldn't go here?
        'fog'      : fog_scale,
        'btemp_c'  : bt_scale_c,
        'lst'      : lst_scale,
        'ndvi'     : ndvi_scale,
        'distance' : passive_scale, # TODO, this is wrong... but we'll sort it out later?
        'percent'  : passive_scale, # TODO, this is wrong, find out what it should be
        'lookup'   : lookup_scale,
    }

    def __init__(self, *rescale_configs, **kwargs):
        kwargs["section_prefix"] = kwargs.get("section_prefix", "rescale_")
        log.info("Loading rescale configuration files:\n\t%s", "\n\t".join(rescale_configs))
        super(Rescaler2, self).__init__(*rescale_configs, **kwargs)

    def register_rescale_method(self, name, func, **kwargs):
        self.rescale_methods[name] = (func, kwargs)

    def rescale_product(self, gridded_product, data_type, inc_by_one=False, fill_value=None):
        """Rescale a gridded product based on how the rescaler is configured.

        The caller should know if it wants to increment the output data by 1 (`inc_by_one` keyword).

        :param data_type: Desired data type of the output data
        :param inc_by_one: After rescaling should 1 be added to all data values to leave the minumum value as the fill
        FUTURE: dec_by_one (mutually exclusive to inc_by_one)

        """
        all_meta = gridded_product["grid_definition"].copy()
        all_meta.update(**gridded_product)
        kwargs = dict((k, all_meta.get(k, None)) for k in self.id_fields)
        # we don't want the product's current data_type, we want what the output will be
        kwargs["data_type"] = data_type
        kwargs["inc_by_one"] = inc_by_one
        kwargs["data_type"] = dtype_to_str(kwargs["data_type"])
        rescale_options = self.get_config_options(**kwargs)
        inc_by_one = rescale_options.pop("inc_by_one")
        if "method" not in rescale_options:
            log.error("No rescaling method found and no default method configured for %s", gridded_product["product_name"])
            raise ValueError("No rescaling method configured for %s" % (gridded_product["product_name"],))
        log.debug("Product %s found in rescale config: %r", gridded_product["product_name"], rescale_options)

        data = gridded_product.copy_array("grid_data", read_only=False)
        rescale_func, arg_convs = self.rescale_methods[rescale_options.pop("method")]
        fill_in = gridded_product.get("fill_value", numpy.nan)
        rescale_options = dict((k, v(rescale_options[k])) for k, v in arg_convs.items() if k in rescale_options)
        data = rescale_func(data, fill_in=fill_in, fill_out=fill_value, **rescale_options)

        good_data_mask = None
        if inc_by_one:
            good_data_mask = ~gridded_product.get_data_mask("grid_data")
            data[good_data_mask] += 1

        log_level = logging.getLogger('').handlers[0].level or 0
        # Only perform this calculation if it will be shown, its very time consuming
        if log_level <= logging.DEBUG:
            try:
                if good_data_mask is None:
                    good_data_mask = ~gridded_product.get_data_mask("grid_data")
                log.debug("Data min: %f, max: %f" % (data[good_data_mask].min(),data[good_data_mask].max()))
            except StandardError:
                log.debug("Couldn't get min/max values for %s (all fill data?)", gridded_product["product_name"])

        return data


class Rescaler(roles.RescalerRole):
    DEFAULT_FILL_IN = DEFAULT_FILL_IN
    DEFAULT_FILL_OUT = DEFAULT_FILL_OUT

    @property
    def default_config_dir(self):
        """Return the default search path to find a configuration file if
        the configuration file provided is not an absolute path and the
        configuration filename was not found in the current working
        directory.
        """
        return os.path.split(os.path.realpath(__file__))[0]

    _known_rescale_kinds = {
                'sqrt'     :  sqrt_scale,
                'linear'   :  linear_scale,
                'unlinear' :  unlinear_scale,
                'raw'      :  passive_scale,
                'btemp'    :  bt_scale,
                'btemp_enh':  linear_scale, # TODO, this probably shouldn't go here?
                'fog'      :  fog_scale,
                'btemp_c'  :  bt_scale_c,
                'btemp_lin':  bt_scale_linear, # DEPRECATED: Use 'linear_flex'
                'lst'      :  lst_scale,
                'ndvi'     :  ndvi_scale,
                'distance' : passive_scale, # TODO, this is wrong... but we'll sort it out later?
                'percent'  : passive_scale, # TODO, this is wrong, find out what it should be
                'lookup'   : lookup_scale,
                'linear_flex' : linear_flexible_scale,
                }
    @property
    def known_rescale_kinds(self):
        # Override the role's rescale property
        return self._known_rescale_kinds

    def __init__(self, *args, **kwargs):
        self.inc_by_one = kwargs.pop("inc_by_one", False)
        super(Rescaler, self).__init__(*args, **kwargs)

    def __call__(self, sat, instrument, nav_set_uid, kind, band, data_kind, data,
            fill_in=None, fill_out=None, inc_by_one=None):
        """Function that uses previously loaded configuration files to choose
        how to rescale the provided data.  If the `config` keyword is not provided
        then a best guess will be made on how to rescale the data.  Usually this
        best guess is a 0-255 scaling based on the `data_kind`.

        `inc_by_one` is meant to make scaling easier in the case of data
        needing the lowest value of data to be the new fill value.  When this
        keyword is set to True (default uses value passed to __init__) it will
        add 1 to the scaled data excluding the invalid values.
        """
        log_level = logging.getLogger('').handlers[0].level or 0
        fill_in = fill_in or self.fill_in
        fill_out = fill_out or self.fill_out

        try:
            rescale_func,rescale_args = self.get_config_entry(sat, instrument, nav_set_uid, kind, band, data_kind)
            log.info("'%r' was found in the rescaling configuration" % ((sat, instrument, nav_set_uid, kind, band, data_kind),))
        except StandardError:
            log.error("'%r' was not found in rescaling configuration file" % ((sat, instrument, nav_set_uid, kind, band, data_kind),))
            raise

        # Only perform this calculation if it will be shown, its very time consuming
        if log_level <= logging.DEBUG:
            try:
                log.debug("Data min: %f, max: %f" % (data[ data != fill_in ].min(),data[ data != fill_in ].max()))
            except StandardError:
                log.debug("Couldn't get min/max values for %s %s (all fill data?)" % (kind,band))

        log.debug("Using rescale arguments: %r" % (rescale_args,))
        log.debug("Using fill in/out values: (%s,%s)" % (fill_in,fill_out))
        data = rescale_func(data, *rescale_args, fill_in=fill_in, fill_out=fill_out)

        # Increment by one to help the backend product
        inc_by_one = inc_by_one if inc_by_one is not None else self.inc_by_one
        if inc_by_one:
            data[ data != fill_out ] += 1

        # Only perform this calculation if it will be shown, its very time consuming
        if log_level <= logging.DEBUG:
            try:
                log.debug("Data min: %f, max: %f" % (data[ data != fill_out ].min(),data[ data != fill_out ].max()))
            except StandardError:
                log.debug("Couldn't get min/max values for %s %s (all fill data?)" % (kind,band))

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
    
    # FUTURE when this allows use of the rescale functions, also allow use of the histogram equalization
    # functions from histogram.py

if __name__ == "__main__":
    sys.exit(main())

