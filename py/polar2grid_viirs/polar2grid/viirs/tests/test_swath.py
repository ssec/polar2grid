#!/usr/bin/env python
# encoding: utf-8
"""
Test the polar2grid.viirs Frontend class.

:author:       David Hoese (davidh)
:author:       Ray Garcia (rayg)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2014
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

    Written by David Hoese    January 2014
    University of Wisconsin-Madison
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

from polar2grid.viirs import swath

import mock
import unittest

FAKE_NAV1 = swath.NavigationTuple("fake_nav1", "lon1", "lat1")
FAKE_PRODUCT_INFO1 = {
    "prod1": swath.ProductInfo(tuple(), FAKE_NAV1, 32, "fake1", "This is a fake product #1"),
    "prod2": swath.ProductInfo(("prod1",), FAKE_NAV1, 32, "fake1", "This is a fake product #2"),
    "lon1": swath.ProductInfo(tuple(), FAKE_NAV1, 32, "longitude", "This is a fake product (lon #1)"),
    "lat1": swath.ProductInfo(tuple(), FAKE_NAV1, 32, "latitude", "This is a fake product (lat #1)"),
}

FAKE_I01_REGEX = r'SVI01_.*\.h5'
FAKE_PRODUCT_FILE_REGEXES1 = {
    "prod1": swath.RawProductFileInfo(FAKE_I01_REGEX, "reflectance"),
    # TODO: Add other stuff
}


def find_all_files_side_effect_factory(patterns, **pass_kwargs):
    def find_all_files_side_effect(*args, **kwargs):
        return [(p % pass_kwargs) for p in patterns]

    return find_all_files_side_effect


class ProductInfoTestCase(unittest.TestCase):
    """Test functions having to do with product definition/information.
    """
    @mock.patch.dict("polar2grid.viirs.swath.PRODUCT_INFO", values=FAKE_PRODUCT_INFO1, clear=True)
    def test_get_product_dependencies_no_deps(self):
        deps = swath.get_product_dependencies("prod1")
        self.assertItemsEqual([], deps)

    @mock.patch.dict("polar2grid.viirs.swath.PRODUCT_INFO", values=FAKE_PRODUCT_INFO1, clear=True)
    def test_get_product_dependencies_deps(self):
        deps = swath.get_product_dependencies("prod2")
        self.assertItemsEqual(["prod1"], deps)

    @mock.patch.dict("polar2grid.viirs.swath.PRODUCT_INFO", values=FAKE_PRODUCT_INFO1, clear=True)
    def test_get_product_descendants_one(self):
        deps = swath.get_product_descendants(["prod1"])
        self.assertItemsEqual(["prod1", "prod2"], deps)

    @mock.patch.dict("polar2grid.viirs.swath.PRODUCT_INFO", values=FAKE_PRODUCT_INFO1, clear=True)
    def test_get_product_descendants_two(self):
        deps = swath.get_product_descendants(["prod1", "prod2"])
        self.assertItemsEqual(["prod1", "prod2"], deps)

    @mock.patch.dict("polar2grid.viirs.swath.PRODUCT_INFO", values=FAKE_PRODUCT_INFO1, clear=True)
    def test_get_product_descendants_three(self):
        deps = swath.get_product_descendants(["prod2"])
        self.assertItemsEqual(["prod2"], deps)


class SwathExtractorTestCase(unittest.TestCase):
    """Test features of the SwathExtractor class.
    """
    @mock.patch.object(swath.SwathExtractor, "find_all_files", spec=swath.SwathExtractor, side_effect=find_all_files_side_effect_factory(["SVI01_npp_d20120928.h5"]))
    @mock.patch("polar2grid.viirs.swath.ALL_FILE_REGEXES", new=[FAKE_I01_REGEX])
    @mock.patch.dict("polar2grid.viirs.swath.PRODUCT_INFO", values=FAKE_PRODUCT_INFO1, clear=True)
    @mock.patch.dict("polar2grid.viirs.swath.PRODUCT_FILE_REGEXES", values=FAKE_PRODUCT_FILE_REGEXES1, clear=True)
    def test_all_products_property(self, find_mock):
        f = swath.SwathExtractor(['.'])
        find_mock.assert_called_with(['.'])
        self.assertItemsEqual(FAKE_PRODUCT_INFO1.keys(), f.all_product_names, msg="Unexpected list for all_product_names")
        self.assertIn("prod1", f.available_product_names)


def suite():
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    test_suite.addTest(loader.loadTestsFromTestCase(ProductInfoTestCase))
    test_suite.addTest(loader.loadTestsFromTestCase(SwathExtractorTestCase))
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

