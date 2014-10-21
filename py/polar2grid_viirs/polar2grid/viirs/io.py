#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
#     input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    October 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""
Simple objects to assist in reading VIIRS data from hdf5 (.h5) files.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Oct 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import h5py
import numpy

from polar2grid.viirs import guidebook
from polar2grid.core import UTC
from polar2grid.core.fbf import FileAppender
from polar2grid.viirs.guidebook import K_DATA_PATH

import os
import sys
import re
import logging
from datetime import datetime, timedelta

LOG = logging.getLogger(__name__)
UTC = UTC()


class HDF5Reader(object):
    """Generic HDF5 reading class.
    """
    def __init__(self, filename):
        self.filename = os.path.basename(filename)
        self.filepath = os.path.realpath(filename)
        self._h5_handle = h5py.File(filename, 'r')
        self.file_items = {}
        self._h5_handle.visititems(self._visit_items)
        # Also add the global attributes
        for attr_name, attr_val in self._h5_handle.attrs.items():
            self.file_items["." + attr_name] = attr_val[0][0]

    def _visit_items(self, name, obj):
        """Look at each variable in the HDF file and record its attributes.

        We also store the variable name because sometimes h5py gives you an
        unhelpful/weird KeyError if it doesn't have that key.
        """
        self.file_items[name] = obj
        for attr_name, attr_obj in obj.attrs.items():
            self.file_items[name + "." + attr_name] = attr_obj

    def __contains__(self, key):
        if key.startswith("/"):
            key = key[1:]

        return key in self.file_items

    def __getitem__(self, key):
        """Get HDF5 variable, making it easier to access attributes.
        """
        if key.startswith("/"):
            key = key[1:]

        return self.file_items[key]


def file_time_to_datetime(file_time):
    """Convert a VIIRS StartTime which is in microseconds since 1958-01-01 to
    a datetime object.
    """
    base = datetime(1958, 1, 1, 0, 0, 0)
    return base + timedelta(microseconds=int(file_time))


def time_attr_to_datetime(d, st):
    # The last character is a Z (as in Zulu/UTC)
    whole_sec, s_us = st[:-1].split(".")
    s_us = int(s_us)
    s_dt = datetime.strptime(d + whole_sec, "%Y%m%d%H%M%S").replace(tzinfo=UTC, microsecond=s_us)
    return s_dt


