#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2016 Space Science and Engineering Center (SSEC),
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
#
#     Written by David Hoese    March 2016
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""
The VIIRS Level 1B Reader operates on NASA Level 1B (L1B) NetCDF files.

The files are from the Suomi National Polar-orbiting Partnership's (NPP) Visible/Infrared
Imager Radiometer Suite (VIIRS) instrument. The VIIRS L1B reader analyzes
the user provided filenames to determine if a file can be used. Files usually
have the following naming scheme::

    VL1BI_snpp_d20160101_t185400_c20160301041812.nc

The VIIRS L1B reader supports all instrument spectral bands, identified as
the products shown below.  Geolocation files must be included when
specifying filepaths to readers and ``polar2grid.sh``.  Therefore, the
creation of The VIIRS L1B frontend can be specified to the Polar2Grid
glue script with the frontend name ``viirs_l1b``.

The list of supported products includes true and false color imagery.
These are created  by means of a python based atmospheric Rayleigh
Scattering algorithm that is executed as part of the Polar2Grid VIIRS L1B
reader.

.. note::

    The VIIRS L1B reader only supports the NASA L1B version 2.0 file format.
    Previous and future versions may work for some products, but are not
    guaranteed.

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--fornav-D`` parameter is set to 40 and the
``--fornav-d`` parameter is set to 2.

+---------------------------+-----------------------------------------------------+
| Product Name              | Description                                         |
+===========================+=====================================================+
| i01                       | I01 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| i02                       | I02 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| i03                       | I03 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| i04                       | I04 Brightness Temperature Band                     |
+---------------------------+-----------------------------------------------------+
| i05                       | I05 Brightness Temperature Band                     |
+---------------------------+-----------------------------------------------------+
| m01                       | M01 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| m02                       | M02 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| m03                       | M03 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| m04                       | M04 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| m05                       | M05 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| m06                       | M06 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| m07                       | M07 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| m08                       | M08 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| m09                       | M09 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| m10                       | M10 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| m11                       | M11 Reflectance Band                                |
+---------------------------+-----------------------------------------------------+
| m12                       | M12 Brightness Temperature Band                     |
+---------------------------+-----------------------------------------------------+
| m13                       | M13 Brightness Temperature Band                     |
+---------------------------+-----------------------------------------------------+
| m14                       | M14 Brightness Temperature Band                     |
+---------------------------+-----------------------------------------------------+
| m15                       | M15 Brightness Temperature Band                     |
+---------------------------+-----------------------------------------------------+
| m16                       | M16 Brightness Temperature Band                     |
+---------------------------+-----------------------------------------------------+
| DNB                       | Raw DNB Band (not useful for images)                |
+---------------------------+-----------------------------------------------------+
| histogram_dnb             | Histogram Equalized DNB Band                        |
+---------------------------+-----------------------------------------------------+
| adaptive_dnb              | Adaptive Histogram Equalized DNB Band               |
+---------------------------+-----------------------------------------------------+
| dynamic_dnb               | Dynamic DNB Band from Steve Miller and              |
|                           | Curtis Seaman. Uses erf to scale the data           |
+---------------------------+-----------------------------------------------------+
| hncc_dnb                  | Simplified High and Near-Constant Contrast          |
|                           | Approach from Stephan Zinke                         |
+---------------------------+-----------------------------------------------------+
| ifog                      | Temperature difference between I05 and I04          |
+---------------------------+-----------------------------------------------------+
| i_solar_zenith_angle      | I Band Solar Zenith Angle                           |
+---------------------------+-----------------------------------------------------+
| i_solar_azimuth_angle     | I Band Solar Azimuth Angle                          |
+---------------------------+-----------------------------------------------------+
| i_satellite_zenith_angle  | I Band Satellite Zenith Angle                       |
+---------------------------+-----------------------------------------------------+
| i_satellite_azimuth_angle | I Band Satellite Azimuth Angle                      |
+---------------------------+-----------------------------------------------------+
| solar_zenith_angle        | M Band Solar Zenith Angle                           |
+---------------------------+-----------------------------------------------------+
| solar_azimuth_angle       | M Band Solar Azimuth Angle                          |
+---------------------------+-----------------------------------------------------+
| satellite_zenith_angle    | M Band Satellite Zenith Angle                       |
+---------------------------+-----------------------------------------------------+
| satellite_azimuth_angle   | M Band Satellite Azimuth Angle                      |
+---------------------------+-----------------------------------------------------+
| dnb_solar_zenith_angle    | DNB Band Solar Zenith Angle                         |
+---------------------------+-----------------------------------------------------+
| dnb_lunar_zenith_angle    | DNB Band Lunar Zenith Angle                         |
+---------------------------+-----------------------------------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |
+---------------------------+-----------------------------------------------------+
| false_color               | Ratio sharpened rayleigh corrected natural color    |
+---------------------------+-----------------------------------------------------+


For reflectance/visible products a check is done to make sure that at least
10% of the swath is day time. Data is considered day time where solar zenith
angle is less than 100 degrees.

