#!/usr/bin/env python3
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
"""Flat binary file utilities

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2014
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

import numpy
import logging

LOG = logging.getLogger(__name__)


class ArrayAppender(object):
    """wrapper for a numpy array object which gives it a binary data append usable with "catenate"
    """
    def __init__(self, nparray=None):
        if nparray:
            self.A = nparray
            self.shape = nparray.shape

    def append(self, data):
        # append new rows to the data
        if self.A is None:
            self.A = numpy.array(data)
            self.shape = data.shape
        else:
            self.A = numpy.concatenate((self.A, data))
            self.shape = self.A.shape
        LOG.debug('array shape is now %s' % repr(self.A.shape))


class FileAppender(object):
    """wrapper for a file object which gives it a binary data append usable with "catenate"
    """
    def __init__(self, file_obj, dtype):
        self.file_obj = file_obj
        self.dtype = dtype
        self.shape = (0, 0)

    def append(self, data):
        # append new rows to the data
        if data is None:
            return
        inform = data.astype(self.dtype) if self.dtype != data.dtype else data
        inform.tofile(self.file_obj)
        self.shape = (self.shape[0] + inform.shape[0],) + data.shape[1:]
        LOG.debug('%d rows in output file' % self.shape[0])
