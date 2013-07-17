"""Module for running unit tests from the polar2grid.core package.

:author: David Hoese, SSEC
"""

import os
import sys
import unittest
from StringIO import StringIO

from . import roles


### Role Tests ###

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
