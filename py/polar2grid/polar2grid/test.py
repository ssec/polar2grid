#!/usr/bin/env python
# encoding: utf-8
"""Python module for running unit tests.
Includes full glue script tests that expect a base directory as input. This
directory is searched for all known test case directories. A test case
directory contains the output of a specific test. This test case directory
maps to one input directory that is searched for before testing is started.
If the input directory does not exist an exception will be raised and the test.
Technically speaking, the glue script tests and any other tests requiring
outside information are not unit tests, but rather
integration tests. We still use the unittest module to organize these tests.

Some of the unit tests also require input files so a base directory argument
is also used. In cases where test data is required, directories are known by
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
:date:         Mar 2013
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

# VIIRS Glue Scripts
from . import viirs2awips,viirs2gtiff,viirs2binary,viirs2ninjo
# MODIS Glue Scripts
from . import modis2awips
# Other components
from polar2grid.core import roles,constants
from .grids import grids
# Utilities
from . import compare

import os
import sys
import logging
import unittest

log = logging.getLogger(__name__)

### Fake polar2grid classes ###
class FakeBackend(roles.BackendRole):
    """Fake backend to help with testing.

    Tests will overwrite these methods
    """
    def __init__(self): pass
    def can_handle_inputs(self, sat, instrument, nav_set_uid,
            kind, band, data_kind):
        pass
    def create_product(self, sat, instrument, nav_set_uid,
            kind, band, data_kind, **kwargs):
        pass

#########################
###     Unit Tests    ###
#########################

###      Backends     ###
class AWIPSBackendTestCase(unittest.TestCase):
    pass

class GtiffBackendTestCase(unittest.TestCase):
    pass

class BinaryBackendTestCase(unittest.TestCase):
    pass

class NinjoBackendTestCase(unittest.TestCase):
    pass

###     Grid Jobs     ###
class GridJobsTestCase(unittest.TestCase):
    """Test the `get_grid_jobs` method from `polar2grid.grids.grids`.
    This test case should only check for the behavior of grid jobs and not of
    the grid determination specifically. The grid determination test case will
    focus on different grid determination possibilities.
    """
    @classmethod
    def setUpClass(cls):
        # Turn off logging if it hasn't been configured already
        if not logging.getLogger('').handlers:
            logging.basicConfig(level=logging.CRITICAL)

        # Mimic a frontend's bands meta dictionary
        band_info = {
                ( constants.BKIND_I, constants.BID_01 ) : {
                    "data_kind"     : constants.DKIND_REFLECTANCE,
                    "remap_data_as" : constants.DKIND_REFLECTANCE,
                    "kind"          : constants.BKIND_I,
                    "band"          : constants.BID_01,
                    "fbf_img"       : None, # Invalid, but we don't have one so...
                    "fill_value"    : constants.DEFAULT_FILL_VALUE,
                    "swath_rows"    : 320,
                    "swath_cols"    : 6400,
                    "swath_scans"   : 10,
                    "rows_per_scan" : 32,
                    },
                ( constants.BKIND_I, constants.BID_02 ) : {
                    "data_kind"     : constants.DKIND_REFLECTANCE,
                    "remap_data_as" : constants.DKIND_REFLECTANCE,
                    "kind"          : constants.BKIND_I,
                    "band"          : constants.BID_02,
                    "fbf_img"       : None, # Invalid, but we don't have one so...
                    "fill_value"    : constants.DEFAULT_FILL_VALUE,
                    "swath_rows"    : 320,
                    "swath_cols"    : 6400,
                    "swath_scans"   : 10,
                    "rows_per_scan" : 32,
                    },
                ( constants.BKIND_I, constants.BID_03 ) : {
                    "data_kind"     : constants.DKIND_BTEMP,
                    "remap_data_as" : constants.DKIND_BTEMP,
                    "kind"          : constants.BKIND_I,
                    "band"          : constants.BID_03,
                    "fbf_img"       : None, # Invalid, but we don't have one so...
                    "fill_value"    : constants.DEFAULT_FILL_VALUE,
                    "swath_rows"    : 320,
                    "swath_cols"    : 6400,
                    "swath_scans"   : 10,
                    "rows_per_scan" : 32,
                    },
                ( constants.BKIND_I, constants.BID_04 ) : {
                    "data_kind"     : constants.DKIND_BTEMP,
                    "remap_data_as" : constants.DKIND_BTEMP,
                    "kind"          : constants.BKIND_I,
                    "band"          : constants.BID_04,
                    "fbf_img"       : None, # Invalid, but we don't have one so...
                    "fill_value"    : constants.DEFAULT_FILL_VALUE,
                    "swath_rows"    : 320,
                    "swath_cols"    : 6400,
                    "swath_scans"   : 10,
                    "rows_per_scan" : 32,
                    },
                ( constants.BKIND_I, constants.BID_05 ) : {
                    "data_kind"     : constants.DKIND_BTEMP,
                    "remap_data_as" : constants.DKIND_BTEMP,
                    "kind"          : constants.BKIND_I,
                    "band"          : constants.BID_05,
                    "fbf_img"       : None, # Invalid, but we don't have one so...
                    "fill_value"    : constants.DEFAULT_FILL_VALUE,
                    "swath_rows"    : 320,
                    "swath_cols"    : 6400,
                    "swath_scans"   : 10,
                    "rows_per_scan" : 32,
                    },
                }
        cls._band_info = band_info

        # Make our own grid configuration file
        grid_config_str = """# Comment - Copy of grids.conf with spaces removed
