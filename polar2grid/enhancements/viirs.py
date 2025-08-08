#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2025 Space Science and Engineering Center (SSEC),
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
"""Enhancement functions for VIIRS."""

import numpy as np
from trollimage.xrimage import XRImage
from satpy.enhancements.wrappers import using_map_blocks


def cloud_layers_lmh(img: XRImage) -> XRImage:
    """Convert bit-mask CloudLayer to Low-Medium-High categories.

    This is done in the CIRA version of the product for easier readability.

    Data is a bit-mask of (0=clear), 1 first layer, 2 second layer, 4 third
    layer, 8 fourth layer, 16 fifth layer. The first and second layers are
    grouped into a "Low" layer, third and fourth layers are grouped into
    a "Mid" layer, and the fifth layer is called "High". This function groups
    these 3 layer types with the final output being
    Clear (0), Low (1), Mid (2), Mid + Low (3), High (4), High + Low (5),
    High + Mid (6), and High + Mid + Low (7).

    """
    return _cloud_layers_lmh(img.data)


@using_map_blocks
def _cloud_layers_lmh(data_np: np.ndarray) -> np.ndarray:
    data_out = np.zeros_like(data_np)
    data_out[data_out & 0b00011] += 1  # Low
    data_out[data_out & 0b01100] += 2  # Mid
    data_out[data_out & 0b10000] += 4  # High
    return data_out
