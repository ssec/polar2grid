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
from polar2grid.core.dtype import dtype_to_str, dtype2range

import os
import sys
import logging
import numpy

log = logging.getLogger(__name__)


def mask_helper(img, fill_value):
    if numpy.isnan(fill_value):
        return numpy.isnan(img)
    else:
        return img == fill_value


def linear_scale(img, m, b, **kwargs):
    log.debug("Running 'linear_scale' with (m: %f, b: %f)..." % (m, b))

    if m != 1:
        numpy.multiply(img, m, img)
    if b != 0:
        numpy.add(img, b, img)
    
    return img


def unlinear_scale(img, m, b, **kwargs):
    log.debug("Running 'unlinear_scale' with (m: %f, b: %f)..." % (m, b))

    # Faster than assigning
    if b != 0:
        numpy.subtract(img, b, img)
    if m != 1:
        numpy.divide(img, m, img)

    return img


def passive_scale(img, **kwargs):
    """When there is no rescaling necessary or it hasn't
    been determined yet, use this function.
    """
    log.debug("Running 'passive_scale'...")
    return img


def linear_flexible_scale(img, min_out, max_out, min_in=None, max_in=None, flip=False, **kwargs):
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
    log.debug("Running 'linear_flexible_scale' with (min_out: %f, max_out: %f)..." % (min_out, max_out))

    min_in = numpy.nanmin(img) if min_in is None else min_in
    max_in = numpy.nanmax(img) if max_in is None else max_in
    if min_in == max_in:
        # Data doesn't differ...at all
        log.warning("Data does not differ (min/max are the same), can not scale properly")
        max_in = min_in + 1.0
    log.debug("Input minimum: %f, Input maximum: %f" % (min_in, max_in))

    if flip:
        m = (min_out - max_out) / (max_in - min_in)
        b = max_out - m * min_in
    else:
        m = (max_out - min_out) / (max_in - min_in)
        b = min_out - m * min_in
    log.debug("Linear parameters: m=%f, b=%f", m, b)

    numpy.multiply(img, m, img)
    numpy.add(img, b, img)

    return img


def sqrt_scale(img, min_out, max_out, inner_mult=None, outer_mult=None, min_in=0.0, max_in=1.0, **kwargs):
    """Square root enhancement

    Note that any values below zero are clipped to zero before calculations.

    Default behavior (for regular 8-bit scaling):
        new_data = sqrt(data * 100.0) * 25.5
    """
    log.debug("Running 'sqrt_scale'...")
    if min_out != 0 and min_in != 0:
        raise RuntimeError("'sqrt_scale' does not support a `min_out` or `min_in` not equal to 0")
    inner_mult = inner_mult if inner_mult is not None else (100.0 / max_in)
    outer_mult = outer_mult if outer_mult is not None else max_out / numpy.sqrt(inner_mult)
    img[img < 0] = 0  # because < 0 cant be sqrted

    if inner_mult != 1:
        numpy.multiply(img, inner_mult, img)

    numpy.sqrt(img, out=img)

    if outer_mult != 1:
        numpy.multiply(img, outer_mult, img)

    numpy.round(img, out=img)

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

lookup_tables = {
    "crefl": pw_255_lookup_table,
}


def lookup_scale(img, max_out, m, b, table_name="crefl", **kwargs):
    log.debug("Running 'lookup_scale'...")
    lut = lookup_tables[table_name]
    img = linear_scale(img, m, b)
    numpy.clip(img, 0, lut.shape[0]-1, out=img)
    img = lut[img.astype(numpy.uint32)]
    img *= max_out  # scale to correct output range (technically not correct since assumes min_out is 0
    return img


def brightness_temperature_scale(img, threshold, min_in, max_in, min_out, max_out,
                                 threshold_out=None, units="kelvin", **kwargs):
    """Brightness temperature scaling is a piecewise function with two linear sub-functions.

    Temperatures less than `threshold` are scaled linearly from `threshold_out` to `max_out`. Temperatures greater than
    or equal to `threshold` are scaled linearly from `min_out` to `threshold_out`.

    In previous versions, this function took the now calculated linear parameters, ``m`` and ``b`` for
    each sub-function. For historical documentation here is how these were converted to the current method:

        equation 1: middle_file_value = low_max - (low_mult * threshold)
        equation 2: max_out = low_max - (low_mult * min_temp)
        equation #1 - #2: threshold_out - max_out = low_mult * threshold + low_mult * min_temp = low_mult (threshold + min_temp) => low_mult = (threshold_out - max_out) / (min_temp - threshold)
        equation 3: middle_file_value = high_max - (high_mult * threshold)
        equation 4: min_out = high_max - (high_mult * max_temp)
        equation #3 - #4: (middle_file_value - min_out) = high_mult * (max_in - threshold)

    :param units: If 'celsius', convert 'in' parameters from kelvin to degrees celsius before performing calculations.

    """
    log.debug("Running 'bt_scale'...")
    if units == "celsius":
        min_in -= 273.15
        max_in -= 273.15
        threshold -= 273.15
    threshold_out = threshold_out if threshold_out is not None else (176 / 255.0) * max_out
    low_factor = (threshold_out - max_out) / (min_in - threshold)
    low_offset = max_out + (low_factor * min_in)
    high_factor = (threshold_out - min_out) / (max_in - threshold)
    high_offset = min_out + (high_factor * max_in)
    log.debug("BT scale: threshold_out=%f; low_factor=%f; low_offset=%f; high_factor=%f; high_offset=%f",
              threshold_out, low_factor, low_offset, high_factor, high_offset)

    high_idx = img >= threshold
    low_idx = img < threshold
    img[high_idx] = high_offset - (high_factor * img[high_idx])
    img[low_idx] = low_offset - (low_factor * img[low_idx])
    return img


