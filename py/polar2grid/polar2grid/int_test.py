#!/usr/bin/env python
# encoding: utf-8
"""Python module for running integration tests.
Includes full glue script tests that expect a base directory as input. This
directory is searched for all known test case directories. A test case
directory contains the output of a specific test. This test case directory
maps to one input directory that is searched for before testing is started.
If the input directory does not exist an exception will be raised and the test
will fail.

In cases where test data is required, directories are known by
three names:

    - input directories:
        Satellite instrument input data
    - expect or expected directories:
        Output of running tests that is known to be correct
    - output directories:
        Output of running tests on the current system and that should be
        verified against the expected directories.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         May 2013
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

    Written by David Hoese    May 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

# VIIRS Glue Scripts
from . import viirs2awips,viirs2gtiff,viirs2binary,viirs2ninjo
# MODIS Glue Scripts
from . import modis2awips
# Utilities
from polar2grid.core import constants
from . import compare

import os
import sys
import logging
import unittest
from glob import glob
import shutil

log = logging.getLogger(__name__)
INPUT_DIR = os.path.realpath(os.environ.get("P2G_TEST_IN", "."))
OUTPUT_DIR = os.path.realpath(os.environ.get("P2G_TEST_OUT", "."))
KEEP_OUTPUT = os.environ.get("P2G_KEEP_TEST_OUTPUT", False)
try:
    KEEP_OUTPUT = int(KEEP_OUTPUT)
except ValueError:
    pass
finally:
    KEEP_OUTPUT = bool(KEEP_OUTPUT)

### Integration Tests ###
#     Glue Scripts      #
#########################

# Lookup from expected directory to input directory name
glue_script_expected_to_input = {
        "expect_viirs2awips_203_20120408" : "input_viirs_20120408",
        "expect_viirs2awips_211e_20120408" : "input_viirs_20120408",
        "expect_viirs2awips_211e_20120225" : "input_viirs_20120225",
        "expect_viirs2gtiff_p4_211e_20120225" : "input_viirs_20120225",
        "expect_viirs2gtiff_polar_north_pacific_20120408" : "input_viirs_20120408",
        "expect_viirs2ninjo_dwd_germany_20120701" : "input_viirs_20120701",
        }

class viirs2awipsTestCase(unittest.TestCase):
    base_dir  = INPUT_DIR
    out_dir   = OUTPUT_DIR

    def compare_expected(self, test_output_dir, expected_dir):
        output_files = os.listdir(test_output_dir)
        expected_files = os.listdir(expected_dir)
        success = True
        for expected_file in expected_files:
            expected_fp = os.path.join(expected_dir, expected_file)
            output_fp = os.path.join(test_output_dir, expected_file)
            if expected_file not in output_files:
                log.info("Missing output file: '%s'" % (expected_fp,))
                success = False
                continue

            # Compare the files
            num_diff_pixels = compare.compare_awips_netcdf(expected_fp, output_fp)
            if num_diff_pixels != 0:
                log.info("Files are not the same %s -vs- %s" % (expected_fp, output_fp))
                success = False

        return success

    def test_expect_viirs2awips_203_20120408(self):
        input_dir_name = glue_script_expected_to_input["expect_viirs2awips_203_20120408"]
        argv = [
                "-g", "203",
                "-f"
                ]
        argv.extend(glob(os.path.join(self.base_dir, input_dir_name, "SV*_npp_d20120408_t131*.h5")))
        output_dir_name = "output_viirs2awips_203_20120408"
        full_output_dir = os.path.join(self.out_dir, output_dir_name)
        os.makedirs(full_output_dir)
        os.chdir(full_output_dir)

        # Run the glue script
        try:
            status = viirs2awips.main(argv=argv)
            # We expect a full success
            self.assertEquals(status, constants.STATUS_SUCCESS)

            # Compare the output with the expected output
            self.assertTrue(self.compare_expected(full_output_dir, os.path.join(self.base_dir, "expect_viirs2awips_203_20120408")))
        except StandardError:
            raise
        finally:
            # If we had a problem then we need to get rid of the working directory
            os.chdir("..")
            if not KEEP_OUTPUT:
                log.debug("Removing output directory: %s" % output_dir_name)
                shutil.rmtree(output_dir_name)

    def test_expect_viirs2awips_211e_20120408(self):
        """Test viirs2awips on Alaska data on the 211e grid
        What happens when we tell it to remap to a grid where the data
        doesn't intersect.
        """
        logging.getLogger('').setLevel(logging.CRITICAL)
        input_dir_name = glue_script_expected_to_input["expect_viirs2awips_211e_20120408"]
        argv = [
                "-g", "211e",
                "-f"
                ]
        argv.extend(glob(os.path.join(self.base_dir, input_dir_name, "SV*_npp_d20120408_t131*.h5")))
        output_dir_name = "output_viirs2awips_211e_20120408"
        full_output_dir = os.path.join(self.out_dir, output_dir_name)
        os.makedirs(full_output_dir)
        os.chdir(full_output_dir)

        # Run the glue script
        try:
            status = viirs2awips.main(argv=argv)
            # We expect a full success
            self.assertEquals(status, constants.STATUS_REMAP_FAIL)
        except StandardError:
            raise
        finally:
            # If we had a problem then we need to get rid of the working directory
            os.chdir("..")
            if not KEEP_OUTPUT:
                log.debug("Removing output directory: %s" % output_dir_name)
                shutil.rmtree(output_dir_name)

    def test_expect_viirs2awips_211e_20120225(self):
        input_dir_name = glue_script_expected_to_input["expect_viirs2awips_211e_20120225"]
        argv = [
                "-g", "211e",
                "-f"
                ]
        argv.extend(glob(os.path.join(self.base_dir, input_dir_name, "SV[I,D]*_npp_d20120225_t180[124]*.h5")))
        output_dir_name = "output_viirs2awips_211e_20120225"
        full_output_dir = os.path.join(self.out_dir, output_dir_name)
        os.makedirs(full_output_dir)
        os.chdir(full_output_dir)

        # Run the glue script
        try:
            status = viirs2awips.main(argv=argv)
            # We expect a full success
            self.assertEquals(status, constants.STATUS_SUCCESS)

            # Compare the output with the expected output
            self.assertTrue(self.compare_expected(full_output_dir, os.path.join(self.base_dir, "expect_viirs2awips_211e_20120225")))
        except StandardError:
            raise
        finally:
            # If we had a problem then we need to get rid of the working directory
            os.chdir("..")
            if not KEEP_OUTPUT:
                log.debug("Removing output directory: %s" % output_dir_name)
                shutil.rmtree(output_dir_name)

class viirs2gtiffTestCase(unittest.TestCase):
    base_dir  = INPUT_DIR
    out_dir   = OUTPUT_DIR

    def compare_expected(self, test_output_dir, expected_dir):
        output_files = os.listdir(test_output_dir)
        expected_files = os.listdir(expected_dir)
        success = True
        for expected_file in expected_files:
            expected_fp = os.path.join(expected_dir, expected_file)
            output_fp = os.path.join(test_output_dir, expected_file)
            if expected_file not in output_files:
                log.info("Missing output file: '%s'" % (expected_fp,))
                success = False
                continue

            # Compare the files
            num_diff_pixels = compare.compare_geotiff(expected_fp, output_fp)
            if num_diff_pixels != 0:
                log.info("Files are not the same %s -vs- %s" % (expected_fp, output_fp))
                success = False

        return success

    def test_expect_viirs2gtiff_p4_211e_20120225(self):
        input_dir_name = glue_script_expected_to_input["expect_viirs2gtiff_p4_211e_20120225"]
        argv = [
                "-g", "p4_211e",
                "-f"
                ]
        argv.extend(glob(os.path.join(self.base_dir, input_dir_name, "SV[I,D]*_npp_d20120225_t180[124]*.h5")))
        output_dir_name = "output_viirs2gtiff_p4_211e_20120225"
        full_output_dir = os.path.join(self.out_dir, output_dir_name)
        os.makedirs(full_output_dir)
        os.chdir(full_output_dir)

        # Run the glue script
        try:
            status = viirs2gtiff.main(argv=argv)
            # We expect a full success
            self.assertEquals(status, constants.STATUS_SUCCESS)

            # Compare the output with the expected output
            self.assertTrue(self.compare_expected(full_output_dir, os.path.join(self.base_dir, "expect_viirs2gtiff_p4_211e_20120225")))
        except StandardError:
            raise
        finally:
            # If we had a problem then we need to get rid of the working directory
            os.chdir("..")
            if not KEEP_OUTPUT:
                log.debug("Removing output directory: %s" % output_dir_name)
                shutil.rmtree(output_dir_name)

    def test_expect_viirs2gtiff_polar_north_pacific_20120408(self):
        this_name = "viirs2gtiff_polar_north_pacific_20120408"
        input_dir_name = glue_script_expected_to_input["expect_" + this_name]
        argv = [
                "-g", "polar_north_pacific",
                "-f"
                ]
        argv.extend(glob(os.path.join(self.base_dir, input_dir_name, "SV*_npp_d20120408_t131*.h5")))
        output_dir_name = "output_" + this_name
        full_output_dir = os.path.join(self.out_dir, output_dir_name)
        os.makedirs(full_output_dir)
        os.chdir(full_output_dir)

        # Run the glue script
        try:
            status = viirs2gtiff.main(argv=argv)
            # We expect a full success
            self.assertEquals(status, constants.STATUS_SUCCESS)

            # Compare the output with the expected output
            self.assertTrue(self.compare_expected(full_output_dir, os.path.join(self.base_dir, "expect_" + this_name)))
        except StandardError:
            raise
        finally:
            # If we had a problem then we need to get rid of the working directory
            os.chdir("..")
            if not KEEP_OUTPUT:
                log.debug("Removing output directory: %s" % output_dir_name)
                shutil.rmtree(output_dir_name)

class viirs2binaryTestCase(unittest.TestCase):
    pass

class viirs2ninjoTestCase(unittest.TestCase):
    base_dir  = INPUT_DIR
    out_dir   = OUTPUT_DIR

    def compare_expected(self, test_output_dir, expected_dir):
        output_files = os.listdir(test_output_dir)
        expected_files = os.listdir(expected_dir)
        success = True
        for expected_file in expected_files:
            expected_fp = os.path.join(expected_dir, expected_file)
            output_fp = os.path.join(test_output_dir, expected_file)
            if expected_file not in output_files:
                log.info("Missing output file: '%s'" % (expected_fp,))
                success = False
                continue

            # Compare the files
            num_diff_pixels = compare.compare_ninjo_tiff(expected_fp, output_fp)
            if num_diff_pixels != 0:
                log.info("Files are not the same %s -vs- %s" % (expected_fp, output_fp))
                success = False

        return success

    def test_expect_viirs2ninjo_dwd_germany_20120701(self):
        this_name = "viirs2ninjo_dwd_germany_20120701"
        input_dir_name = glue_script_expected_to_input["expect_" + this_name]
        argv = [
                "-g", "dwd_germany",
                "-f"
                ]
        argv.extend(glob(os.path.join(self.base_dir, input_dir_name, "SV*_npp_d20120701_t114*.h5")))
        output_dir_name = "output_" + this_name
        full_output_dir = os.path.join(self.out_dir, output_dir_name)
        os.makedirs(full_output_dir)
        os.chdir(full_output_dir)

        # Run the glue script
        try:
            status = viirs2ninjo.main(argv=argv)
            # We expect a full success
            self.assertEquals(status, constants.STATUS_SUCCESS)

            # Compare the output with the expected output
            self.assertTrue(self.compare_expected(full_output_dir, os.path.join(self.base_dir, "expect_" + this_name)))
        except StandardError:
            raise
        finally:
            # If we had a problem then we need to get rid of the working directory
            os.chdir("..")
            if not KEEP_OUTPUT:
                log.debug("Removing output directory: %s" % output_dir_name)
                shutil.rmtree(output_dir_name)

### MODIS ###

class modis2awipsTestCase(unittest.TestCase):
    pass

### End of Integration Tests ###

def discover_glue_script_test_cases(base_dir):
    """Search a directory for any known test inputs and expected directories.
    Expected directories are the known-to-be-good output of running the test
    cases.

    :param base_dir: Absolute path of a directory containing input and
        expected directories.
    :type base_dir: str
    :returns: List of 2-element tuples representing test cases. The first
        element is the input directory containing satellite instrument data,
        the second is the expected directory containing known valid test case
        results.
    """
    input_dirs  = [ x for x in os.listdir(base_dir) if x.startswith("input_")  ]
    expect_dirs = [ x for x in os.listdir(base_dir) if x.startswith("expect_") ]
    list_of_cases = []
    for e_dir in expect_dirs:
        i_dir = glue_script_expected_to_input.get(e_dir, None)
        if i_dir is None:
            log.warning("Expected output directory %s is unknown to this test module" % (e_dir,))
            continue

        if i_dir not in input_dirs:
            log.warning("Could not find required input directory (%s) for expected output directory %s" % (i_dir,e_dir))
            continue

        list_of_cases.append((i_dir,e_dir))

    return list_of_cases

def get_glue_script_test_suite(base_dir, out_dir, list_of_cases):
    """Return a `unittest.TestSuite` object for the available test
    cases discovered by `discover_glue_script_test_cases`.

    :param list_of_cases: Output from `discover_glue_script_test_cases`.
    :returns: Single `unittest.TestSuite` object to run all available tests.
    """
    test_case_names = [ "test_" + e_dir for i_dir,e_dir in list_of_cases ]
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Discover all tests that we have available
    for obj_name in globals():
        obj = globals()[obj_name]
        #print "Object: %r" % obj
        if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
            obj.base_dir = base_dir
            obj.out_dir  = out_dir
            this_test_cases_names = loader.getTestCaseNames(obj)
            for this_test_case_name in this_test_cases_names:
                if this_test_case_name in test_case_names:
                    log.debug("Found test %s.%s" % (obj_name,this_test_case_name))
                    suite.addTest(obj(this_test_case_name))

    return suite

def load_tests(loader, tests, pattern, in_dir=INPUT_DIR, out_dir=OUTPUT_DIR):
    suite = unittest.TestSuite()
    list_of_cases = discover_glue_script_test_cases(in_dir)
    test_case_names = [ "test_" + e_dir for i_dir,e_dir in list_of_cases ]
    for test_suite in tests:
        for t in test_suite:
            t.base_dir = in_dir
            t.out_dir = out_dir
            this_test_case_name = t.id().split('.')[-1]
            if this_test_case_name in test_case_names:
                log.debug("Found test %s.%s" % (t.__class__,this_test_case_name))
                suite.addTest(t)

    return suite

def main():
    global KEEP_OUTPUT
    global INPUT_DIR
    global OUTPUT_DIR
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Run polar2grid tests")
    parser.add_argument("-s", "--src-dir", nargs="?", default=INPUT_DIR,
            help="Base directory of test case input and expected directories")
    parser.add_argument("-d", "--dst-dir", nargs="?", default=OUTPUT_DIR,
            help="Base directory for output of running the tests")
    #parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
    #        help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument('--debug', dest='debug_mode', action='store_true', default=False,
            help='keep working output directories')
    args = parser.parse_args()

    #levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    #logging.basicConfig(level=levels[min(3,args.verbosity)])

    KEEP_OUTPUT = args.debug_mode
    INPUT_DIR = args.src_dir
    OUTPUT_DIR = args.dst_dir

    #args.src_dir = os.path.abspath(os.path.expanduser(args.src_dir))
    #args.dst_dir = os.path.abspath(os.path.expanduser(args.dst_dir))
    #list_of_cases = discover_glue_script_test_cases(args.src_dir)
    #test_suite = get_glue_script_test_suite(args.src_dir, args.dst_dir, list_of_cases)
    #test_runner = unittest.TextTestRunner()
    #test_result = test_runner.run(test_suite)

    unittest.main()

if __name__ == "__main__":
    sys.exit(main())

