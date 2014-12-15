#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    December 2014
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""Common RGB compositors.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import numpy
from polar2grid.core import roles
from polar2grid.core.fbf import FileAppender

import os
import sys
import logging

LOG = logging.getLogger(__name__)


class RGBCompositor(roles.CompositorRole):
    def __init__(self, **kwargs):
        super(RGBCompositor, self).__init__(**kwargs)

    def shared_mask(self, gridded_scene, product_names, axis=0):
        return numpy.any([gridded_scene[pname].get_data_mask() for pname in product_names], axis=axis)

    def joined_array(self, gridded_scene, product_names):
        # the_stuff = [gridded_scene[pname].get_data_array() for pname in product_names]
        # print [x.shape for x in the_stuff]
        # return numpy.array(the_stuff)
        return numpy.array([gridded_scene[pname].get_data_array() for pname in product_names])

    def modify_scene(self, gridded_scene, composite_products, composite_name="rgb_composite",
                     composite_data_kind="rgb", share_mask=True, fill_value=None, **kwargs):
        if composite_name in gridded_scene:
            LOG.error("Cannot create composite product '%s', it already exists." % (composite_name,))
            raise ValueError("Cannot create composite product '%s', it already exists." % (composite_name,))
        available_products = set(gridded_scene.keys())
        desired_products = set(composite_products)
        missing_products = desired_products - (available_products & desired_products)
        if missing_products:
            LOG.error("Not all bands available to create RGB composite. Missing:\n\t%s", "\n\t".join(missing_products))
            raise RuntimeError("Not all bands available to create RGB composite")

        if fill_value is None:
            fill_value = gridded_scene[composite_products[0]]["fill_value"]

        fn = composite_name + ".dat"

        try:
            comp_data = self.joined_array(gridded_scene, composite_products)

            if share_mask:
                bad_mask = self.shared_mask(gridded_scene, composite_products)
                comp_data[bad_mask, :] = fill_value
                del bad_mask

            comp_data.tofile(fn)
            base_product = gridded_scene[composite_products[0]]
            base_product["data_kind"] = composite_data_kind
            gridded_scene[composite_name] = self._create_gridded_product(composite_name, fn, base_product=base_product)
        except StandardError:
            LOG.error("Could not create composite product with name '%s'", composite_name)
            if os.path.isfile(fn):
                os.remove(fn)
            raise

        return gridded_scene


