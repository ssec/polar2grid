#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2015 Space Science and Engineering Center (SSEC),
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
# Written by David Hoese    October 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""The VIIRS Frontend operates on Environmental Data Record (EDR) files from
the Suomi National Polar-orbiting Partnership's (NPP) Visible/Infrared
Imager Radiometer Suite (VIIRS) instrument. The VIIRS frontend ignores filenames and uses internal
file content to determine the type of file being provided, but EDR HDF5 files are typically named as below
and have corresponding geolocation files::

    SVI01_npp_d20120225_t1801245_e1802487_b01708_c20120226002130255476_noaa_ops.h5

The VIIRS frontend supports a small amount of EDR files available. The supported products are shown below.
Geolocation files must be included
when specifying filepaths to frontends and glue scripts. The VIIRS frontend can be specified to the ``polar2grid.sh`` script
with the frontend name ``viirs``.

    +---------------------------+--------------------------------------------+
    | Product Name              | Description                                |
    +===========================+============================================+
    | aod_555nm                 | Aerosol Optical Depth at 550nm             |
    +---------------------------+--------------------------------------------+
    | cot                       | Average Cloud Optical Thickness            |
    +---------------------------+--------------------------------------------+

|

.. note::

    Terrain corrected geolocation for the DNB band has recently been added and is included in the non-TC file (GDNBO).
    This may cause some confusion to users as the VIIRS frontend currently only checks for terrain corrected data. To
    use non-TC data use the ``--no-tc`` flag (described below).

:author:       David Hoese (davidh)
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012-2015 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2015
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import sys

import logging
import os

from polar2grid.core.frontend_utils import ProductDict, GeoPairDict
from . import guidebook
from .io import VIIRSSDRMultiReader
from .swath import Frontend as SDRFrontend

LOG = logging.getLogger(__name__)

### PRODUCT KEYS ###
PRODUCT_AOD_555 = "aod_555nm"
PRODUCT_AVG_COT = "cot"

# Geolocation "Products"
# These products aren't really products at the moment and should only be used as navigation for the above products
PRODUCT_AERO_LAT = "aero_latitude"
PRODUCT_AERO_LON = "aero_longitude"
PRODUCT_COT_LAT = "cloud_latitude"
PRODUCT_COT_LON = "cloud_longitude"

AOD_PRODUCTS = [
    PRODUCT_AOD_555,
]
COT_PRODUCTS = [
    PRODUCT_AVG_COT,
]

PRODUCTS = ProductDict()
GEO_PAIRS = GeoPairDict()

PAIR_AERO_NAV = "aeronav"
PAIR_COT_NAV = "cotnav"
# Cool, there's no way to get rows per scan from the file
GEO_PAIRS.add_pair(PAIR_AERO_NAV, PRODUCT_AERO_LON, PRODUCT_AERO_LAT, 2)
GEO_PAIRS.add_pair(PAIR_COT_NAV, PRODUCT_COT_LON, PRODUCT_COT_LAT, 2)

# TODO: Add description and units
PRODUCTS.add_product(PRODUCT_AERO_LON, PAIR_AERO_NAV, "longitude", (
    guidebook.FILE_TYPE_GAERO, guidebook.FILE_TYPE_GAERO), guidebook.K_LONGITUDE)
PRODUCTS.add_product(PRODUCT_AERO_LAT, PAIR_AERO_NAV, "latitude", (
    guidebook.FILE_TYPE_GAERO, guidebook.FILE_TYPE_GAERO), guidebook.K_LATITUDE)
PRODUCTS.add_product(PRODUCT_COT_LON, PAIR_COT_NAV, "longitude", (guidebook.FILE_TYPE_GCLDO, guidebook.FILE_TYPE_GCLDO), guidebook.K_LONGITUDE)
PRODUCTS.add_product(PRODUCT_COT_LAT, PAIR_COT_NAV, "latitude", (guidebook.FILE_TYPE_GCLDO, guidebook.FILE_TYPE_GCLDO), guidebook.K_LATITUDE)

PRODUCTS.add_product(PRODUCT_AOD_555, PAIR_AERO_NAV, "optical_depth", guidebook.FILE_TYPE_VAOOO, guidebook.K_AOD_555)
PRODUCTS.add_product(PRODUCT_AVG_COT, PAIR_COT_NAV, "cloud_optical_thickness", guidebook.FILE_TYPE_VCOTO, guidebook.K_AVG_COT)


