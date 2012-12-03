#!/usr/bin/env python
# encoding: utf-8
"""Simple backend to just passively 'produce' the binary files that are
provided.

FUTURE: Provide rescaled binaries.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

from polar2grid.core import roles
from polar2grid.core.constants import GRIDS_ANY

class Backend(roles.BackendRole):
    def __init__(self):
        pass

    def can_handle_inputs(self, sat, instrument, kind, band, data_kind):
        return GRIDS_ANY

    def create_product(self, sat, instrument,
            kind, band, data_kind, data):
        pass

