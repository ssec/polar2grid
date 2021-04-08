#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2012-2021 Space Science and Engineering Center (SSEC),
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
#
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
#
"""The MiRS frontend extracts data from files created by the Community
Satellite Processing Package (CSPP) direct broadcast version of the
NOAA/STAR Microwave Integrated Retrieval System (MIRS). The software
supports the creation of atmospheric profile and surface parameters from 
ATMS, AMSU-A, and MHS microwave sensor data. For more information
on this product, please see the 

When executed on Suomi-NPP Advanced Technology Microwave Sounder (ATMS) 
MIRS product files, a limb correction algorithm is applied for  
brightness temperatures reprojections for each of the 22 spectral bands.  
The correction software was provided by Kexin Zhang of NOAA STAR, and
is applied as part of the MIRS ATMS Polar2Grid execution. 

This reader's default resampling algorithm is ``ewa`` for Elliptical Weighted
Averaging resampling. The ``--fornav-D`` option is set to 100 and the
``--fornav-d`` option is set to 1.

The frontend offers the following products:

    +--------------------+----------------------------------------------------+
    | Product Name       | Description                                        |
    +====================+====================================================+
    | rain_rate          | Rain Rate                                          |
    +--------------------+----------------------------------------------------+
    | sea_ice            | Sea Ice in percent                                 |
    +--------------------+----------------------------------------------------+
    | snow_cover         | Snow Cover                                         |
    +--------------------+----------------------------------------------------+
    | tpw                | Total Precipitable Water                           |
    +--------------------+----------------------------------------------------+
    | swe                | Snow Water Equivalence                             |
    +--------------------+----------------------------------------------------+
    | btemp_X            | Brightness Temperature for channel X (see below)   |
    +--------------------+----------------------------------------------------+

For specific brightness temperature band products, use the ``btemp_X`` option,
where ``X`` is a combination of the microwave frequency (integer) and
polarization of the channel. If there is more than one channel at that
frequency and polarization a "count" number is added to the end. To create
output files of all available bands, use the ``--bt-channels`` option.

As an example, the ATMS band options are:

.. list-table:: ATMS Brightness Temperature Channels
    :header-rows: 1
    
    * - **Band Number**
      - **Frequency (GHz)**
      - **Polarization**
      - **Polar2Grid Dataset Name**
    * - 1
      - 23.79
      - V
      - btemp_23v
    * - 2
      - 31.40
      - V
      - btemp_31v
    * - 3
      - 50.30
      - H
      - btemp_50h
    * - 4
      - 51.76
      - H
      - btemp_51h
    * - 5
      - 52.80
      - H
      - btemp_52h
    * - 6
      - 53.59±0.115
      - H
      - btemp_53h
    * - 7
      - 54.40
      - H
      - btemp_54h1
    * - 8
      - 54.94
      - H
      - btemp_54h2
    * - 9
      - 55.50
      - H
      - btemp_55h
    * - 10
      - 57.29
      - H
      - btemp_57h1
    * - 11
      - 57.29±2.17
      - H
      - btemp_57h2
    * - 12
      - 57.29±0.3222±0.048
      - H
      - btemp_57h3
    * - 13
      - 57.29±0.3222±0.022
      - H
      - btemp_57h4
    * - 14
      - 57.29±0.3222±0.010
      - H
      - btemp_57h5
    * - 15
      - 57.29±0.3222±0.0045
      - H
      - btemp_57h6
    * - 16
      - 88.20
      - V
      - btemp_88v
    * - 17
      - 165.50
      - H
      - btemp_165h
    * - 18
      - 183.31±7.0
      - H
      - btemp_183h1
    * - 19
      - 183.31±4.5
      - H
      - btemp_183h2
    * - 20
      - 183.31±3.0
      - H
      - btemp_183h3
    * - 21
      - 183.31±1.8
      - H
      - btemp_183h4
    * - 22
      - 183.31±1.0
      - H
      - btemp_183h5

"""

from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from ._base import ReaderProxyBase

PRECIP_PRODUCTS = [
    "rain_rate",
    "tpw",
]
SNOW_PRODUCTS = [
    "snow_cover",
    "swe",
]
SEAICE_PRODUCTS = [
    "sea_ice",
]

BTEMP_PRODUCTS = [
    "btemp_23v",
    "btemp_31v",
    "btemp_50h",
    "btemp_51h",
    "btemp_52h",
    "btemp_53h",
    "btemp_54h1",
    "btemp_54h2",
    "btemp_55h",
    "btemp_57h1",
    "btemp_57h2",
    "btemp_57h3",
    "btemp_57h4",
    "btemp_57h5",
    "btemp_57h6",
    "btemp_88v",
    "btemp_165h",
    "btemp_183h1",
    "btemp_183h2",
    "btemp_183h3",
    "btemp_183h4",
    "btemp_183h5",
]
DEFAULT_PRODUCTS = ["rain_rate", "btemp_88v", "btemp_89v1"]

PRODUCT_ALIASES = {}
PRODUCT_ALIASES["rain_rate"] = "RR"
PRODUCT_ALIASES["tpw"] = "TPW"

PRODUCT_ALIASES["snow_cover"] = "Snow"
PRODUCT_ALIASES["swe"] = "SWE"

PRODUCT_ALIASES["sea_ice"] = "SIce"

P2G_PRODUCTS = PRECIP_PRODUCTS + SNOW_PRODUCTS + SEAICE_PRODUCTS + BTEMP_PRODUCTS


class ReaderProxy(ReaderProxyBase):
    """Provide Polar2Grid-specific information about this reader's products."""

    # TODO: Filter default products and all products by what btemps are available/known
    is_polar2grid_reader = True

    def get_default_products(self) -> list[str]:
        """Get products to load if users hasn't specified any others."""
        return DEFAULT_PRODUCTS

    def get_all_products(self):
        """Get all polar2grid products that could be loaded."""
        return P2G_PRODUCTS

    @property
    def _aliases(self):
        return PRODUCT_ALIASES


def add_reader_argument_groups(
    parser: ArgumentParser, group: Optional[_ArgumentGroup] = None
) -> tuple[Optional[_ArgumentGroup], Optional[_ArgumentGroup]]:
    """Add reader-specific command line arguments to an existing argument parser."""
    return None, None