def linear_brightness_temperature_scale(img, min_out, max_out, min_in=None, max_in=None,
                                        units="kelvin", flip=True, **kwargs):
    """Linearly scale brightness temperatures.

    :param units: If 'celsius', convert 'in' parameters from kelvin to degrees celsius before performing calculations.
    """
    if units == "celsius":
        min_in -= 273.15
        max_in -= 273.15
    return linear_flexible_scale(img, min_out, max_out, min_in, max_in, flip=flip, **kwargs)


def temperature_difference_scale(img, min_in, max_in, min_out, max_out, **kwargs):
    """Scale data linearly. Then clip the data to the following values based on `min_out` and `max_out`:

        - clip_min = min_out + 5
        - clip_max = 0.8 * (max_out - min_out)

    Values outside of the threshold are set to -1 from the 'clip_min' and +1 from the 'clip_max'. The data is scaled
    linearly to the clip limits.

    Basic behavior is to put -10 to 10 range into 5 to 205 with clipped data set to 4 and 206.
    """
    log.debug("Running 'temperature_difference_scale'...")
    clip_min = min_out + 5
    clip_max = 0.8 * (max_out - min_out)
    img = linear_flexible_scale(img, clip_min, clip_max, min_in=min_in, max_in=max_in)
    img[img < clip_min] = clip_min - 1
    img[img > clip_max] = clip_max + 1
    return img


def lst_scale(img, min_out, max_out, min_in, max_in, fill_out, **kwargs):
    """Linearly scale data to +-5 of the output limits. Clip higher values and mask lower values.

    linear scale from a to b range to c to d range; if greater than b, set to d instead of scaling, if less than a, set to fill value x instead of scaling
    for winter/normal (a, b) is (233.2K, 322.0K) and (c, d) is (5, 245)
    for summer        (a, b) is (255.4K, 344.3K) and (c, d) is (5, 245)
    """
    new_min = min_out + 5
    new_max = max_out - 5
    img = linear_flexible_scale(img, new_min, new_max, min_in, max_in, **kwargs)
    img[img > new_max] = new_max
    img[img < new_min] = fill_out
    
    return img


def ctt_scale(img, min_out, max_out, min_in, max_in, flip=True, **kwargs):
    """The original cloud top temperature scaling.

    The original was for unsigned 8-bit files from 10 to 250.
    """
    img = linear_flexible_scale(img, min_out+10, max_out-5, min_in, max_in, flip=flip, **kwargs)
    numpy.clip(img, min_out+10, max_out-5, img)
    return img


def ndvi_scale(img, min_out, max_out, min_in=-1.0, max_in=1.0, threshold=0.0, threshold_out=None, **kwargs):
    """Given NDVI data, clip it to the range `min_in` (default -1) to `max_in` (default 1),
    then linearly scale values below `threshold` (default 0) to between `min_out` and `threshold_out`. Then linearly scale
    values greater than or equal to `threshold` between `threshold_out` and `max_out`. The `threshold_out` value
    defaults to the value at about 19.2% of the output range (calculated as 49/255 * `max_out`).

    """
    # clip to the min_before max_before range
    numpy.clip(img, min_in, max_in, img)

    # make two section masks
    negative_mask = (img < threshold)
    pos_zero_mask = (img >= threshold)
    threshold_out = threshold_out if threshold_out is not None else 49 / 255.0 * max_out
    log.debug("Running NDVI: Low data (%f -> %f to %f -> %f); High data (%f -> %f to %f -> %f).",
              min_in, threshold, min_out, threshold_out,
              threshold, max_in, threshold_out, max_out)
    img[negative_mask] = linear_flexible_scale(img[negative_mask], min_out, threshold_out, min_in, threshold)
    img[pos_zero_mask] = linear_flexible_scale(img[pos_zero_mask], threshold_out, max_out, threshold, max_in)

    return img