class TrueColorCompositor(RGBCompositor):
    default_compare_index = 0

    def __init__(self, tc_red_products, tc_green_products, tc_blue_products, tc_hires_products, **kwargs):
        self.red_products = tc_red_products
        self.green_products = tc_green_products
        self.blue_products = tc_blue_products
        self.hires_products = tc_hires_products
        super(TrueColorCompositor, self).__init__(**kwargs)

    def _get_first_available_product(self, gridded_scene, desired_products):
        LOG.debug("Checking if any of the following are in the scene: %s", desired_products)
        for pn in desired_products:
            if pn in gridded_scene:
                LOG.debug("Found '%s' in the scene", pn)
                return pn

        return None

    def _get_first_available_products(self, gridded_scene, product_order, **kwargs):
        found_products = []
        for band_name in product_order:
            product_list = kwargs[band_name]
            product_name = self._get_first_available_product(gridded_scene, product_list)
            if product_name is None:
                LOG.error("Missing '%s' band product, can not create rgb image" % (band_name,))
                raise RuntimeError("Missing '%s' band product, can not create rgb image" % (band_name,))
            found_products.append(product_name)
        return found_products

    def ratio_sharpen(self, lowres_red_data, rgb_data, compare_index=None):
        compare_index = compare_index if compare_index is not None else self.default_compare_index
        lowres_band_indexes = [x for x in range(rgb_data.shape[0]) if x != compare_index]
        LOG.debug("True color compare index is set to %d, shape %r, lowres indexes %r",
                  compare_index, rgb_data.shape, lowres_band_indexes)
        ratio = rgb_data[compare_index] / lowres_red_data
        for idx in lowres_band_indexes:
            rgb_data[idx, :] *= ratio

    def modify_scene(self, gridded_scene, composite_name="true_color", composite_data_kind="crefl_true_color",
                     share_mask=True, fill_value=None, sharpen_rgb=True, **kwargs):
        if composite_name in gridded_scene:
            LOG.error("Cannot create composite product '%s', it already exists." % (composite_name,))
            raise ValueError("Cannot create composite product '%s', it already exists." % (composite_name,))

        # GROSS:
        red_product, green_product, blue_product = self._get_first_available_products(gridded_scene,
                                                                                      ("red", "green", "blue"),
                                                                                      red=self.red_products,
                                                                                      green=self.green_products,
                                                                                      blue=self.blue_products)

        if fill_value is None:
            fill_value = gridded_scene[red_product]["fill_value"]

        fn = composite_name + ".dat"

        try:
            all_products = [red_product, green_product, blue_product]
            sharp_red_product = self._get_first_available_product(gridded_scene, self.hires_products)
            if sharpen_rgb and not sharp_red_product:
                LOG.info("No high resolution products were found so true color sharpening will not be done")
                LOG.debug("Will attempt to create a true color image using: %s", ",".join(all_products))
                comp_data = self.joined_array(gridded_scene, all_products)
            elif sharpen_rgb:
                all_products.append(sharp_red_product)
                LOG.debug("Will attempt to create a true color image using: %s", ",".join(all_products))
                comp_data = self.joined_array(gridded_scene, (sharp_red_product, green_product, blue_product))
                self.ratio_sharpen(gridded_scene[red_product].get_data_array(), comp_data)

            if share_mask:
                LOG.debug("Sharing missing value mask between bands and using fill value %r", fill_value)
                # comp_data[:, self.shared_mask(gridded_scene, all_products)] = fill_value
                shared_mask = self.shared_mask(gridded_scene, all_products)
                print shared_mask.shape
                comp_data[:, shared_mask] = fill_value

            LOG.debug("True color array has shape %r", comp_data.shape)
            LOG.info("Saving true color image to filename '%s'", fn)
            comp_data.tofile(fn)
            base_product = gridded_scene[all_products[0]]
            base_product["data_kind"] = composite_data_kind
            gridded_scene[composite_name] = self._create_gridded_product(composite_name, fn, base_product=base_product)
        except StandardError:
            LOG.error("Could not create composite product with name '%s'", composite_name)
            if os.path.isfile(fn):
                os.remove(fn)
            raise

        return gridded_scene


class FalseColorCompositor(TrueColorCompositor):
    # see TrueColorCompositor.ratio_sharpen()
    default_compare_index = 2

    def __init__(self, fc_red_products, fc_green_products, fc_blue_products, fc_hires_products, **kwargs):
        super(FalseColorCompositor, self).__init__(fc_red_products,
                                                   fc_green_products,
                                                   fc_blue_products,
                                                   fc_hires_products,
                                                   **kwargs)

    def modify_scene(self, gridded_scene, composite_name="false_color", composite_data_kind="crefl_false_color",
                     share_mask=True, fill_value=None, sharpen_rgb=True, **kwargs):
        if composite_name in gridded_scene:
            LOG.error("Cannot create composite product '%s', it already exists." % (composite_name,))
            raise ValueError("Cannot create composite product '%s', it already exists." % (composite_name,))

        red_product, green_product, blue_product = self._get_first_available_products(gridded_scene,
                                                                                      ("red", "green", "blue"),
                                                                                      red=self.red_products,
                                                                                      green=self.green_products,
                                                                                      blue=self.blue_products)
        if fill_value is None:
            fill_value = gridded_scene[red_product]["fill_value"]

        fn = composite_name + ".dat"

        try:
            all_products = [red_product, green_product, blue_product]
            sharp_blue_product = self._get_first_available_product(gridded_scene, self.hires_products)

            if sharpen_rgb and not sharp_blue_product:
                LOG.info("No high resolution products were found so false color sharpening will not be done")
                LOG.debug("Will attempt to create a false color image using: %s", ",".join(all_products))
                comp_data = self.joined_array(gridded_scene, all_products)
            elif sharpen_rgb:
                all_products.append(sharp_blue_product)
                LOG.debug("Will attempt to create a false color image using: %s", ",".join(all_products))
                comp_data = self.joined_array(gridded_scene, (red_product, green_product, sharp_blue_product))
                self.ratio_sharpen(gridded_scene[blue_product].get_data_array(), comp_data)

            if share_mask:
                comp_data[:, self.shared_mask(gridded_scene, all_products)] = fill_value

            LOG.debug("False color array has shape %r", comp_data.shape)
            LOG.info("Saving false color image to filename '%s'", fn)
            comp_data.tofile(fn)
            base_product = gridded_scene[all_products[0]]
            base_product["data_kind"] = composite_data_kind
            gridded_scene[composite_name] = self._create_gridded_product(composite_name, fn, base_product=base_product)
        except StandardError:
            LOG.error("Could not create composite product with name '%s'", composite_name)
            if os.path.isfile(fn):
                os.remove(fn)
            raise

        return gridded_scene


