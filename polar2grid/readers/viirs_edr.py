# Copyright (C) 2023 Space Science and Engineering Center (SSEC),
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
"""The VIIRS EDR Reader operates on Environmental Data Record (SDR) HDF5 files
from the Suomi National Polar-orbiting Partnership's (NPP), the NOAA20, or the
NOAA-21 Visible/Infrared Imager Radiometer Suite (VIIRS) instrument. The VIIRS
EDR reader requires filenames to match one of a couple different standard
filename schemes used for official products. EDR files are typically named
as below::

    JRR-AOD_v3r2_npp_s202307230941369_e202307230943011_c202307231038217.nc

The VIIRS EDR reader supports most JPSS Risk Reduction (JRR) enterprise algorithm
output. The VIIRS EDR reader can be specified to the ``polar2grid.sh`` script
with the reader name ``viirs_edr``.

This reader's default remapping algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--weight-delta-max`` parameter set to 40 and the
``--weight-distance-max`` parameter set to 2.

+---------------------------+-----------------------------------------------------+
| Product Name              | Description                                         |
+===========================+=====================================================+
| surf_refl_i01             | I01 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| surf_refl_i02             | I02 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| surf_refl_i03             | I03 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| surf_refl_m01             | M01 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| surf_refl_m02             | M02 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| surf_refl_m03             | M03 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| surf_refl_m04             | M04 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| surf_refl_m05             | M05 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| surf_refl_m07             | M07 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| surf_refl_m08             | M08 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| surf_refl_m10             | M10 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| surf_refl_m11             | M11 Surface Reflectance Band                        |
+---------------------------+-----------------------------------------------------+
| true_color_surf           | Ratio sharpened surface true color                  |
+---------------------------+-----------------------------------------------------+
| false_color_surf          | Ratio sharpened surface false color                 |
+---------------------------+-----------------------------------------------------+
| NDVI                      | Normalized Difference Vegetation Index              |
+---------------------------+-----------------------------------------------------+
| EVI                       | Enhanced Vegetation Index                           |
+---------------------------+-----------------------------------------------------+
| CldTopTemp                | Cloud Top Temperature                               |
+---------------------------+-----------------------------------------------------+
| CldTopHght                | Cloud Top Height                                    |
+---------------------------+-----------------------------------------------------+
| AOD550                    | Aerosol Optical Depth                               |
+---------------------------+-----------------------------------------------------+
| VLST                      | Land Surface Temperature                            |
+---------------------------+-----------------------------------------------------+

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup, BooleanOptionalAction
from typing import Optional

from satpy import DataQuery

from ._base import ReaderProxyBase

PREFERRED_CHUNK_SIZE: int = 6400

I_PRODUCTS = ["surf_refl_I{:02d}".format(chan_num) for chan_num in range(1, 4)]
M_PRODUCTS = ["surf_refl_M{:02d}".format(chan_num) for chan_num in range(1, 12) if chan_num not in (6, 9)]
SURF_COMPS = ["true_color_surf", "false_color_ref"]
OTHER_PRODS = ["NDVI", "EVI", "CldTopTemp", "CldTopHght", "AOD550", "VLST"]

PRODUCT_ALIASES = {}
SURF_ALIASES = []

for surf_band in I_PRODUCTS + M_PRODUCTS:
    PRODUCT_ALIASES[surf_band.lower()] = surf_band
    SURF_ALIASES.append(surf_band.lower())

DEFAULT_PRODUCTS = SURF_ALIASES + SURF_COMPS + OTHER_PRODS
P2G_PRODUCTS = SURF_ALIASES + SURF_COMPS + OTHER_PRODS

FILTERS = {
    "day_only": {
        "standard_name": [
            "surface_bidirectional_reflectance",
            "true_color",
            "false_color",
            "natural_color",
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

    def get_all_products(self):
        """Get all polar2grid products that could be loaded."""
        return P2G_PRODUCTS

    @property
    def _aliases(self) -> dict[str, DataQuery | str]:
        return PRODUCT_ALIASES


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="VIIRS EDR Reader")

    group.add_argument(
        "--filter-veg",
        action=BooleanOptionalAction,
        default=True,
        help="Filter vegetation index variables by various quality flags. Default is enabled.",
    )
    group.add_argument(
        "--aod-qc-filter",
        default=1,
        type=_int_or_none,
        choices=[None, 0, 1, 2, 3],
        help="Filter AOD550 variable by QCAll variable. Value specifies the maximum "
        "quality to include (0-high, 1-medium, 2-low, 3-no retrieval). Defaults to "
        "1 which means medium and high quality data are included.",
    )

    return group, None


def _int_or_none(value: str) -> None | int:
    if value.lower() == "none":
        return None
    return int(value)