class EDRFrontend(SDRFrontend):
    FILE_EXTENSIONS = [".h5"]
    DEFAULT_FILE_READER = VIIRSSDRMultiReader
    PRODUCTS = PRODUCTS
    GEO_PAIRS = GEO_PAIRS

    def __init__(self, use_terrain_corrected=True, day_fraction=0.10, night_fraction=0.10, sza_threshold=100, **kwargs):
        """Initialize the frontend.

        For each search path, check if it exists and that it is
        a directory. If it is not a valid search path it will be removed
        and a warning will be raised.

        The order of the search paths does not matter. Any duplicate
        directories in the search path will be removed. This frontend
        does *not* recursively search directories.

        :param search_paths: A list of paths to search for usable files
        :param use_terrain_corrected: Look for terrain-corrected files instead of non-TC files (default True)
        """
        self.use_terrain_corrected = use_terrain_corrected
        LOG.debug("Day fraction set to %f", day_fraction)
        self.day_fraction = day_fraction
        LOG.debug("Night fraction set to %f", night_fraction)
        self.night_fraction = night_fraction
        LOG.debug("SZA threshold set to %f", sza_threshold)
        self.sza_threshold = sza_threshold
        # Don't call the SDRFrontend's init, call its parent
        super(SDRFrontend, self).__init__(**kwargs)

        # Load and sort all files
        self._load_files(self.find_files_with_extensions())

        # Functions to create additional products
        self.secondary_product_functions = {
        }

    @property
    def default_products(self):
        if os.getenv("P2G_VIIRS_EDR_DEFAULTS", None):
            return os.getenv("P2G_VIIRS_EDR_DEFAULTS").split(" ")

        defaults = [
            PRODUCT_AOD_555,
            PRODUCT_AVG_COT,
        ]
        return defaults

    ### Secondary Product Functions


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    from polar2grid.core.script_utils import ExtendAction
    # Set defaults for other components that may be used in polar2grid processing
    parser.set_defaults(fornav_D=40, fornav_d=1)

    # Use the append_const action to handle adding products to the list
    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                       help="List available frontend products and exit")
    group.add_argument("--no-tc", dest="use_terrain_corrected", action="store_false",
                       help="Don't use terrain-corrected navigation")
    group.add_argument("--day-fraction", dest="day_fraction", type=float, default=float(os.environ.get("P2G_DAY_FRACTION", 0.10)),
                       help="Fraction of day required to produce reflectance products (default 0.10)")
    group.add_argument("--night-fraction", dest="night_fraction", type=float, default=float(os.environ.get("P2G_NIGHT_FRACTION", 0.10)),
                       help="Fraction of night required to product products like fog (default 0.10)")
    group.add_argument("--sza-threshold", dest="sza_threshold", type=float, default=float(os.environ.get("P2G_SZA_THRESHOLD", 100)),
                       help="Angle threshold of solar zenith angle used when deciding day or night (default 100)")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    # FIXME: Probably need some proper defaults
    group.add_argument("-p", "--products", dest="products", nargs="+", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    return ["Frontend Initialization", "Frontend Swath Extraction"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    parser = create_basic_parser(description="Extract VIIRS swath data into binary files")
    subgroup_titles = add_frontend_argument_groups(parser)
    parser.add_argument('-f', dest='data_files', nargs="+", default=[],
                        help="List of data files or directories to extract data from")
    parser.add_argument('-o', dest="output_filename", default=None,
                        help="Output filename for JSON scene (default is to stdout)")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(subgroup_titles=subgroup_titles, global_keywords=global_keywords)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)
    LOG.debug("Starting script with arguments: %s", " ".join(sys.argv))

    list_products = args.subgroup_args["Frontend Initialization"].pop("list_products")
    f = EDRFrontend(search_paths=args.data_files, **args.subgroup_args["Frontend Initialization"])

    if list_products:
        print("\n".join(f.available_product_names))
        return 0

    if args.output_filename and os.path.isfile(args.output_filename):
        LOG.error("JSON file '%s' already exists, will not overwrite." % (args.output_filename,))
        raise RuntimeError("JSON file '%s' already exists, will not overwrite." % (args.output_filename,))

    scene = f.create_scene(**args.subgroup_args["Frontend Swath Extraction"])
    json_str = scene.dumps(persist=True)
    if args.output_filename:
        with open(args.output_filename, 'w') as output_file:
            output_file.write(json_str)
    else:
        print(json_str)
    return 0

if __name__ == '__main__':
    sys.exit(main())
