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
"""The METimage Level 1B reader operates on Radiance (RAD) NetCDF4 files from
the Visible/Infrared Imager (VII), also known as METimage, on board the
EUMETSAT Metop Second Generation A (Metop-SG-A) satellites.

Files are distributed by EUMETSAT with long names following the WMO
convention. They typically look like::

    W_XX-EUMETSAT-Darmstadt,SAT,SGA1-VII-1B-RAD_C_EUMT_20260518110117_G_V_20260518102859_20260518102958_C_N_T__.nc

The METimage Level 1B reader can be specified to the ``polar2grid.sh`` script
with the reader name ``metimage_l1b_nc``.

This reader's default remapping algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--weight-delta-max`` option is set to 40 and
``--weight-distance-max`` is set to 2.

All 20 imaging bands are loaded by default, as is the ``true_color``
composite. Band products are named after their nominal wavelength in
nanometers. The 11 shortest wavelength bands are calibrated to reflectance
(percent) and the 9 longest to brightness temperature (Kelvin).

+--------------------+--------------------------------------------------------+
| Product Name       | Description                                            |
+====================+========================================================+
| vii_443            | Band at 0.443um Reflectance                            |
+--------------------+--------------------------------------------------------+
| vii_555            | Band at 0.555um Reflectance                            |
+--------------------+--------------------------------------------------------+
| vii_668            | Band at 0.668um Reflectance                            |
+--------------------+--------------------------------------------------------+
| vii_752            | Band at 0.752um Reflectance                            |
+--------------------+--------------------------------------------------------+
| vii_763            | Band at 0.763um Reflectance                            |
+--------------------+--------------------------------------------------------+
| vii_865            | Band at 0.865um Reflectance                            |
+--------------------+--------------------------------------------------------+
| vii_914            | Band at 0.914um Reflectance                            |
+--------------------+--------------------------------------------------------+
| vii_1240           | Band at 1.240um Reflectance                            |
+--------------------+--------------------------------------------------------+
| vii_1375           | Band at 1.375um Reflectance                            |
+--------------------+--------------------------------------------------------+
| vii_1630           | Band at 1.630um Reflectance                            |
+--------------------+--------------------------------------------------------+
| vii_2250           | Band at 2.250um Reflectance                            |
+--------------------+--------------------------------------------------------+
| vii_3740           | Band at 3.740um Brightness Temperature                 |
+--------------------+--------------------------------------------------------+
| vii_3959           | Band at 3.959um Brightness Temperature                 |
+--------------------+--------------------------------------------------------+
| vii_4050           | Band at 4.050um Brightness Temperature                 |
+--------------------+--------------------------------------------------------+
| vii_6725           | Band at 6.725um Brightness Temperature                 |
+--------------------+--------------------------------------------------------+
| vii_7325           | Band at 7.325um Brightness Temperature                 |
+--------------------+--------------------------------------------------------+
| vii_8540           | Band at 8.540um Brightness Temperature                 |
+--------------------+--------------------------------------------------------+
| vii_10690          | Band at 10.690um Brightness Temperature                |
+--------------------+--------------------------------------------------------+
| vii_12020          | Band at 12.020um Brightness Temperature                |
+--------------------+--------------------------------------------------------+
| vii_13345          | Band at 13.345um Brightness Temperature                |
+--------------------+--------------------------------------------------------+
| true_color         | Rayleigh corrected true color RGB                      |
+--------------------+--------------------------------------------------------+

Additional RGB composites provided by Satpy for this instrument, such as
``natural_color``, ``snow``, ``dust``, and ``day_microphysics``, are not
loaded by default but can still be requested by name with the ``--products``
flag. Use ``--list-products-all`` to see everything available for a set of
input files.

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup

from satpy import DataQuery

from ._base import ReaderProxyBase

PREFERRED_CHUNK_SIZE: int = 3144  # roughly the number of columns in a granule

REFLECTANCE_BANDS = [
    "vii_443",
    "vii_555",
    "vii_668",
    "vii_752",
    "vii_763",
    "vii_865",
    "vii_914",
    "vii_1240",
    "vii_1375",
    "vii_1630",
    "vii_2250",
]
BT_BANDS = [
    "vii_3740",
    "vii_3959",
    "vii_4050",
    "vii_6725",
    "vii_7325",
    "vii_8540",
    "vii_10690",
    "vii_12020",
    "vii_13345",
]
ALL_BANDS = REFLECTANCE_BANDS + BT_BANDS
COMPOSITES = ["true_color"]

# Satpy's product naming is kept as-is for this reader
PRODUCT_ALIASES = {}

DEFAULT_PRODUCTS = ALL_BANDS + COMPOSITES
P2G_PRODUCTS = ALL_BANDS + COMPOSITES

FILTERS = {
    "day_only": {
        "standard_name": [
            "toa_bidirectional_reflectance",
            "true_color",
        ],
    },
    "night_only": {},
}


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULT_PRODUCTS

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return P2G_PRODUCTS

    @property
    def _aliases(self) -> dict[str, DataQuery | str]:
        return PRODUCT_ALIASES


def add_reader_argument_groups(
    parser: ArgumentParser, group: _ArgumentGroup | None = None
) -> tuple[_ArgumentGroup | None, _ArgumentGroup | None]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="METimage L1B Reader")

    group.add_argument(
        "--orthorectify",
        dest="orthorect",
        action="store_true",
        help="Apply the digital elevation model (DEM) based orthorectification "
        "correction to longitude and latitude. Defaults to off.",
    )

    return group, None
