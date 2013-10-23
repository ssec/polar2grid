#!/usr/bin/env python
# encoding: utf-8
"""
Simple objects to assist in reading VIIRS data from hdf5 (.h5) files.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Oct 2013
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

    Written by David Hoese    October 2013
    University of Wisconsin-Madison
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

import h5py
import numpy

from . import guidebook
from polar2grid.core import UTC
from polar2grid.core.fbf import check_stem, file_appender, data_type_to_fbf_type

import os
import sys
import re
import logging
from datetime import datetime, timedelta

log = logging.getLogger(__name__)
UTC = UTC()


class HDF5Reader(object):
    """Generic HDF5 reading class.
    """
    def __init__(self, filename):
        self._h5_handle = h5py.File(filename, 'r')
        self.file_items = {}
        self._h5_handle.visititems(self._visit_items)

    def _visit_items(self, name, obj):
        """Look at each variable in the HDF file and record its attributes.

        We also store the variable name because sometimes h5py gives you an
        unhelpful/weird KeyError if it doesn't have that key.
        """
        self.file_items[name] = obj
        for attr_name, attr_obj in obj.attrs.items():
            self.file_items[name + "." + attr_name] = attr_obj

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
    whole_sec,s_us = st[:-1].split(".")
    s_us = int(s_us)
    s_dt = datetime.strptime(d + whole_sec, "%Y%m%d%H%M%S").replace(tzinfo=UTC, microsecond=s_us)
    return s_dt


class VIIRSSDRReader(HDF5Reader):
    """VIIRS Data SDR hdf5 reader.

    Handles all the difficulties of reading SDR data (masking, scaling, etc.)
    """
    def __init__(self, filename, known_file_info=None):
        """Initialize VIIRS SDR Reader and get information that we can derive by the file name.

        :param filename: HDF5 filename for a VIIRS data SDR file.
        :param known_file_info: Dictionary mapping file patterns to information we know about that type of file pattern.
                                Defaults to ``SV_FILE_GUIDE`` in the VIIRS ``guidebook``.
        """
        super(VIIRSSDRReader, self).__init__(filename)
        known_file_info = known_file_info or guidebook.SV_FILE_GUIDE
        self.filename = os.path.basename(filename)
        self.filepath = os.path.realpath(filename)
        self.file_pattern = self.find_file_pattern(self.filename, known_file_info.keys())
        self.known_file_info = known_file_info[self.file_pattern]

        # Get some basic information about this file
        self.start_time = self.get_start_time()
        self.end_time = self.get_end_time()

    def find_file_pattern(self, filename, file_patterns):
        for file_pattern in file_patterns:
            if re.match(file_pattern, filename) is not None:
                return file_pattern

        # We couldn't find a pattern
        msg = "%s doesn't know how to handle '%s'" % (self.__class__.__name__, filename,)
        log.error(msg)
        raise ValueError(msg)

    def __getitem__(self, item):
        item = self.known_file_info.get(item, item)
        log.debug("Loading %s from %s", item, self.filename)
        return super(VIIRSSDRReader, self).__getitem__(item)

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
                scaling_mask[start_idx : end_idx] = 1
            else:
                data[start_idx : end_idx] = m * data[start_idx : end_idx] + b

        scaling_mask = scaling_mask.astype(numpy.bool)
        return data, scaling_mask

    def get_swath_data(self, item, dtype=numpy.float32, fill=numpy.nan):
        """Retrieve the item asked for then set it to the specified data type, scale it, and mask it.
        """
        data = self[item].value.astype(dtype)

        # Get the scaling factors
        scaling_factors = None
        if item in guidebook.SCALING_FACTORS:
            try:
                scaling_factors = list(self[guidebook.SCALING_FACTORS[item]][:])
            except KeyError:
                log.info("No scaling factors for %s", item)

        # Get the mask for the data (based on unscaled data)
        mask = None
        if item in guidebook.MISSING_GUIDE:
           mask = guidebook.MISSING_GUIDE[item][scaling_factors is not None](data)

        # Scale the data
        if scaling_factors is not None:
           data,scaling_mask = self.scale_swath_data(data, scaling_factors)

        if mask is not None:
            if scaling_factors is not None:
                mask |= scaling_mask
            data[mask] = fill

        return data

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

    def get_start_time(self):
        sd = self[guidebook.K_AGGR_STARTDATE][0][0]
        st = self[guidebook.K_AGGR_STARTTIME][0][0]
        return time_attr_to_datetime(sd, st)

    def get_end_time(self):
        ed = self[guidebook.K_AGGR_ENDDATE][0][0]
        et = self[guidebook.K_AGGR_ENDTIME][0][0]
        return time_attr_to_datetime(ed, et)


class VIIRSSDRGeoReader(VIIRSSDRReader):
    """Generic VIIRS SDR Geolocation hdf5 reader.
    """
    def __init__(self, filename, known_file_info=None):
        known_file_info = known_file_info or guidebook.GEO_FILE_GUIDE
        super(VIIRSSDRGeoReader, self).__init__(filename, known_file_info=known_file_info)


class VIIRSSDRMultiReader(object):
    """Helper class to wrap multiple VIIRS SDR Files and assist in reading them.
    """
    SINGLE_FILE_CLASS = VIIRSSDRReader

    def __init__(self, filenames, known_file_info=None, sort_files=True):
        """Load multiple HDF5 files, sorting by start time if necessary.
        """
        # TODO: Add methods for verifying that all of the files we just loaded have similar information
        # Like same satellite, same instrument, etc.
        # If they aren't all the same then we need to tell the user that their files aren't supported
        self.files = [self.SINGLE_FILE_CLASS(fn, known_file_info=known_file_info) for fn in filenames]

        if sort_files:
            self.files = sorted(self.files)

    def __len__(self):
        return len(self.files)

    def __getitem__(self, item):
        """Get a HDF5 variable as one array.

        This function will try its best to concatenate arrays together. If it can't figure out what to do it will
        return a list of each file's contents.
        """
        raise NotImplementedError("Can not get items from MultiReaders yet")

    def write_var_to_flat_binary(self, var, stem=None, filename=None):
        """Write multiple HDF5 variables to disk as one concatenated flat binary file.

        Data is written incrementally to reduce memory usage.

        :param var: Variable name to retrieve
        :param stem: Filename stem if the file should follow traditional FBF naming conventions
        :param filename: Filename to save to if ``stem`` is not provided.
        """
        if stem is None and filename is None:
            msg = "No stem was provided during flat binary write for variable '%s'" % (var,)
            log.error(msg)
            raise ValueError(msg)

        # Figure out what filename we should save the data to first
        if stem is None:
            if os.path.exists(filename):
                log.error("File exists already: '%s'", filename)
                raise ValueError("File exists already: '%s'", filename)
            tmp_fn = filename
        else:
            check_stem(stem)
            tmp_fn = stem + ".fbftmp"

        tmp_file = file(tmp_fn, 'wb')
        fbf_fa = None
        for fo in self.files:
            try:
                data = fo.get_swath_data(var)
                if fbf_fa is None:
                    fbf_fa = file_appender(tmp_file, dtype=data.dtype)
                fbf_fa.append(data)
            except StandardError:
                log.error("Could not write '%s' to file, see debug messages for more info" % (var,))
                log.debug("FBF Write Exception", exc_info=True)

                try:
                    log.debug("Removing temporary FBF file: '%s'", tmp_fn)
                    tmp_file.close()
                    os.remove(tmp_fn)
                except StandardError:
                    log.error("Could not remove FBF temporary file: %s", tmp_fn)

                raise

        log.info("Swath data for variable '%s' loaded from %d files; rows=%d; cols=%d", var, len(self), fbf_fa.shape[0], fbf_fa.shape[1])

        # Close all file objects
        tmp_file.close()

        # If they gave us a stem then rename the file to a conventional FBF name
        if stem is not None:
            # FIXME: Put this polar2grid.core.fbf
            dtype_to_fbf_type = {
                numpy.float32: "real4"
            }
            filename = stem + '.' + dtype_to_fbf_type[fbf_fa.dtype.type] + '.' + '.'.join(str(x) for x in reversed(fbf_fa.shape))
            log.debug("Renaming temporary FBF '%s' to '%s'", tmp_fn, filename)
            os.rename(tmp_fn, filename)

        log.info("Swath data for variable '%s' stored in file '%s'", var, filename)

        return filename


class VIIRSSDRGeoMultiReader(VIIRSSDRMultiReader):
    """Helper class to wrap multiple VIIRS Geolocation SDR Files and assist in reading them.
    """
    SINGLE_FILE_CLASS = VIIRSSDRGeoReader
    pass


def main():
    import doctest
    return doctest.testmod()

if __name__ == "__main__":
    sys.exit(main())
