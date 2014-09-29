#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2013 Space Science and Engineering Center (SSEC),
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
# Written by David Hoese    January 2013
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
""" Time utilities and time zone information

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import re
import logging
import datetime

log = logging.getLogger(__name__)


class UTC(datetime.tzinfo):
    """Time zone class for UTC
    """
    ZERO = datetime.timedelta(0)

    def utcoffset(self, dt):
        return self.ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return self.ZERO


def utc_now():
    return datetime.datetime.utcnow().replace(tzinfo=UTC())

### Parse ISO8601 Times ###
ISO8601_REGEX = r'^(?P<year>-?(?:[1-9][0-9]*)?[0-9]{4})-?(?P<month>1[0-2]|0[1-9])-?(?P<day>3[0-1]|0[1-9]|[1-2][0-9])T(?P<hour>2[0-3]|[0-1][0-9]):?(?P<minute>[0-5][0-9]):?(?P<second>[0-5][0-9])(?P<ms>\.[0-9]+)??(?P<timezone>Z|[+-](?:2[0-3]|[0-1][0-9]):?[0-5][0-9])?$'
iso8601_re = re.compile(ISO8601_REGEX)


def iso8601(s):
    """Convert ISO8601 string to datetime object"""
    match = iso8601_re.match(s)
    if match is None:
        raise ValueError("Invalid timestamp format '%s'" % (s,))

    d = match.groupdict()
    if 'ms' in d and d['ms'] is not None:
        ms = int(d['ms'][1:4])*1000
    else:
        ms = 0
    return datetime.datetime(int(d['year']), int(d['month']), int(d['day']),
                             int(d['hour']), int(d['minute']), int(d['second']), ms)
