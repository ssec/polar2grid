#!/usr/bin/env python
# encoding: utf-8
""" Time utilities and time zone information

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

import os
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
