#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2020 Space Science and Engineering Center (SSEC),
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
"""The VIIRS SDR Reader operates on Science Data Record (SDR) HDF5 files from
the Suomi National Polar-orbiting Partnership's (NPP) and/or the NOAA20
Visible/Infrared Imager Radiometer Suite (VIIRS) instrument. The VIIRS
SDR reader ignores filenames and uses internal file content to determine
the type of file being provided, but SDR are typically named as below
and have corresponding geolocation files::

    SVI01_npp_d20120225_t1801245_e1802487_b01708_c20120226002130255476_noaa_ops.h5

The VIIRS SDR reader supports all instrument spectral bands, identified as
the products shown below. It supports terrain corrected or non-terrain corrected
navigation files. Geolocation files must be included when specifying filepaths to
readers and ``polar2grid.sh``. The VIIRS reader can be specified to the ``polar2grid.sh`` script
with the reader name ``viirs_sdr``.

This reader's default remapping algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--fornav-D`` parameter set to 40 and the
``--fornav-d`` parameter set to 2.

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
| i01_rad                   | I01 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| i02_rad                   | I02 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| i03_rad                   | I03 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| i04_rad                   | I04 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| i05_rad                   | I05 Radiance Band                                   |
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
| m01_rad                   | M01 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m02_rad                   | M02 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m03_rad                   | M03 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m04_rad                   | M04 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m05_rad                   | M05 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m06_rad                   | M06 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m07_rad                   | M07 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m08_rad                   | M08 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m09_rad                   | M09 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m10_rad                   | M10 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m11_rad                   | M11 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m12_rad                   | M12 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m13_rad                   | M13 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m14_rad                   | M14 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m15_rad                   | M15 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| m16_rad                   | M16 Radiance Band                                   |
+---------------------------+-----------------------------------------------------+
| dnb                       | Raw DNB Band (not useful for images)                |
+---------------------------+-----------------------------------------------------+
| histogram_dnb             | Histogram Equalized DNB Band                        |
+---------------------------+-----------------------------------------------------+
| adaptive_dnb              | Adaptive Histogram Equalized DNB Band               |
+---------------------------+-----------------------------------------------------+
| dynamic_dnb               | Dynamic DNB Band from Steve Miller and              |
|                           | Curtis Seaman. Uses erf to scale the data.          |
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
| i_sat_zenith_angle        | I Band Satellite Zenith Angle                       |
+---------------------------+-----------------------------------------------------+
| i_sat_azimuth_angle       | I Band Satellite Azimuth Angle                      |
+---------------------------+-----------------------------------------------------+
| m_solar_zenith_angle      | M Band Solar Zenith Angle                           |
+---------------------------+-----------------------------------------------------+
| m_solar_azimuth_angle     | M Band Solar Azimuth Angle                          |
+---------------------------+-----------------------------------------------------+
| m_sat_zenith_angle        | M Band Satellite Zenith Angle                       |
+---------------------------+-----------------------------------------------------+
| m_sat_azimuth_angle       | M Band Satellite Azimuth Angle                      |
+---------------------------+-----------------------------------------------------+
| dnb_solar_zenith_angle    | DNB Band Solar Zenith Angle                         |
+---------------------------+-----------------------------------------------------+
| dnb_solar_azimuth_angle   | DNB Band Solar Azimuth Angle                        |
+---------------------------+-----------------------------------------------------+
| dnb_sat_zenith_angle      | DNB Band Satellite Zenith Angle                     |
+---------------------------+-----------------------------------------------------+
| dnb_sat_azimuth_angle     | DNB Band Satellite Azimuth Angle                    |
+---------------------------+-----------------------------------------------------+
| dnb_lunar_zenith_angle    | DNB Band Lunar Zenith Angle                         |
+---------------------------+-----------------------------------------------------+
| dnb_lunar_azimuth_angle   | DNB Band Lunar Azimuth Angle                        |
+---------------------------+-----------------------------------------------------+
| true_color                | Ratio sharpened rayleigh corrected true color       |
+---------------------------+-----------------------------------------------------+
| false_color               | Ratio sharpened rayleigh corrected false color      |
+---------------------------+-----------------------------------------------------+

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from satpy import DataQuery, Scene

from polar2grid.core.script_utils import ExtendConstAction

from ._base import ReaderProxyBase

I_PRODUCTS = [
    "I01",
    "I02",
    "I03",
    "I04",
    "I05",
]
I_ANGLE_PRODUCTS = [
    "i_solar_zenith_angle",
    "i_solar_azimuth_angle",
    "i_sat_zenith_angle",
    "i_sat_azimuth_angle",
]
M_PRODUCTS = [
    "M01",
    "M02",
    "M03",
    "M04",
    "M05",
    "M06",
    "M07",
    "M08",
    "M09",
    "M10",
    "M11",
    "M12",
    "M13",
    "M14",
    "M15",
    "M16",
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
    "dnb_sat_zenith_angle",
    "dnb_sat_azimuth_angle",
    "dnb_lunar_zenith_angle",
    "dnb_lunar_azimuth_angle",
]
TRUE_COLOR_PRODUCTS = ["true_color"]
FALSE_COLOR_PRODUCTS = ["false_color"]
OTHER_COMPS = [
    "ifog",
]


PRODUCT_ALIASES = {}


def _process_legacy_and_rad_products(satpy_names, band_aliases, rad_aliases):
    """Map all lowercase band names to uppercase names and add radiance product."""
    for band in satpy_names:
        # P2G name is lowercase, Satpy is uppercase
        PRODUCT_ALIASES[band.lower()] = band
        band_aliases.append(band.lower())

        # radiance products for M and I bands
        rad_name = band.lower() + "_rad"
        dq = DataQuery(name=band, calibration="radiance")
        PRODUCT_ALIASES[rad_name] = dq
        rad_aliases.append(rad_name)


I_ALIASES = []
I_RAD_PRODUCTS = []
_process_legacy_and_rad_products(I_PRODUCTS, I_ALIASES, I_RAD_PRODUCTS)
M_ALIASES = []
M_RAD_PRODUCTS = []
_process_legacy_and_rad_products(M_PRODUCTS, M_ALIASES, M_RAD_PRODUCTS)

_AWIPS_TRUE_COLOR = ["viirs_crefl08", "viirs_crefl04", "viirs_crefl03"]
_AWIPS_FALSE_COLOR = ["viirs_crefl07", "viirs_crefl09", "viirs_crefl08"]

PRODUCT_ALIASES["dnb_solar_zenith_angle"] = DataQuery(name="dnb_solar_zenith_angle")
PRODUCT_ALIASES["dnb_solar_azimuth_angle"] = DataQuery(name="dnb_solar_azimuth_angle")
PRODUCT_ALIASES["dnb_sat_zenith_angle"] = DataQuery(name="dnb_satellite_zenith_angle")
PRODUCT_ALIASES["dnb_sat_azimuth_angle"] = DataQuery(name="dnb_satellite_azimuth_angle")
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

DEFAULT_PRODUCTS = I_ALIASES + M_ALIASES + DNB_PRODUCTS[1:] + TRUE_COLOR_PRODUCTS + FALSE_COLOR_PRODUCTS + OTHER_COMPS
P2G_PRODUCTS = I_ALIASES + M_ALIASES + DNB_PRODUCTS + I_RAD_PRODUCTS + M_RAD_PRODUCTS
P2G_PRODUCTS += I_ANGLE_PRODUCTS + M_ANGLE_PRODUCTS + DNB_ANGLE_PRODUCTS + OTHER_COMPS
P2G_PRODUCTS += TRUE_COLOR_PRODUCTS + FALSE_COLOR_PRODUCTS

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

    def __init__(self, scn: Scene, user_products: list[str]):
        self._modified_aliases = PRODUCT_ALIASES.copy()
        if "dynamic_dnb_saturation" in user_products:
            # they specified --dnb-saturation-correction
            # let's modify the aliases so dynamic_dnb points to this product
            user_products.remove("dynamic_dnb_saturation")
            self._modified_aliases["dynamic_dnb"] = DataQuery(name="dynamic_dnb_saturation")
        super().__init__(scn, user_products)

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULT_PRODUCTS

    def get_all_products(self):
        """Get all polar2grid products that could be loaded."""
        return P2G_PRODUCTS

    @property
    def _aliases(self):
        return self._modified_aliases


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser.

    If ``group`` is provided then arguments are added to this group. If not,
    a new group is added to the parser and arguments added to this new group.

    """
    if group is None:
        group = parser.add_argument_group(title="VIIRS SDR Reader")

    group.add_argument(
        "--i-bands",
        dest="products",
        action=ExtendConstAction,
        const=I_ALIASES,
        help="Add all I-band raw products to list of products",
    )
    group.add_argument(
        "--m-bands",
        dest="products",
        action=ExtendConstAction,
        const=M_ALIASES,
        help="Add all M-band raw products to list of products",
    )
    group.add_argument(
        "--dnb-angle-products",
        dest="products",
        action=ExtendConstAction,
        const=DNB_ANGLE_PRODUCTS,
        help="Add DNB-band geolocation 'angle' products to list of products",
    )
    group.add_argument(
        "--dnb-saturation-correction",
        dest="products",
        action=ExtendConstAction,
        const=["dynamic_dnb_saturation"],
        help="Enable dynamic DNB saturation correction (normally used for aurora scenes)",
    )
    group.add_argument(
        "--i-angle-products",
        dest="products",
        action=ExtendConstAction,
        const=I_ANGLE_PRODUCTS,
        help="Add I-band geolocation 'angle' products to list of products",
    )
    group.add_argument(
        "--m-angle-products",
        dest="products",
        action=ExtendConstAction,
        const=M_ANGLE_PRODUCTS,
        help="Add M-band geolocation 'angle' products to list of products",
    )
    group.add_argument(
        "--m-rad-products",
        dest="products",
        action=ExtendConstAction,
        const=M_RAD_PRODUCTS,
        help="Add M-band geolocation radiance products to list of products",
    )
    group.add_argument(
        "--i-rad-products",
        dest="products",
        action=ExtendConstAction,
        const=I_RAD_PRODUCTS,
        help="Add I-band geolocation radiance products to list of products",
    )
    group.add_argument(
        "--awips-true-color",
        dest="products",
        action=ExtendConstAction,
        const=_AWIPS_TRUE_COLOR,
        help="Add individual CREFL corrected products to create " "the 'true_color' composite in AWIPS.",
    )
    group.add_argument(
        "--awips-false-color",
        dest="products",
        action=ExtendConstAction,
        const=_AWIPS_FALSE_COLOR,
        help="Add individual CREFL corrected products to create " "the 'false_color' composite in AWIPS.",
    )
    return group, None