# TODO: Frontend iterates through each class, runs `handles_file` which gets them the exact file type
class VIIRSSDRReader(object):
    """VIIRS Data SDR hdf5 reader.

    Handles all the difficulties of reading SDR data (masking, scaling, etc.)
    """
    def __init__(self, filename_or_hdf_obj, file_type_info, instrument="viirs"):
        """Initialize VIIRS SDR Reader and get information that we can derive by the file name.

        :param filename: HDF5 filename for a VIIRS data SDR file.
        :param file_type_info: Dictionary mapping file key constants to the variable path in the file
        :param instrument: Name of the instrument that recorded the data in the file. Defaults to 'viirs'.
        """
        super(VIIRSSDRReader, self).__init__()
        if isinstance(filename_or_hdf_obj, str):
            self.reader = HDF5Reader(filename_or_hdf_obj)
        else:
            self.reader = filename_or_hdf_obj

        self.file_type_info = file_type_info
        self.filename = self.reader.filename
        self.filepath = self.reader.filepath
        self.satellite = self[guidebook.K_SATELLITE].lower()
        self.instrument = instrument

        # begin time
        sd = self[guidebook.K_AGGR_STARTDATE][0][0]
        st = self[guidebook.K_AGGR_STARTTIME][0][0]
        self.begin_time = time_attr_to_datetime(sd, st)

        # end time
        ed = self[guidebook.K_AGGR_ENDDATE][0][0]
        et = self[guidebook.K_AGGR_ENDTIME][0][0]
        self.end_time = time_attr_to_datetime(ed, et)

        # number of scans
        # item = self.file_type_info[guidebook.K_NUMSCANS]
        # if not isinstance(item, str):
        #     self.num_scans = item
        # else:
        #     self.num_scans = self[guidebook.K_NUMSCANS]

        # rows per scan line
        # item = self.file_type_info[guidebook.K_ROWSPERSCAN]
        # if not isinstance(item, str):
        #     self.rows_per_scan = guidebook.K_ROWSPERSCAN
        # else:
        #     self.rows_per_scan = self[guidebook.K_ROWSPERSCAN]

    @classmethod
    def handles_file(cls, filepath_or_hdf_reader, file_type_info):
        """Check if this class can handle the provided file.

        DEPRECATED
        """
        if isinstance(filepath_or_hdf_reader, str):
            hdf_reader = HDF5Reader(filepath_or_hdf_reader)
        else:
            hdf_reader = filepath_or_hdf_reader

        try:
            # let's see if we know stuff about this file
            if file_type_info[K_DATA_PATH] not in hdf_reader:
                # LOG.debug("Key '%s' not found in file '%s'", v, filepath)
                return False
            LOG.debug("Found all file type keys in '%s'", filepath)
            return True
        except StandardError:
            return False

    def __getitem__(self, item):
        known_item = self.file_type_info.get(item, item)
        if known_item is None:
            raise KeyError("Key 'None' was not found")

        if not isinstance(known_item, (str, unicode)):
            # Using FileVar class
            known_item = known_item.var_path
        LOG.debug("Loading %s from %s", known_item, self.filename)
        return self.reader[known_item]

    def scale_swath_data(self, data, scaling_factors):
        num_grans = len(scaling_factors)/2
        gran_size = data.shape[0]/num_grans
        scaling_mask = numpy.zeros(data.shape)
        for i in range(num_grans):
            start_idx = i * gran_size
            end_idx = start_idx + gran_size
            m = scaling_factors[i*2]
            b = scaling_factors[i*2 + 1]
            if m <= -999 or b <= -999:
                scaling_mask[start_idx:end_idx] = 1
            else:
                data[start_idx:end_idx] = m * data[start_idx:end_idx] + b

        scaling_mask = scaling_mask.astype(numpy.bool)
        return data, scaling_mask

    def get_swath_data(self, item, dtype=numpy.float32, fill=numpy.nan):
        """Retrieve the item asked for then set it to the specified data type, scale it, and mask it.
        """
        var_info = self.file_type_info.get(item)
        data = self[var_info.var_path].value.astype(dtype)

        # Get the scaling factors
        scaling_factors = None
        try:
            scaling_factors = list(self[var_info.scaling_path][:])
        except KeyError:
            LOG.debug("No scaling factors for %s", item)

        # Get the mask for the data (based on unscaled data)
        mask = None
        if scaling_factors is not None and var_info.scaling_mask_func is not None:
            mask = var_info.scaling_mask_func(data)
        elif scaling_factors is None and var_info.nonscaling_mask_func is not None:
            mask = var_info.nonscaling_mask_func(data)

        # Scale the data
        scaling_mask = None
        if scaling_factors is not None:
            data, scaling_mask = self.scale_swath_data(data, scaling_factors)

        if mask is not None:
            if scaling_factors is not None:
                mask |= scaling_mask
            data[mask] = fill

        return data

    def _compare(self, other, method):
        try:
            return method(self.begin_time, other.begin_time)
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

    @property
    def nadir_resolution(self):
        return None

    @property
    def edge_resolution(self):
        return None


class VIIRSSDRGeoReader(VIIRSSDRReader):
    """Generic VIIRS SDR Geolocation hdf5 reader.
    """
    def __init__(self, filename, file_type_info):
        super(VIIRSSDRGeoReader, self).__init__(filename, file_type_info)


