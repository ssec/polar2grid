#!/usr/bin/env pythpn
"""Polar2Grid frontend for extracting data and metadata from files processed by the
Microwave Integrated Retrieval System (MIRS).

FUTURE: Right now this frontend uses a new structure (coding and metadata provided) that isn't supported by the rest P2G. In the future it will not need the wrapper code.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Sept 2014
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

    Written by David Hoese    September 2014
    University of Wisconsin-Madison
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import numpy
from netCDF4 import Dataset

from polar2grid.core import roles

LOG = logging.getLogger(__name__)

### PRODUCT DEFINITIONS ###
PRODUCTS = []


class ProductDefinition(object):
    def __init__(self, name, dependencies=None):
        self.name = name
        self.dependencies = dependencies or []


def init_product_list():
    """Initialize the list of product definitions.

    This function is not necessarily needed, but helps with future changes where the available products are dynamic
    based on the system or location (just trying something out).
    """
    pass

### I/O Operations ###

# Constant keys mapping "what I want" to "what is actually in the file"
RR_VAR = "rr"
BT_VAR = "bt"
BT_VAR_88 = "bt_88"
FREQ_VAR = "freq"
LAT_VAR = "latitude"
LON_VAR = "longitude"

BT_VARS = [
    BT_VAR_88,
]


class MIRSFileReader(object):
    """Basic MIRS file reader.

    If there are alternate formats/structures for MIRS files then new classes should be made.
    """
    GLOBAL_FILL_ATTR_NAME = "missing_value"
    # Constant -> (var_name, scale_attr_name, fill_attr_name, frequency)
    FILE_STRUCTURE = {
        RR_VAR: ("RR", "scale", None, None),
        BT_VAR_88: ("BT", "scale", None, 88.2),
        FREQ_VAR: ("Freq", None, None, None),
        LAT_VAR: ("Latitude", None, None, None),
        LON_VAR: ("Longitude", None, None, None),
    }

    def __init__(self, filepath, validate=True):
        self.filename = os.path.basename(filepath)
        self.filepath = os.path.realpath(filepath)
        self.nc_obj = Dataset(self.filepath, "r")
        if validate:
            self._validate()

        self.satellite = self.nc_obj.satellite_name
        self.instrument = self.nc_obj.instrument_name
        self.start_time = datetime.strptime(self.nc_obj.time_coverage_start, "%Y-%m-%dT%H:%M:%SZ")
        self.end_time = datetime.strptime(self.nc_obj.time_coverage_end, "%Y-%m-%dT%H:%M:%SZ")

    def _validate(self):
        """Validate that the file this object represents is something that we actually know how to read.
        """
        try:
            assert(self.nc_obj.project == "Microwave Integrated Retrieval System")
            assert(self.nc_obj.title == "MIRS IMG")
            assert(self.nc_obj.data_model == "NETCDF4")
        except AssertionError:
            LOG.debug("Debug Exception Information: ", exc_info=True)
            LOG.error("Unknown file format for file %s" % (self.filename,))
            raise ValueError("Unknown file format for file %s" % (self.filename,))

    def __getitem__(self, item):
        if item in self.FILE_STRUCTURE:
            var_name = self.FILE_STRUCTURE[item][0]
            nc_var = self.nc_obj.variables[var_name]
            return nc_var
        return self.nc_obj.variables[item]

    def get_fill_value(self, item):
        fill_value = None
        if item in self.FILE_STRUCTURE:
            var_name = self.FILE_STRUCTURE[item][0]
            fill_attr_name = self.FILE_STRUCTURE[item][2]
            if fill_attr_name:
                fill_value = getattr(self.nc_obj.variables[var_name], fill_attr_name)
        if fill_value is None:
            fill_value = getattr(self.nc_obj, self.GLOBAL_FILL_ATTR_NAME, None)

        LOG.debug("File fill value for '%s' is '%f'", item, float(fill_value))
        return fill_value

    def get_scale_value(self, item):
        scale_value = None
        if item in self.FILE_STRUCTURE:
            var_name = self.FILE_STRUCTURE[item][0]
            scale_attr_name = self.FILE_STRUCTURE[item][1]
            if scale_attr_name:
                scale_value = float(getattr(self.nc_obj.variables[var_name], scale_attr_name))
                LOG.debug("File scale value for '%s' is '%f'", item, float(scale_value))
        return scale_value

    def filter_by_frequency(self, item, arr, freq):
        freq_var = self[FREQ_VAR]
        freq_idx = numpy.nonzero(freq_var[:] == freq)[0]
        if freq_idx:
            freq_idx = freq_idx[0]
        else:
            LOG.error("Frequency %f for variable %s does not exist" % (freq, item))
            raise ValueError("Frequency %f for variable %s does not exist" % (freq, item))

        freq_dim_idx = self[item].dimensions.index(freq_var.dimensions[0])
        idx_obj = [slice(x) for x in arr.shape]
        idx_obj[freq_dim_idx] = freq_idx
        return arr[idx_obj]

    def get_swath_data(self, item, dtype=numpy.float32, fill=numpy.nan):
        """Get swath data from the file. Usually requires special processing.
        """
        var_data = self[item][:].astype(dtype)
        freq = self.FILE_STRUCTURE[item][3]
        if freq:
            var_data = self.filter_by_frequency(item, var_data, freq)

        file_fill = self.get_fill_value(item)
        file_scale = self.get_scale_value(item)

        if file_scale:
            var_data = var_data.astype(numpy.float32) / file_scale
        if file_fill:
            var_data[var_data == file_fill] = fill

        return var_data

    def _compare(self, other, method):
        try:
            return method(self.start_time, other.start_time)
        except AttributeError:
            raise NotImplemented

    def __lt__(self, other):
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        return self._compare(other, lambda s, o: s == o)

    def __ge__(self, other):
        return self._compare(other, lambda s, o: s >= o)

    def __gt__(self, other):
        return self._compare(other, lambda s, o: s > o)

    def __ne__(self, other):
        return self._compare(other, lambda s, o: s != o)

### Frontend Objects###


class NewStyleFrontend(object):
    """Polar2Grid Frontend object for handling MIRS files.

    FUTURE: Currently uses an undefined interface that is still in development
    """
    def create_scenes(self, products=None):
        pass


# FUTURE: Can we make the new style frontend and all of its glue scripts use the new object, but slowly update the other code?
class Frontend(roles.FrontendRole):
    pass


def add_base_args(parser):
    """Add arguments that all polar2grid scripts should have
    """
    # FUTURE: Move to polar2grid.core or at least polar2grid


def add_frontend_args(parser):
    parser.add_argument("")
    return parser


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Extract swath data from MIRS data files")
    parser = add_frontend_args(parser)
    args = parser.parse_args()

    f = NewStyleFrontend(args.filenames)
    f.create_scenes(products=args.product_names)

if __name__ == "__main__":
    sys.exit(main())
