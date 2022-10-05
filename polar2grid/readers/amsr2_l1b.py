#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2016-2021 Space Science and Engineering Center (SSEC),
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
"""AMSR2 L1B files contain various parameters from the GCOM-W1 AMSR2 instrument.

This reader can be used by specifying the reader name
``amsr2_l1b`` to the ``polar2grid.sh`` script.
Supported files usually have the following naming scheme::

    GW1AM2_201607201808_128A_L1DLBTBR_1110110.h5

This reader's default remapping algorithm is ``nearest`` for nearest
neighbor resampling due to the instruments scan pattern and swath shape.
The ``--distance_upper_bound`` flag defaults to 12.

Currently this reader provides only the following datasets:

+---------------------------+-----------------------------------------------------------+
| Product Name              | Description                                               |
+===========================+===========================================================+
| btemp_36.5v               | Brightness Temperature 36.5GHz Polarization Vertical      |
+---------------------------+-----------------------------------------------------------+
| btemp_36.5h               | Brightness Temperature 36.5GHz Polarization Horizontal    |
+---------------------------+-----------------------------------------------------------+
| btemp_89.0av              | Brightness Temperature 89.0GHz A Polarization Vertical    |
+---------------------------+-----------------------------------------------------------+
| btemp_89.0ah              | Brightness Temperature 89.0GHz A Polarization Horizontal  |
+---------------------------+-----------------------------------------------------------+
| btemp_89.0bv              | Brightness Temperature 89.0GHz B Polarization Vertical    |
+---------------------------+-----------------------------------------------------------+
| btemp_89.0bh              | Brightness Temperature 89.0GHz B Polarization Horizontal  |
+---------------------------+-----------------------------------------------------------+

Special AMSR2 Naval Research Lab (NRL) PNG Scaling
--------------------------------------------------

A common use case for the AMSR2 L1B reader is to generate PNG images similar
to those generated by the U.S. Naval Research Lab (NRL) with a colormap and
coastlines. This requires using an alternate non-default scaling configuration
provided in the tarball. It can be used by providing the
``--extra-config-path $POLAR2GRID_HOME/example_enhancements/amsr2_png``
flag when generating AMSR2 L1B GeoTIFFs. This allows the scaling provided
in the ``$POLAR2GRID_HOME/example_enhancements/amsr2_png/enhancements/generic.yaml``
file to be used.  Once this rescaling has been done, colormap files can be 
found in ``$POLAR2GRID_HOME/colormaps`` which can then be applied using the
the `add_colormap.sh` script.

See the example section :doc:`../examples/amsr2_example`
for more information on generating these NRL-like PNGs. 

"""
from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from satpy import DataQuery

from ._base import ReaderProxyBase

DEFAULT_CHANNELS = [
    # "btemp_10.7v",
    # "btemp_10.7h",
    "btemp_36.5v",
    "btemp_36.5h",
    "btemp_89.0av",
    "btemp_89.0ah",
    "btemp_89.0bv",
    "btemp_89.0bh",
]


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULT_CHANNELS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return DEFAULT_CHANNELS

    @property
    def _aliases(self) -> dict[str, DataQuery]:
        return {}


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="AMSR2 L1B Reader")
    return group, None