class Rescaler(roles.INIConfigReader):
    # Fields used to match a product object to it's correct configuration
    id_fields = (
        "product_name",
        "data_type",
        "data_kind",
        "satellite",
        "instrument",
        "grid_name",
        "inc_by_one",
    )

    rescale_methods = {
        'linear': linear_flexible_scale,
        'linear_basic': linear_scale,
        'brightness_temperature': brightness_temperature_scale,
        'linear_brightness_temperature': linear_brightness_temperature_scale,
        'sqrt': sqrt_scale,
        'temperature_difference': temperature_difference_scale,
        'raw': passive_scale,
        'lst': lst_scale,
        'ctt': ctt_scale,
        'ndvi': ndvi_scale,
        'unlinear': unlinear_scale,
        'lookup': lookup_scale,
    }

    def __init__(self, *rescale_configs, **kwargs):
        kwargs["section_prefix"] = kwargs.get("section_prefix", "rescale_")
        # kwargs["default_keyword_type"] = lambda: float
        # set defaults for the config reader (these will get passed to the scaling function)
        # kwargs["fill_in"] = kwargs.get("fill_in", "nan")
        # kwargs["fill_out"] = kwargs.get("fill_out", "nan")
        kwargs["float_kwargs"] = self._float_kwargs()
        kwargs["boolean_kwargs"] = self._bool_kwargs()
        log.info("Loading rescale configuration files:\n\t%s", "\n\t".join(rescale_configs))
        super(Rescaler, self).__init__(*rescale_configs, **kwargs)

    def _bool_kwargs(self):
        args = {"clip", "flip"}
        return args

    def _float_kwargs(self):
        """Get the names of the arguments that will be passed to the scaling functions.
        """
        import inspect
        args = set([a for func in self.rescale_methods.values() for a in inspect.getargspec(func).args])
        # caller provided arguments
        args.remove("img")
        args.remove("flip")  # boolean
        args.remove("table_name")  # string
        args.add("min_out")
        args.add("max_out")
        return args

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
        kwargs["data_type"] = dtype_to_str(data_type)
        kwargs["inc_by_one"] = inc_by_one
        rescale_options = self.get_config_options(**kwargs)
        inc_by_one = rescale_options.pop("inc_by_one")
        if "method" not in rescale_options:
            log.error("No rescaling method found and no default method configured for %s", gridded_product["product_name"])
            raise ValueError("No rescaling method configured for %s" % (gridded_product["product_name"],))
        log.debug("Product %s found in rescale config: %r", gridded_product["product_name"], rescale_options)

        method = rescale_options.pop("method")
        rescale_func = self.rescale_methods[method]
        # if the configuration file didn't force these then provide a logical default
        clip = rescale_options.pop("clip", True)
        min_out, max_out = dtype2range[kwargs["data_type"]]
        rescale_options.setdefault("min_out", min_out)
        rescale_options.setdefault("max_out", max_out - 1 if inc_by_one else max_out)
        rescale_options.setdefault("units", gridded_product.get("units", "kelvin"))
        rescale_options["fill_out"] = fill_value

        try:
            log.debug("Scaling data with method %s and arguments %r", method, rescale_options)
            data = gridded_product.copy_array(read_only=False)
            good_data_mask = ~gridded_product.get_data_mask()
            good_data = data[good_data_mask]
            good_data = rescale_func(good_data, **rescale_options)

            # Note: If the output fill value is anything that is affected by clipping or incrementing then
            # certain scalings may fail if they decided some values could not be calculated
            if clip:
                log.debug("Clipping data between %f and %f", rescale_options["min_out"], rescale_options["max_out"])
                good_data = numpy.clip(good_data, rescale_options["min_out"], rescale_options["max_out"], out=good_data)

            data[good_data_mask] = good_data
            data[~good_data_mask] = fill_value

            if inc_by_one:
                log.debug("Incrementing data by 1 so 0 acts as a fill value")
                # need to recalculate mask here in case the rescaling method assigned some new fill values
                data[mask_helper(data, fill_value)] += 1
        except StandardError:
            log.error("Unexpected error during rescaling")
            raise


        log_level = logging.getLogger('').handlers[0].level or 0
        # Only perform this calculation if it will be shown, its very time consuming
        if log_level <= logging.DEBUG:
            try:
                if good_data_mask is None:
                    good_data_mask = ~gridded_product.get_data_mask("grid_data")
                log.debug("Data min: %f, max: %f" % (data[good_data_mask].min(), data[good_data_mask].max()))
            except StandardError:
                log.debug("Couldn't get min/max values for %s (all fill data?)", gridded_product["product_name"])

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

