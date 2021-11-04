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
from satpy.enhancements import colorize as _colorize
from satpy.enhancements import palettize as _palettize

from polar2grid.add_colormap import parse_color_table_file
from polar2grid.utils.config import get_polar2grid_home


def temperature_difference(img, min_stretch, max_stretch, **kwargs):
    """Scale data linearly with a buffer on the edges for over limit data.

    Basic behavior is to put -10 to 10 range into 5 to 205 with clipped data
    set to 4 and 206.

    """
    img.crude_stretch(min_stretch, max_stretch)
    # we assume uint8 images for legacy AWIPS comparisons
    offset = 1 / 255.0
    factor = (205.0 - 5.0) / 255.0
    img.data = img.data * factor
    img.data.data = np.clip(img.data.data, -offset, factor + offset)  # 4 and 206 offset
    img.data = img.data + 5 * offset  # lower bound of 5
    return img


def _parse_palettes_for_p2g_cmap(palettes: list):
    for palette in palettes:
        filename = palette.get("filename", "")
        if not filename or (filename.endswith(".npy") or filename.endswith(".npz")):
            yield palette
            continue
        p2g_home = get_polar2grid_home()
        filename = filename.replace("$POLAR2GRID_HOME", p2g_home)
        filename = filename.replace("$GEO2GRID_HOME", p2g_home)
        colors = parse_color_table_file(filename)
        values = [color[0] for color in colors]
        colors = [color[1:] for color in colors]
        new_palette = {
            "colors": colors,
            "values": values,
        }
        yield new_palette


def colorize(img, **kwargs):
    kwargs["palettes"] = list(_parse_palettes_for_p2g_cmap(kwargs["palettes"]))
    return _colorize(img, **kwargs)


def palettize(img, **kwargs):
    kwargs["palettes"] = list(_parse_palettes_for_p2g_cmap(kwargs["palettes"]))
    return _palettize(img, **kwargs)
