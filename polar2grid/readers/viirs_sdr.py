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

+---------------------------+--------------------------------------------+
| Product Name              | Description                                |
+===========================+============================================+
| i01                       | I01 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| i02                       | I02 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| i03                       | I03 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| i04                       | I04 Brightness Temperature Band            |
+---------------------------+--------------------------------------------+
| i05                       | I05 Brightness Temperature Band            |
+---------------------------+--------------------------------------------+
| i01_rad                   | I01 Radiance Band                          |
+---------------------------+--------------------------------------------+
| i02_rad                   | I02 Radiance Band                          |
+---------------------------+--------------------------------------------+
| i03_rad                   | I03 Radiance Band                          |
+---------------------------+--------------------------------------------+
| i04_rad                   | I04 Radiance Band                          |
+---------------------------+--------------------------------------------+
| i05_rad                   | I05 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m01                       | M01 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| m02                       | M02 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| m03                       | M03 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| m04                       | M04 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| m05                       | M05 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| m06                       | M06 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| m07                       | M07 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| m08                       | M08 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| m09                       | M09 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| m10                       | M10 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| m11                       | M11 Reflectance Band                       |
+---------------------------+--------------------------------------------+
| m12                       | M12 Brightness Temperature Band            |
+---------------------------+--------------------------------------------+
| m13                       | M13 Brightness Temperature Band            |
+---------------------------+--------------------------------------------+
| m14                       | M14 Brightness Temperature Band            |
+---------------------------+--------------------------------------------+
| m15                       | M15 Brightness Temperature Band            |
+---------------------------+--------------------------------------------+
| m16                       | M16 Brightness Temperature Band            |
+---------------------------+--------------------------------------------+
| m01_rad                   | M01 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m02_rad                   | M02 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m03_rad                   | M03 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m04_rad                   | M04 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m05_rad                   | M05 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m06_rad                   | M06 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m07_rad                   | M07 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m08_rad                   | M08 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m09_rad                   | M09 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m10_rad                   | M10 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m11_rad                   | M11 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m12_rad                   | M12 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m13_rad                   | M13 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m14_rad                   | M14 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m15_rad                   | M15 Radiance Band                          |
+---------------------------+--------------------------------------------+
| m16_rad                   | M16 Radiance Band                          |
+---------------------------+--------------------------------------------+
| dnb                       | Raw DNB Band (not useful for images)       |
+---------------------------+--------------------------------------------+
| histogram_dnb             | Histogram Equalized DNB Band               |
+---------------------------+--------------------------------------------+
| adaptive_dnb              | Adaptive Histogram Equalized DNB Band      |
+---------------------------+--------------------------------------------+
| dynamic_dnb               | Dynamic DNB Band from Steve Miller and     |
|                           | Curtis Seaman. Uses erf to scale the data. |
+---------------------------+--------------------------------------------+
| hncc_dnb                  | Simplified High and Near-Constant Contrast |
|                           | Approach from Stephan Zinke                |
+---------------------------+--------------------------------------------+
| ifog                      | Temperature difference between I05 and I04 |
+---------------------------+--------------------------------------------+
| i_solar_zenith_angle      | I Band Solar Zenith Angle                  |
+---------------------------+--------------------------------------------+
| i_solar_azimuth_angle     | I Band Solar Azimuth Angle                 |
+---------------------------+--------------------------------------------+
| i_sat_zenith_angle        | I Band Satellite Zenith Angle              |
+---------------------------+--------------------------------------------+
| i_sat_azimuth_angle       | I Band Satellite Azimuth Angle             |
+---------------------------+--------------------------------------------+
| m_solar_zenith_angle      | M Band Solar Zenith Angle                  |
+---------------------------+--------------------------------------------+
| m_solar_azimuth_angle     | M Band Solar Azimuth Angle                 |
+---------------------------+--------------------------------------------+
| m_sat_zenith_angle        | M Band Satellite Zenith Angle              |
+---------------------------+--------------------------------------------+
| m_sat_azimuth_angle       | M Band Satellite Azimuth Angle             |
+---------------------------+--------------------------------------------+
| dnb_solar_zenith_angle    | DNB Band Solar Zenith Angle                |
+---------------------------+--------------------------------------------+
| dnb_solar_azimuth_angle   | DNB Band Solar Azimuth Angle               |
+---------------------------+--------------------------------------------+
| dnb_sat_zenith_angle      | DNB Band Satellite Zenith Angle            |
+---------------------------+--------------------------------------------+
| dnb_sat_azimuth_angle     | DNB Band Satellite Azimuth Angle           |
+---------------------------+--------------------------------------------+
| dnb_lunar_zenith_angle    | DNB Band Lunar Zenith Angle                |
+---------------------------+--------------------------------------------+
| dnb_lunar_azimuth_angle   | DNB Band Lunar Azimuth Angle               |
+---------------------------+--------------------------------------------+

"""

from satpy import DataQuery

I_PRODUCTS = [
    "I01",
    "I02",
    "I03",
    "I04",
    "I05",
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
DNB_PRODUCTS = [
    "histogram_dnb",
    "adaptive_dnb",
    "dynamic_dnb",
    "hncc_dnb",
]
TRUE_COLOR_PRODUCTS = [
    "true_color"
]
FALSE_COLOR_PRODUCTS = [
    "false_color"
]
OTHER_COMPS = [
    "ifog",
]
DEFAULT_PRODUCTS = I_PRODUCTS + M_PRODUCTS + DNB_PRODUCTS[1:] + TRUE_COLOR_PRODUCTS + FALSE_COLOR_PRODUCTS + OTHER_COMPS

# map all lowercase band names to uppercase names
PRODUCT_ALIASES = {}
for band in I_PRODUCTS + M_PRODUCTS:
    PRODUCT_ALIASES[band.lower()] = band
# radiance products
for band in I_PRODUCTS + M_PRODUCTS:
    dq = DataQuery(name=band, calibration='radiance')
    PRODUCT_ALIASES[band.lower() + '_rad'] = dq
    PRODUCT_ALIASES[band.lower() + '_rad'] = dq

PRODUCT_ALIASES['awips_true_color'] = ['viirs_crefl08', 'viirs_crefl04', 'viirs_crefl03']
PRODUCT_ALIASES['awips_false_color'] = ['viirs_crefl07', 'viirs_crefl09', 'viirs_crefl08']

FILTERS = {
    'day': {
        'standard_name': ['toa_bidirectional_reflectance', 'true_color', 'false_color', 'natural_color'],
    },
    'night': {
        'standard_name': ['temperature_difference'],
    }
}


def add_reader_argument_groups(parser):
    return parser
