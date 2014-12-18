#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
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
"""Module for running unit tests from the polar2grid.core package.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import sys
import unittest
from StringIO import StringIO

from polar2grid.core import roles


class TestCSVConfig(unittest.TestCase):
    string_1 = """# This is a comment
this,is,item,1,id,id,stuff1,stuff1
this,  is,   item,  2, id, id, stuff2, stuff2
"""
    string_1_diff = """# This is a comment
this,is,item,1,id,id,stuff1_diff,stuff1_diff
this,  is,   item,  2, id, id, stuff2_diff, stuff2_diff
"""
    string_2 = """# This is a comment
this,is,item,3,id,id,stuff3,stuff3
this,  is,   item,  4, id, id, stuff4, stuff4
# Another comment
"""
    string_3 = """# This is a comment
this,  is,   item,  4, id, id, stuff4, stuff4
this,is,item,*,id,id,stuffwild,stuffwild
# Another comment
"""
    def test_basic_1(self):
        """Test that config files can be loaded.
        """
        file_obj = StringIO(self.string_1)
        reader = roles.CSVConfigReader(file_obj)
        self.assertEqual(reader.get_config_entry("this", "is", "item", "1", "id", "id"), ("stuff1", "stuff1"))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "2", "id", "id"), ("stuff2", "stuff2"))

    def test_basic_2(self):
        """Test that a config file can be loaded after initialization.
        """
        file_obj = StringIO(self.string_1)
        reader = roles.CSVConfigReader(file_obj)
        reader.load_config_file(StringIO(self.string_2))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "1", "id", "id"), ("stuff1", "stuff1"))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "2", "id", "id"), ("stuff2", "stuff2"))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "3", "id", "id"), ("stuff3", "stuff3"))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "4", "id", "id"), ("stuff4", "stuff4"))

    def test_repeat_1(self):
        """Test that config files are handled in order.
        """
        reader = roles.CSVConfigReader()
        reader.load_config_file(StringIO(self.string_1))
        reader.load_config_file(StringIO(self.string_1_diff))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "1", "id", "id"), ("stuff1", "stuff1"))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "2", "id", "id"), ("stuff2", "stuff2"))

        reader = roles.CSVConfigReader()
        reader.load_config_file(StringIO(self.string_1_diff))
        reader.load_config_file(StringIO(self.string_1))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "1", "id", "id"), ("stuff1_diff", "stuff1_diff"))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "2", "id", "id"), ("stuff2_diff", "stuff2_diff"))

    def test_wildcard_1(self):
        """Test that wild cards work.
        """
        reader = roles.CSVConfigReader()
        reader.load_config_file(StringIO(self.string_3))
        reader.load_config_file(StringIO(self.string_1))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "1", "id", "id"), ("stuffwild", "stuffwild"))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "2", "id", "id"), ("stuffwild", "stuffwild"))
        self.assertEqual(reader.get_config_entry("this", "is", "item", "4", "id", "id"), ("stuff4", "stuff4"))
        pass


def main():
    return unittest.main()

if __name__ == "__main__":
    sys.exit(main())
