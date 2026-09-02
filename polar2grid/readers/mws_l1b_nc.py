#!/usr/bin/env python3
# Copyright (C) 2026 Space Science and Engineering Center (SSEC),
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
"""The Metop-SGA1 MicroWave Sounder (MWS) reader is for reading L1B files
for the MWS instrument.

These files are NetCDF4 files distributed by EUMETSAT. The reader can be
specified with the ``polar2grid.sh`` command using the ``mws_l1b_nc`` reader
name.

MWS is a cross-track scanning microwave sounder with 24 channels between
23.8GHz and 229GHz. Every channel is a top of atmosphere brightness
temperature in Kelvin at a nadir resolution of 17km. Products are named after
the MWS band number they come from.

This reader's default resampling algorithm is ``nearest`` for nearest
neighbor resampling.

The MWS reader provides the following products:

+--------------+------------------------------------------------------------------------+
| Product Name | Description                                                            |
+==============+========================================================================+
| 1            | Band 1 (23.8 GHz, QH) Brightness Temperature                           |
+--------------+------------------------------------------------------------------------+
| 2            | Band 2 (31.4 GHz, QH) Brightness Temperature                           |
+--------------+------------------------------------------------------------------------+
| 3            | Band 3 (50.3 GHz, QH) Brightness Temperature                           |
+--------------+------------------------------------------------------------------------+
| 4            | Band 4 (52.8 GHz, QH) Brightness Temperature                           |
+--------------+------------------------------------------------------------------------+
| 5            | Band 5 (53.246 +/-0.08 GHz, QH) Brightness Temperature                 |
+--------------+------------------------------------------------------------------------+
| 6            | Band 6 (53.596 +/-0.115 GHz, QH) Brightness Temperature                |
+--------------+------------------------------------------------------------------------+
| 7            | Band 7 (53.948 +/-0.081 GHz, QH) Brightness Temperature                |
+--------------+------------------------------------------------------------------------+
| 8            | Band 8 (54.4 GHz, QH) Brightness Temperature                           |
+--------------+------------------------------------------------------------------------+
| 9            | Band 9 (54.94 GHz, QH) Brightness Temperature                          |
+--------------+------------------------------------------------------------------------+
| 10           | Band 10 (55.5 GHz, QH) Brightness Temperature                          |
+--------------+------------------------------------------------------------------------+
| 11           | Band 11 (57.290344 GHz, QH) Brightness Temperature                     |
+--------------+------------------------------------------------------------------------+
| 12           | Band 12 (57.290344 +/-0.217 GHz, QH) Brightness Temperature            |
+--------------+------------------------------------------------------------------------+
| 13           | Band 13 (57.290344 +/-0.3222 +/-0.048 GHz, QH) Brightness Temperature  |
+--------------+------------------------------------------------------------------------+
| 14           | Band 14 (57.290344 +/-0.3222 +/-0.022 GHz, QH) Brightness Temperature  |
+--------------+------------------------------------------------------------------------+
| 15           | Band 15 (57.290344 +/-0.3222 +/-0.01 GHz, QH) Brightness Temperature   |
+--------------+------------------------------------------------------------------------+
| 16           | Band 16 (57.290344 +/-0.3222 +/-0.0045 GHz, QH) Brightness Temperature |
+--------------+------------------------------------------------------------------------+
| 17           | Band 17 (89.0 GHz, QV) Brightness Temperature                          |
+--------------+------------------------------------------------------------------------+
| 18           | Band 18 (166.0 GHz, QH) Brightness Temperature                         |
+--------------+------------------------------------------------------------------------+
| 19           | Band 19 (183.311 +/-7.0 GHz, QV) Brightness Temperature                |
+--------------+------------------------------------------------------------------------+
| 20           | Band 20 (183.311 +/-4.5 GHz, QV) Brightness Temperature                |
+--------------+------------------------------------------------------------------------+
| 21           | Band 21 (183.311 +/-3.0 GHz, QV) Brightness Temperature                |
+--------------+------------------------------------------------------------------------+
| 22           | Band 22 (183.311 +/-1.8 GHz, QV) Brightness Temperature                |
+--------------+------------------------------------------------------------------------+
| 23           | Band 23 (183.311 +/-1.0 GHz, QV) Brightness Temperature                |
+--------------+------------------------------------------------------------------------+
| 24           | Band 24 (229.0 GHz, QV) Brightness Temperature                         |
+--------------+------------------------------------------------------------------------+

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
import logging

from ._base import ReaderProxyBase

logger = logging.getLogger(__name__)

FILTERS = {}

# Satpy names the MWS channels after their band number. Keep them in numerical
# order (not sorted order) so product listings read 1, 2, ... 24.
BT_BANDS = [str(band_num) for band_num in range(1, 25)]


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return BT_BANDS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return BT_BANDS

    @property
    def _aliases(self) -> dict[str, str]:
        """Get mapping of Polar2Grid names to Satpy names.

        The Satpy band names are used as-is so no aliases are needed.

        """
        return {}


def add_reader_argument_groups(
    parser: ArgumentParser, group: _ArgumentGroup | None = None
) -> tuple[_ArgumentGroup | None, _ArgumentGroup | None]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="MWS L1b Reader")
    return group, None