def add_rgb_compositor_argument_groups(parser, num_compositors=1):
    # By adding a number to this we can have more than one compositor at a time...I think that'll work
    pass


def add_true_color_compositor_argument_groups(parser):
    from argparse import SUPPRESS
    group = parser.add_argument_group(title="true_color Initialization")
    group.add_argument("--true-color-red", dest="tc_red_products", nargs="+", default=SUPPRESS,
                       help="Specify what bands to look for to make true color images")
    group.add_argument("--true-color-green", dest="tc_green_products", nargs="+", default=SUPPRESS,
                       help="Specify what bands to look for to make true color images")
    group.add_argument("--true-color-blue", dest="tc_blue_products", nargs="+", default=SUPPRESS,
                       help="Specify what bands to look for to make true color images")
    group.add_argument("--true-color-hires", dest="tc_hires_products", nargs="+", default=SUPPRESS,
                       help="Specify what bands to look for to sharpen true color images (red color)")
    group = parser.add_argument_group(title="true_color Modification")
    group.add_argument("--true-color-name", dest="composite_name", default="true_color",
                       help="specify alternate name for true color product")
    group.add_argument("--true-color-kind", dest="composite_data_kind", default="crefl_true_color",
                       help="specify alternate 'data_kind' for true color product (useful in rescaling)")
    group.add_argument("--true-color-no-sharpen", dest="sharpen_rgb", action="store_false",
                       help="Don't use the high resolution band to sharpen the other bands")
    return ["true_color Initialization", "true_color Modification"]


def add_false_color_compositor_argument_groups(parser):
    from argparse import SUPPRESS
    group = parser.add_argument_group(title="false_color Initialization")
    group.add_argument("--false-color-red", dest="fc_red_products", nargs="+", default=SUPPRESS,
                       help="Specify what bands to look for to make false color images")
    group.add_argument("--false-color-green", dest="fc_green_products", nargs="+", default=SUPPRESS,
                       help="Specify what bands to look for to make false color images")
    group.add_argument("--false-color-blue", dest="fc_blue_products", nargs="+", default=SUPPRESS,
                       help="Specify what bands to look for to make false color images")
    group.add_argument("--false-color-hires", dest="fc_hires_products", nargs="+", default=SUPPRESS,
                       help="Specify what bands to look for to sharpen false color images (red color)")
    group = parser.add_argument_group(title="false_color Modification")
    group.add_argument("--false-color-name", dest="composite_name", default="false_color",
                       help="specify alternate name for false color product")
    group.add_argument("--false-color-kind", dest="composite_data_kind", default="crefl_false_color",
                       help="specify alternate 'data_kind' for false color product (useful in rescaling)")
    group.add_argument("--false-color-no-sharpen", dest="sharpen_rgb", action="store_false",
                       help="Don't use the high resolution band to sharpen the other bands")
    return ["false_color Initialization", "false_color Modification"]


def main():
    pass


if __name__ == "__main__":
    sys.exit(main())