class VIIRSSDRMultiReader(object):
    """Helper class to wrap multiple VIIRS SDR Files and assist in reading them.
    """
    SINGLE_FILE_CLASS = VIIRSSDRReader

    def __init__(self, file_type_info, filenames=None):
        """Load multiple HDF5 files, sorting by start time if necessary.
        """
        self.file_readers = []
        self._files_finalized = False
        self.file_type_info = file_type_info
        if filenames:
            self.add_files(filenames)
            self.finalize_files()

    @classmethod
    def handles_file(cls, fn_or_nc_obj, file_type_info):
        return cls.SINGLE_FILE_CLASS.handles_file(fn_or_nc_obj, file_type_info)

    def add_file(self, fn):
        if self._files_finalized:
            LOG.error("File reader has been finalized and no more files can be added")
            raise RuntimeError("File reader has been finalized and no more files can be added")
        self.file_readers.append(self.SINGLE_FILE_CLASS(fn, self.file_type_info))

    def add_files(self, filenames):
        for fn in filenames:
            self.add_file(fn)

    def finalize_files(self):
        self.file_readers = sorted(self.file_readers)
        if not all(fr.instrument == self.file_readers[0].instrument for fr in self.file_readers):
            LOG.error("Can't concatenate files because they are not for the same instrument")
            raise RuntimeError("Can't concatenate files because they are not for the same instrument")
        if not all(fr.satellite == self.file_readers[0].satellite for fr in self.file_readers):
            LOG.error("Can't concatenate files because they are not for the same satellite")
            raise RuntimeError("Can't concatenate files because they are not for the same satellite")
        self._files_finalized = True

    def __len__(self):
        return len(self.file_readers)

    @property
    def satellite(self):
        return self.file_readers[0].satellite

    @property
    def instrument(self):
        return self.file_readers[0].instrument

    @property
    def begin_time(self):
        return self.file_readers[0].begin_time

    @property
    def end_time(self):
        return self.file_readers[-1].end_time

    @property
    def nadir_resolution(self):
        return self.file_readers[0].nadir_resolution

    @property
    def edge_resolution(self):
        return self.file_readers[0].edge_resolution

    @property
    def filepaths(self):
        return [fr.filepath for fr in self.file_readers]

    def __getitem__(self, item):
        """Get a HDF5 variable as one logical item.

        This function will try its best to concatenate arrays together. If it can't figure out what to do it will
        return a list of each file's contents.

        Current Rules:
            - If each file's item is one element, sum those elements and return the sum
        """
        try:
            # Get the data element from the file and get the actual value out of the h5py object
            individual_items = [f[item].value for f in self.file_readers]
        except KeyError:
            LOG.error("Could not get '%s' from source files", item, exc_info=True)
            raise

        # This all assumes we are dealing with numpy arrays
        if len(individual_items[0]) == 1:
            # We are dealing with integers or floats, we should probably add them together
            return sum(individual_items)[0]
        else:
            # TODO: Other possible formations of data
            return individual_items

    def get_one(self, item):
        """Get a HDF5 variable from one file.

        This function should be used when we know we are getting a representative value from one single file. For
        example, if we are looking for something that describes all the files and *should* be the same in all of them,
        then we only want one of those elements.
        """
        val = self.file_readers[0][item]
        if hasattr(val, "value"):
            return val.value
        else:
            return val

    def write_var_to_flat_binary(self, item, filename, dtype=numpy.float32):
        """Write multiple HDF5 variables to disk as one concatenated flat binary file.

        Data is written incrementally to reduce memory usage.

        :param item: Variable name to retrieve from these files
        :param filename: Filename to write to
        """
        LOG.debug("Writing binary data for '%s' to file '%s'", item, filename)
        try:
            with open(filename, "w") as file_obj:
                file_appender = FileAppender(file_obj, dtype)
                for file_reader in self.file_readers:
                    single_array = file_reader.get_swath_data(item)
                    file_appender.append(single_array)
        except StandardError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        LOG.debug("File %s has shape %r", filename, file_appender.shape)
        return file_appender.shape

    def get_number_of_scans(self):
        return self.file_readers[0].get_number_of_scans()

    def get_rows_per_scan(self):
        return self.file_readers[0].get_rows_per_scan()


class VIIRSSDRGeoMultiReader(VIIRSSDRMultiReader):
    """Helper class to wrap multiple VIIRS Geolocation SDR Files and assist in reading them.
    """
    SINGLE_FILE_CLASS = VIIRSSDRGeoReader