# GPD Grids
211e,gpd,grid211e.gpd,0,0,0,0,0,0,0,0
211e,gpd,grid211e.gpd,-123.044,59.844,-49.385,57.289,-65.091,14.335,-113.133,16.369
211w,gpd,grid211w.gpd,-152.855,54.536,-91.444,61.257,-92.720,17.514,-133.459,12.190
203,gpd,grid203.gpd,115.601,44.646,-53.660,57.635,-123.435,24.362,174.162,19.132
204,gpd,grid204.gpd,110.000,60.644,-109.129,60.644,-109.129,25.000,110.000,25.000
dwd_germany,gpd,griddwd_germany.gpd,-2.000,56.000,25.000,56.000,25.000,40.000,-2.000,40.000
# PROJ.4 Grids
p4_211e,proj4, +proj=lcc +datum=NAD83 +ellps=GRS80 +lat_1=25 +lon_0=-95 +no_defs,5120,5120,1015.9,-1015.9,-1956254.806724622,4364276.201489102
lcc_fit,proj4, +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=25 +lon_0=-95,None,None,1000,-1000,None,None
lcc_fit_hr,proj4, +proj=lcc +datum=WGS84 +ellps=WGS84 +lat_0=25 +lon_0=-95,None,None,400,-400,None,None
wgs84_fit,proj4, +proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs,None,None,0.0001,-0.0001,None,None
polar_canada,proj4, +proj=stere +datum=WGS84 +ellps=WGS84 +lat_0=90 +lat_ts=45.0 +lon_0=-150,None,None,1000,-1000,None,None
polar_north_pacific,proj4, +proj=stere +datum=WGS84 +ellps=WGS84 +lat_0=90 +lat_ts=45.0 +lon_0=-170,None,None,400,-400,None,None
polar_south_pacific,proj4, +proj=stere +datum=WGS84 +ellps=WGS84 +lat_0=-90 +lat_ts=-45.0 +lon_0=-170,None,None,400,-400,None,None
"""
        cls._grid_config_str = grid_config_str

    def test_except_grids_any_forced_0bands(self,
            can_handle=constants.GRIDS_ANY,
            forced_grids=["211e"]
            ):
        """Test that create_grid_jobs reports a ValueError when provided an empty band_info dictionary.
        Also provided that the backend reports any grid
        can be provided, and a grid is forced (skipping grid determination).
        """
        def fake_handle_inputs(self, *args, **kwargs):
            return can_handle
        backend = FakeBackend()
        backend.can_handle_inputs = fake_handle_inputs
        cart = grids.Cartographer(no_defaults=True)
        cart.add_grid_config_str(self._grid_config_str)
        self.assertRaises(ValueError, grids.create_grid_jobs,
                constants.SAT_NPP,
                constants.INST_VIIRS,
                constants.IBAND_NAV_UID,
                {},
                backend,
                cart,
                forced_grids=forced_grids
                )

    def test_except_grids_proj4_forced_0bands(self):
        """Same as `test_except_grids_any_forced_0bands`, but backend supports any PROJ.4 grid.
        """
        self.test_except_grids_any_forced_0bands(can_handle=constants.GRIDS_ANY_PROJ4)

    def test_except_grids_gpd_forced_0bands(self):
        """Same as `test_except_grids_any_forced_0bands`, but backend supports any GPD grid.
        """
        self.test_except_grids_any_forced_0bands(can_handle=constants.GRIDS_ANY_GPD)

    def test_output_grids_any_forced(self):
        """Test that create_grid_jobs returns the correct structure when any grid is supported.
        """
        def fake_handle_inputs(self, *args, **kwargs):
            return constants.GRIDS_ANY
        backend = FakeBackend()
        backend.can_handle_inputs = fake_handle_inputs
        cart = grids.Cartographer(no_defaults=True)
        cart.add_grid_config_str(self._grid_config_str)
        forced_grids = cart.grid_information.keys()[::2]
        grid_jobs = grids.create_grid_jobs(
                constants.SAT_NPP,
                constants.INST_VIIRS,
                constants.IBAND_NAV_UID,
                self._band_info,
                backend,
                cart,
                forced_grids=forced_grids
                )

        self.assertEqual(len(grid_jobs.keys()), len(forced_grids))
        for grid_name in forced_grids:
            self.assertIn(grid_name, grid_jobs.keys())

    def test_output_grids_proj4_forced(self):
        def fake_handle_inputs(self, *args, **kwargs):
            return constants.GRIDS_ANY_PROJ4
        backend = FakeBackend()
        backend.can_handle_inputs = fake_handle_inputs
        cart = grids.Cartographer(no_defaults=True)
        cart.add_grid_config_str(self._grid_config_str)
        forced_grids = ["wgs84_fit", "211e", "203", "dwd_germany", "p4_211e"]
        grid_jobs = grids.create_grid_jobs(
                constants.SAT_NPP,
                constants.INST_VIIRS,
                constants.IBAND_NAV_UID,
                self._band_info,
                backend,
                cart,
                forced_grids=forced_grids
                )

        self.assertEqual(len(grid_jobs.keys()), 2)
        self.assertIn("wgs84_fit", grid_jobs.keys())
        self.assertIn("p4_211e", grid_jobs.keys())

    def test_output_grids_gpd_forced(self):
        def fake_handle_inputs(self, *args, **kwargs):
            return constants.GRIDS_ANY_GPD
        backend = FakeBackend()
        backend.can_handle_inputs = fake_handle_inputs
        cart = grids.Cartographer(no_defaults=True)
        cart.add_grid_config_str(self._grid_config_str)
        forced_grids = ["wgs84_fit", "211e", "203", "dwd_germany", "p4_211e"]
        grid_jobs = grids.create_grid_jobs(
                constants.SAT_NPP,
                constants.INST_VIIRS,
                constants.IBAND_NAV_UID,
                self._band_info,
                backend,
                cart,
                forced_grids=forced_grids
                )

        self.assertEqual(len(grid_jobs.keys()), 3)
        self.assertIn("211e", grid_jobs.keys())
        self.assertIn("dwd_germany", grid_jobs.keys())
        self.assertIn("203", grid_jobs.keys())
        self.assertIn((constants.BKIND_I,constants.BID_01), grid_jobs["211e"])
        self.assertIn((constants.BKIND_I,constants.BID_02), grid_jobs["211e"])
        self.assertIn((constants.BKIND_I,constants.BID_03), grid_jobs["211e"])
        self.assertIn((constants.BKIND_I,constants.BID_04), grid_jobs["211e"])
        self.assertIn((constants.BKIND_I,constants.BID_05), grid_jobs["211e"])
        self.assertIn((constants.BKIND_I,constants.BID_01), grid_jobs["203"])
        self.assertIn((constants.BKIND_I,constants.BID_02), grid_jobs["203"])
        self.assertIn((constants.BKIND_I,constants.BID_03), grid_jobs["203"])
        self.assertIn((constants.BKIND_I,constants.BID_04), grid_jobs["203"])
        self.assertIn((constants.BKIND_I,constants.BID_05), grid_jobs["203"])
        self.assertIn((constants.BKIND_I,constants.BID_01), grid_jobs["dwd_germany"])
        self.assertIn((constants.BKIND_I,constants.BID_02), grid_jobs["dwd_germany"])
        self.assertIn((constants.BKIND_I,constants.BID_03), grid_jobs["dwd_germany"])
        self.assertIn((constants.BKIND_I,constants.BID_04), grid_jobs["dwd_germany"])
        self.assertIn((constants.BKIND_I,constants.BID_05), grid_jobs["dwd_germany"])

    def test_output_grids_any_determined(self):
        """Test that create_grid_jobs returns the correct structure when any grid is supported and determined.
        """
        def fake_handle_inputs(self, *args, **kwargs):
            return constants.GRIDS_ANY
        backend = FakeBackend()
        backend.can_handle_inputs = fake_handle_inputs
        cart = grids.Cartographer(no_defaults=True)
        cart.add_grid_config_str(self._grid_config_str)
        grid_jobs = grids.create_grid_jobs(
                constants.SAT_NPP,
                constants.INST_VIIRS,
                constants.IBAND_NAV_UID,
                self._band_info,
                backend,
                cart,
                bbox=(-110,50,-80,10)
                )

        self.assertEqual(len(grid_jobs.keys()), 3)
        self.assertIn("211e", grid_jobs.keys())
        self.assertIn("211w", grid_jobs.keys())
        self.assertIn("p4_211e", grid_jobs.keys())

class GridDeterminationTestCase(unittest.TestCase):
    pass

###    Frontends      ###
class VIIRSFrontendTestCase(unittest.TestCase):
    pass

class MODISFrontendTestCase(unittest.TestCase):
    pass

### Integration Tests ###
#     Glue Scripts      #
#########################

class viirs2awipsTestCase(unittest.TestCase):
    pass

class viirs2gtiffTestCase(unittest.TestCase):
    pass

class viirs2binaryTestCase(unittest.TestCase):
    pass

class viirs2ninjoTestCase(unittest.TestCase):
    pass

glue_script_expected_to_input = {
        "expect_viirs2awips_ak_20120408" : "input_viirs_20120408",
        }

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
            log.warning("Expected output directory %s is unknown to this test module" % (e_dir,i_dir))
            continue

        if i_dir not in input_dirs:
            log.warning("Could not find required input directory (%s) for expected output directory %s" % (i_dir,e_dir))
            continue

        list_of_cases.append((i_dir,e_dir))

    return list_of_cases

def get_glue_script_test_suite(list_of_cases):
    """Return a `unittest.TestSuite` object for the available test
    cases discovered by `discover_glue_script_test_cases`.

    :param list_of_cases: Output from `discover_glue_script_test_cases`.
    :returns: Single `unittest.TestSuite` object to run all available tests.
    """
    test_case_names = [ "test_" + i_dir + "_" + e_dir for i_dir,e_dir in list_of_cases ]
    suite = unittest.TestSuite()
    #for test_case_name in test_case_names:
    #    suite.addTest()

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Run polar2grid tests")
    parser.add_argument("--awips-png", action="store_true", default=False,
            help="Create PNG images whenever an AWIPS NetCDF was successfully created")

    parser.add_argument("-s", "--src-dir", nargs="?",
            help="Base directory of test case input and expected directories")
    parser.add_argument("-d", "--dst-dir", nargs="?",
            help="Base directory for output of running the tests")
    args = parser.parse_args()

    args.src_dir = os.path.abspath(os.path.expanduser(args.src_dir))
    args.dst_dir = os.path.abspath(os.path.expanduser(args.dst_dir))
    list_of_cases = discover_glue_script_test_cases(args.src_dir)
    test_suite = get_glue_script_test_suite(list_of_cases)

if __name__ == "__main__":
    sys.exit(main())

