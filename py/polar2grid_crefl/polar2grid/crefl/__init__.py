#!/usr/bin/env python
# encoding: utf-8
"""Polar2grid frontend for corrected reflectance (crefl) products created
for VIIRS and MODIS data.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Sept 2014
:license:      GNU GPLv3
:revision: $Id$
"""
__docformat__ = "restructuredtext en"

from .crefl2swath import Frontend, add_frontend_argument_groups
