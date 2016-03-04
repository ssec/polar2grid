#!/usr/bin/env python
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
"""SatPy compatible readers and legacy P2G frontends to wrap them.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2016 University of Wisconsin SSEC. All rights reserved.
:date:         Mar 2016
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

from polar2grid.core import containers, roles
from polar2grid.core.dtype import dtype_to_str

import numpy as np
from satpy.scene import Scene

import os
import sys
import logging

LOG = logging.getLogger(__name__)


def area_to_swath_def(area, overwrite_existing=False):
    lons = area.lons
    lats = area.lats
    name = area.name
    name = name.replace(":", "")
    info = {
        "swath_name": name,
        "longitude": name + "_lon.dat",
        "latitude": name + "_lat.dat",
        "swath_rows": lons.shape[0],
        "swath_columns": lons.shape[1],
        "data_type": lons.dtype,
        "fill_value": np.nan,
    }

    # Write lons to disk
    filename = info["longitude"]
    if os.path.isfile(filename):
        if not overwrite_existing:
            LOG.error("Binary file already exists: %s" % (filename,))
            raise RuntimeError("Binary file already exists: %s" % (filename,))
        else:
            LOG.warning("Binary file already exists, will overwrite: %s", filename)
    lon_arr = np.memmap(filename, mode="w+", dtype=lons.dtype, shape=lons.shape)
    lon_arr[:] = lons.data
    lon_arr[lons.mask] = np.nan

    # Write lats to disk
    filename = info["latitude"]
    if os.path.isfile(filename):
        if not overwrite_existing:
            LOG.error("Binary file already exists: %s" % (filename,))
            raise RuntimeError("Binary file already exists: %s" % (filename,))
        else:
            LOG.warning("Binary file already exists, will overwrite: %s", filename)
    lat_arr = np.memmap(filename, mode="w+", dtype=lats.dtype, shape=lats.shape)
    lat_arr[:] = lats.data
    lat_arr[lats.mask] = np.nan
    return containers.SwathDefinition(**info)


def dataset_to_swath_product(ds, swath_def, overwrite_existing=False):
    info = ds.info.copy()
    info.pop("area")
    filename = info["id"].name + ".dat"
    p2g_metadata = {
        "product_name": info["id"].name,
        "satellite": info["platform"].lower(),
        "instrument": info["sensor"].lower() if isinstance(info["sensor"], str) else list(info["sensor"])[0].lower(),
        "data_kind": info["standard_name"],
        "begin_time": info["start_time"],
        "end_time": info["end_time"],
        "fill_value": np.nan,
        "swath_columns": ds.shape[1],
        "swath_rows": ds.shape[0],
        "rows_per_scan": info["rows_per_scan"],
        "swath_data": filename,
        "data_type": ds.dtype,
        "swath_definition": swath_def,
    }
    info.update(p2g_metadata)

    if os.path.isfile(filename):
        if not overwrite_existing:
            LOG.error("Binary file already exists: %s" % (filename,))
            raise RuntimeError("Binary file already exists: %s" % (filename,))
        else:
            LOG.warning("Binary file already exists, will overwrite: %s", filename)

    p2g_arr = np.memmap(filename, mode="w+", dtype=ds.dtype, shape=ds.shape)
    p2g_arr[:] = ds.data
    p2g_arr[ds.mask] = np.nan

    return containers.SwathProduct(**info)


class Frontend(roles.FrontendRole):
    FILE_EXTENSIONS = [".nc"]

    def __init__(self, **kwargs):
        self.reader_name = kwargs.pop("reader_name", "viirs_l1b")
        super(Frontend, self).__init__(**kwargs)
        pathnames = self.find_files_with_extensions()
        # Create a satpy Scene object
        self.scene = Scene(reader_name=self.reader_name, filenames=pathnames)
        self._begin_time = min(fr.start_time for fr in self.scene.readers[self.reader_name].file_readers.values())
        self._end_time = min(fr.end_time for fr in self.scene.readers[self.reader_name].file_readers.values())

    @property
    def begin_time(self):
        return self._begin_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def available_product_names(self):
        return sorted(set(k.name for k in self.scene.readers[self.reader_name].datasets.keys()))

    @property
    def all_product_names(self):
        return sorted(set(k.name for k in self.scene.readers[self.reader_name].datasets.keys()))

    @property
    def default_products(self):
        return [
            "I01",
            "I02",
            "I03",
            "I04",
            "I05",
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
            # "histogram_dnb",
            # "adaptive_dnb"
        ]

    def create_scene(self, products=None, **kwargs):
        LOG.debug("Loading scene data...")
        # If the user didn't provide the products they want, figure out which ones we can create
        if products is None:
            LOG.debug("No products specified to frontend, will try to load logical defaults products")
            products = self.default_products

        kwargs.pop("overwrite_existing")
        kwargs.pop("exit_on_error")
        kwargs.pop("keep_intermediate")
        self.scene.load(products, **kwargs)

        p2g_scene = containers.SwathScene()
        areas = {}
        for ds in self.scene:
            if ds.info["area"].name in areas:
                swath_def = areas[ds.info["area"].name]
            else:
                areas[ds.info["area"].name] = swath_def = area_to_swath_def(ds.info["area"], overwrite_existing=self.overwrite_existing)
                swath_def["rows_per_scan"] = ds.info["rows_per_scan"]

            swath_product = dataset_to_swath_product(ds, swath_def, overwrite_existing=self.overwrite_existing)
            p2g_scene[swath_product["product_name"]] = swath_product

        # Delete the satpy scene so memory is cleared out
        self.scene = None
        return p2g_scene


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    from polar2grid.core.script_utils import ExtendAction, ExtendConstAction
    # Set defaults for other components that may be used in polar2grid processing
    parser.set_defaults(fornav_D=40, fornav_d=2)

    # Use the append_const action to handle adding products to the list
    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                       help="List available frontend products and exit")
    # group.add_argument("--no-tc", dest="use_terrain_corrected", action="store_false",
    #                    help="Don't use terrain-corrected navigation")
    # group.add_argument("--day-fraction", dest="day_fraction", type=float, default=float(os.environ.get("P2G_DAY_FRACTION", 0.10)),
    #                    help="Fraction of day required to produce reflectance products (default 0.10)")
    # group.add_argument("--night-fraction", dest="night_fraction", type=float, default=float(os.environ.get("P2G_NIGHT_FRACTION", 0.10)),
    #                    help="Fraction of night required to product products like fog (default 0.10)")
    # group.add_argument("--sza-threshold", dest="sza_threshold", type=float, default=float(os.environ.get("P2G_SZA_THRESHOLD", 100)),
    #                    help="Angle threshold of solar zenith angle used when deciding day or night (default 100)")
    # group.add_argument("--dnb-saturation-correction", action="store_true",
    #                    help="Enable dynamic DNB saturation correction (normally used for aurora scenes)")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    # FIXME: Probably need some proper defaults
    group.add_argument("-p", "--products", dest="products", nargs="+", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    # group.add_argument('--i-bands', dest='products', action=ExtendConstAction, const=I_PRODUCTS,
    #                    help="Add all I-band raw products to list of products")
    # group.add_argument('--m-bands', dest='products', action=ExtendConstAction, const=M_PRODUCTS,
    #                    help="Add all M-band raw products to list of products")
    # group.add_argument('--dnb-angle-products', dest='products', action=ExtendConstAction, const=DNB_ANGLE_PRODUCTS,
    #                    help="Add DNB-band geolocation 'angle' products to list of products")
    # group.add_argument('--i-angle-products', dest='products', action=ExtendConstAction, const=I_ANGLE_PRODUCTS,
    #                    help="Add I-band geolocation 'angle' products to list of products")
    # group.add_argument('--m-angle-products', dest='products', action=ExtendConstAction, const=M_ANGLE_PRODUCTS,
    #                    help="Add M-band geolocation 'angle' products to list of products")
    # group.add_argument('--m-rad-products', dest='products', action=ExtendConstAction, const=M_RAD_PRODUCTS,
    #                    help="Add M-band geolocation radiance products to list of products")
    # group.add_argument('--i-rad-products', dest='products', action=ExtendConstAction, const=I_RAD_PRODUCTS,
    #                    help="Add I-band geolocation radiance products to list of products")
    return ["Frontend Initialization", "Frontend Swath Extraction"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    parser = create_basic_parser(description="Extract VIIRS L1B swath data into binary files")
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
    f = Frontend(search_paths=args.data_files, **args.subgroup_args["Frontend Initialization"])

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

if __name__ == "__main__":
    sys.exit(main())
