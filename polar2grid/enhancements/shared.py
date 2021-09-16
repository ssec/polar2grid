#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2021 Space Science and Engineering Center (SSEC),
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
"""Enhancement functions shared between multiple sensors."""

import numpy as np


def temperature_difference(img, min_stretch, max_stretch, **kwargs):
    """Scale data linearly with a buffer on the edges for over limit data.

    Basic behavior is to put -10 to 10 range into 5 to 205 with clipped data
    set to 4 and 206.

    """

    img.crude_stretch(min_stretch, max_stretch)
    # we assume uint8 images for legacy AWIPS comparisons
    offset = 1 / 255.0
    img.data = img.data * 0.8
    img.data = np.clip(img.data, -offset, 0.8 + offset)  # 4 and 206 offset
    img.data + img.data + 5 * offset  # lower bound of 5
    return img
