#!/usr/bin/env python
# encoding: utf-8
"""Various image sharpening functions.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         April 2013
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

    Written by David Hoese    April 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

from .fbf import Workspace
import numpy

import os
import sys

def rgb_ratio_sharpen(band1_hires, band1_lores, band2, band3, fill_value=None):
    """Sharpen 2 remapped bands by using the ratio of a
    a third band in high resolution and low resolution remapped versions.
    All bands must be remapped to the same grid.
    """
    if fill_value is not None:
        fill_mask = (band1_hires == fill_value) | (band2 == fill_value) | (band3 == fill_value)

    ratio = band1_hires / band1_lores
    sharp2 = ratio * band2
    sharp3 = ratio * band3

    # Make sure fill values are respected
    if fill_value is not None:
        sharp2[ fill_mask ] = fill_value
        sharp3[ fill_mask ] = fill_value

    return band1_hires,sharp2,sharp3

def rgb_ratio_sharpen_fbf(band1_hires_fn, band1_lores_fn, band2_fn, band3_fn, fill_value=None, workspace_dir='.'):
    """Simple wrapper of `rgb_ratio_sharpen` to load binary files from their
    filenames.
    """
    W = Workspace(workspace_dir)
    band1_hires = getattr(W, band1_hires_fn.split(".")[0])
    band1_lores = getattr(W, band1_lores_fn.split(".")[0])
    band2 = getattr(W, band2_fn.split(".")[0])
    band3 = getattr(W, band3_fn.split(".")[0])
    return rgb_ratio_sharpen(band1_hires, band1_lores, band2, band3, fill_value=fill_value)