"""
from __future__ import annotations

__docformat__ = "restructuredtext en"

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from ._base import ReaderProxyBase
from polar2grid.core.script_utils import ExtendConstAction

from satpy import DataQuery

I_PRODUCTS = [
    "i01",
    "i02",
    "i03",
    "i04",
    "i05",
]
I_ANGLE_PRODUCTS = [
    "i_solar_zenith_angle",
    "i_solar_azimuth_angle",
    "i_sat_zenith_angle",
    "i_sat_azimuth_angle",
]
M_PRODUCTS = [
    "m01",
    "m02",
    "m03",
    "m04",
    "m05",
    "m06",
    "m07",
    "m08",
    "m09",
    "m10",
    "m11",
    "m12",
    "m13",
    "m14",
    "m15",
    "m16",
]

M_ANGLE_PRODUCTS = [
    "m_solar_zenith_angle",
    "m_solar_azimuth_angle",
    "m_sat_zenith_angle",
    "m_sat_azimuth_angle",
]
DNB_PRODUCTS = [
    "histogram_dnb",
    "adaptive_dnb",
    "dynamic_dnb",
    "hncc_dnb",
]

DNB_ANGLE_PRODUCTS = [
    "dnb_solar_zenith_angle",
    "dnb_solar_azimuth_angle",
    "dnb_lunar_zenith_angle",
    "dnb_lunar_azimuth_angle",
]

TRUE_COLOR_PRODUCTS = ["true_color"]
FALSE_COLOR_PRODUCTS = ["false_color"]
OTHER_COMPS = [
    "ifog",
]

PRODUCT_ALIASES = {}


def _process_legacy_products(satpy_names, band_aliases):
    """Map all lowercase band names to uppercase names and add radiance product."""
    for band in satpy_names:
        # P2G name is lowercase, Satpy is uppercase
        PRODUCT_ALIASES[band.lower()] = band
        band_aliases.append(band.lower())


I_ALIASES = []
_process_legacy_products(I_PRODUCTS, I_ALIASES)
M_ALIASES = []
_process_legacy_products(M_PRODUCTS, M_ALIASES)

_AWIPS_TRUE_COLOR = ["viirs_crefl08", "viirs_crefl04", "viirs_crefl03"]
_AWIPS_FALSE_COLOR = ["viirs_crefl07", "viirs_crefl09", "viirs_crefl08"]

PRODUCT_ALIASES["dnb_solar_zenith_angle"] = DataQuery(name="dnb_solar_zenith_angle")
PRODUCT_ALIASES["dnb_solar_azimuth_angle"] = DataQuery(name="dnb_solar_azimuth_angle")
PRODUCT_ALIASES["dnb_lunar_zenith_angle"] = DataQuery(name="dnb_lunar_zenith_angle")
PRODUCT_ALIASES["dnb_lunar_azimuth_angle"] = DataQuery(name="dnb_lunar_azimuth_angle")
PRODUCT_ALIASES["m_solar_zenith_angle"] = DataQuery(name="solar_zenith_angle", resolution=742)
PRODUCT_ALIASES["m_solar_azimuth_angle"] = DataQuery(name="solar_azimuth_angle", resolution=742)
PRODUCT_ALIASES["m_sat_zenith_angle"] = DataQuery(name="satellite_zenith_angle", resolution=742)
PRODUCT_ALIASES["m_sat_azimuth_angle"] = DataQuery(name="satellite_azimuth_angle", resolution=742)
PRODUCT_ALIASES["i_solar_zenith_angle"] = DataQuery(name="solar_zenith_angle", resolution=371)
PRODUCT_ALIASES["i_solar_azimuth_angle"] = DataQuery(name="solar_azimuth_angle", resolution=371)
PRODUCT_ALIASES["i_sat_zenith_angle"] = DataQuery(name="satellite_zenith_angle", resolution=371)
PRODUCT_ALIASES["i_sat_azimuth_angle"] = DataQuery(name="satellite_azimuth_angle", resolution=371)

DEFAULT_PRODUCTS = I_PRODUCTS + M_PRODUCTS + TRUE_COLOR_PRODUCTS + FALSE_COLOR_PRODUCTS + DNB_PRODUCTS[1:] + OTHER_COMPS

P2G_PRODUCTS = (
    I_PRODUCTS
    + M_PRODUCTS
    + TRUE_COLOR_PRODUCTS
    + FALSE_COLOR_PRODUCTS
    + DNB_PRODUCTS
    + DNB_ANGLE_PRODUCTS
    + M_ANGLE_PRODUCTS
    + I_ANGLE_PRODUCTS
    + OTHER_COMPS
)

FILTERS = {
    "day_only": {
        "standard_name": [
            "toa_bidirectional_reflectance",
            "true_color",
            "false_color",
            "natural_color",
            "corrected_reflectance",
        ],
    },
    "night_only": {
        "standard_name": ["temperature_difference"],
    },
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
    def _aliases(self) -> dict[DataQuery]:
        return PRODUCT_ALIASES


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="VIIRS l1b Reader")
    group.add_argument(
        "--i-bands",
        dest="products",
        action=ExtendConstAction,
        const=I_PRODUCTS,
        help="Add all I-band raw products to list of products",
    )
    group.add_argument(
        "--m-bands",
        dest="products",
        action=ExtendConstAction,
        const=M_PRODUCTS,
        help="Add all M-band raw products to list of products",
    )
    group.add_argument(
        "--true-color",
        dest="products",
        action=ExtendConstAction,
        const=_AWIPS_TRUE_COLOR,
        help="Add the True Color product to the list of products",
    )
    group.add_argument(
        "--false-color",
        dest="products",
        action=ExtendConstAction,
        const=_AWIPS_FALSE_COLOR,
        help="Add the False Color product to the list of products",
    )
    return group, None
