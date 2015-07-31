#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2012-2015 Space Science and Engineering Center (SSEC),
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
# Written by David Hoese    September 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""The AVHRR frontend is for reading AAPP L1B files for the AVHRR instrument.
The frontend is contained in the `polar2grid.avhrr` python package. These files are
a custom binary format. The frontend can be specified with the ``p2g_glue`` command
using the ``avhrr`` frontend name.
The AVHRR frontend provides the following products:

+--------------------+--------------------------------------------+
| Product Name       | Description                                |
+====================+============================================+
| band1_vis          | Band 1 Visible                             |
+--------------------+--------------------------------------------+
| band2_vis          | Band 2 Visible                             |
+--------------------+--------------------------------------------+
| band3a_vis         | Band 3A Visible                            |
+--------------------+--------------------------------------------+
| band3b_bt          | Band 3B Brightness Temperature             |
+--------------------+--------------------------------------------+
| band4_vis          | Band 4 Brightness Temperature              |
+--------------------+--------------------------------------------+
| band5_vis          | Band 5 Brightness Temperature              |
+--------------------+--------------------------------------------+

|

:author:       David Hoese (davidh)
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012-2015 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import os
import sys
import logging
import numpy

from polar2grid.core import roles
from polar2grid.core import containers
from polar2grid.core.frontend_utils import ProductDict, GeoPairDict
from polar2grid.avhrr import readers

LOG = logging.getLogger(__name__)

PRODUCT_LATITUDE = "latitude1km"
PRODUCT_LONGITUDE = "longitude1km"
PRODUCT_BAND1_VIS = "band1_vis"
PRODUCT_BAND2_VIS = "band2_vis"
PRODUCT_BAND3A_VIS = "band3a_vis"
PRODUCT_BAND3B_BT = "band3b_bt"
PRODUCT_BAND4_BT = "band4_bt"
PRODUCT_BAND5_BT = "band5_bt"
PAIR_1KM = "1km_nav"

PRODUCTS = ProductDict()
PRODUCTS.add_product(PRODUCT_LONGITUDE, PAIR_1KM, "longitude", readers.FT_AAPP, readers.K_LONGITUDE, description="Longitude", units="degrees")
PRODUCTS.add_product(PRODUCT_LATITUDE, PAIR_1KM, "latitude", readers.FT_AAPP, readers.K_LATITUDE, description="Latitude", units="degrees")
PRODUCTS.add_product(PRODUCT_BAND1_VIS, PAIR_1KM, "reflectance", readers.FT_AAPP, readers.K_BAND1, description="AVHRR Band 1 visible", units="percent")
PRODUCTS.add_product(PRODUCT_BAND2_VIS, PAIR_1KM, "reflectance", readers.FT_AAPP, readers.K_BAND2, description="AVHRR Band 2 visible", units="percent")
PRODUCTS.add_product(PRODUCT_BAND3A_VIS, PAIR_1KM, "reflectance", readers.FT_AAPP, readers.K_BAND3a, description="AVHRR Band 3A visible", units="percent", dependencies=(None,))
PRODUCTS.add_product(PRODUCT_BAND3B_BT, PAIR_1KM, "brightness_temperature", readers.FT_AAPP, readers.K_BAND3b, description="AVHRR Band 3B brightness temperature", units="Kelvin", dependencies=(None,))
PRODUCTS.add_product(PRODUCT_BAND4_BT, PAIR_1KM, "brightness_temperature", readers.FT_AAPP, readers.K_BAND4, description="AVHRR Band 4 brightness temperature", units="Kelvin")
PRODUCTS.add_product(PRODUCT_BAND5_BT, PAIR_1KM, "brightness_temperature", readers.FT_AAPP, readers.K_BAND5, description="AVHRR Band 5 brightness temperature", units="Kelvin")

GEO_PAIRS = GeoPairDict()
GEO_PAIRS.add_pair(PAIR_1KM, PRODUCT_LONGITUDE, PRODUCT_LATITUDE, 1)


class Frontend(roles.FrontendRole):
    """Polar2Grid Frontend object for handling AVHRR files.
    """
    FILE_EXTENSIONS = [".l1b"]

    def __init__(self, **kwargs):
        super(Frontend, self).__init__(**kwargs)
        self.load_files(self.find_files_with_extensions())

        self.secondary_product_functions = {
            PRODUCT_BAND3A_VIS: self._mask_band3,
            PRODUCT_BAND3B_BT: self._mask_band3,
        }

    def load_files(self, file_paths):
        """Sort files by 'file type' and create objects to help load the data later.

        This method should not be called by the user.
        """
        self.file_readers = {}
        for file_type, file_type_info in readers.FILE_TYPES.items():
            self.file_readers[file_type] = readers.AVHRRMultiFileReader(file_type_info)

        # Don't modify the passed list (we use in place operations)
        file_paths_left = []
        for fp in file_paths:
            try:
                h = readers.AVHRRReader(fp)
                LOG.debug("Recognize file %s as file type %s", fp, h.file_type)
                if h.file_type in self.file_readers:
                    self.file_readers[h.file_type].add_file(h)
                else:
                    LOG.debug("Recognized the file type, but don't know anything more about the file")
            except StandardError:
                LOG.debug("Could not parse .l1b file as AVHRR AAPP file: %s", fp)
                LOG.debug("File parsing error: ", exc_info=True)
                file_paths_left.append(fp)
                continue

        # Log what files we were given that we didn't understand
        for fp in file_paths_left:
            LOG.debug("Unrecognized file: %s", fp)

        # Get rid of the readers we aren't using
        for file_type, file_reader in self.file_readers.items():
            if not len(file_reader):
                del self.file_readers[file_type]
            else:
                self.file_readers[file_type].finalize_files()

        if not self.file_readers:
            LOG.error("No useable files loaded")
            raise ValueError("No useable files loaded")

        first_length = len(self.file_readers[self.file_readers.keys()[0]])
        if not all(len(x) == first_length for x in self.file_readers.values()):
            LOG.error("Corrupt directory: Varying number of files for each type")
            ft_str = "\n\t".join("%s: %d" % (ft, len(fr)) for ft, fr in self.file_readers.items())
            LOG.debug("File types and number of files:\n\t%s", ft_str)
            raise RuntimeError("Corrupt directory: Varying number of files for each type")

        self.available_file_types = self.file_readers.keys()

    @property
    def begin_time(self):
        return self.file_readers[self.available_file_types[0]].begin_time

    @property
    def end_time(self):
        return self.file_readers[self.available_file_types[0]].end_time

    @property
    def all_product_names(self):
        return PRODUCTS.keys()

    @property
    def available_product_names(self):
        """Return all loadable products including all geolocation products.
        """
        raw_products = [p for p in PRODUCTS.all_raw_products if self.raw_product_available(p)]
        return sorted(PRODUCTS.get_product_dependents(raw_products))

    @property
    def default_products(self):
        """Logical default list of products if not specified by the user
        """
        if os.getenv("P2G_AVHRR_DEFAULTS", None):
            return os.getenv("P2G_AVHRR_DEFAULTS")
        defaults = [
            PRODUCT_BAND1_VIS,
            PRODUCT_BAND2_VIS,
            PRODUCT_BAND3A_VIS,
            PRODUCT_BAND3B_BT,
            PRODUCT_BAND4_BT,
            PRODUCT_BAND5_BT,
        ]
        available = self.available_product_names
        return list(set(defaults) & set(available))

    def raw_product_available(self, product_name):
        """Is it possible to load the provided product with the files provided to the `Frontend`.

        :returns: True if product can be loaded, False otherwise (including if product is not a raw product)
        """
        product_def = PRODUCTS[product_name]
        if product_def.is_raw:
            if isinstance(product_def.file_type, str):
                file_type = product_def.file_type
            else:
                return any(ft in self.file_readers for ft in product_def.file_type)

            return file_type in self.file_readers
        return False

    def create_swath_definition(self, lon_product, lat_product):
        product_def = PRODUCTS[lon_product["product_name"]]
        file_type = product_def.get_file_type(self.available_file_types)
        lon_file_reader = self.file_readers[file_type]
        product_def = PRODUCTS[lat_product["product_name"]]
        file_type = product_def.get_file_type(self.available_file_types)
        lat_file_reader = self.file_readers[file_type]

        # sanity check
        for k in ["data_type", "swath_rows", "swath_columns", "rows_per_scan", "fill_value"]:
            if lon_product[k] != lat_product[k]:
                if k == "fill_value" and numpy.isnan(lon_product[k]) and numpy.isnan(lat_product[k]):
                    # NaN special case: NaNs can't be compared normally
                    continue
                LOG.error("Longitude and latitude products do not have equal attributes: %s", k)
                raise RuntimeError("Longitude and latitude products do not have equal attributes: %s" % (k,))

        swath_name = GEO_PAIRS[product_def.get_geo_pair_name(self.available_file_types)].name
        swath_definition = containers.SwathDefinition(
            swath_name=swath_name, longitude=lon_product["swath_data"], latitude=lat_product["swath_data"],
            data_type=lon_product["data_type"], swath_rows=lon_product["swath_rows"],
            swath_columns=lon_product["swath_columns"], rows_per_scan=lon_product["rows_per_scan"],
            source_filenames=sorted(set(lon_file_reader.filepaths + lat_file_reader.filepaths)),
            # nadir_resolution=lon_file_reader.nadir_resolution, limb_resolution=lat_file_reader.limb_resolution,
            fill_value=lon_product["fill_value"],
            )

        # Tell the lat and lon products not to delete the data arrays, the swath definition will handle that
        lon_product.set_persist()
        lat_product.set_persist()

        # mmmmm, almost circular
        lon_product["swath_definition"] = swath_definition
        lat_product["swath_definition"] = swath_definition

        return swath_definition

    def create_raw_swath_object(self, product_name, swath_definition):
        product_def = PRODUCTS[product_name]
        try:
            file_type = product_def.get_file_type(self.available_file_types)
            file_key = product_def.get_file_key(self.available_file_types)
        except StandardError:
            LOG.error("Could not create product '%s' because some data files are missing" % (product_name,))
            raise RuntimeError("Could not create product '%s' because some data files are missing" % (product_name,))
        file_reader = self.file_readers[file_type]
        LOG.debug("Using file type '%s' and getting file key '%s' for product '%s'", file_type, file_key, product_name)

        LOG.debug("Writing product '%s' data to binary file", product_name)
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        try:
            data_type = file_reader.get_data_type(file_key)
            fill_value = file_reader.get_fill_value(file_key)
            shape = file_reader.write_var_to_flat_binary(file_key, filename, dtype=data_type)
            rows_per_scan = GEO_PAIRS[product_def.get_geo_pair_name(self.available_file_types)].rows_per_scan
        except StandardError:
            LOG.error("Could not extract data from file")
            LOG.debug("Extraction exception: ", exc_info=True)
            raise

        one_swath = containers.SwathProduct(
            product_name=product_name, description=product_def.description, units=product_def.units,
            satellite=file_reader.satellite, instrument=file_reader.instrument,
            begin_time=file_reader.begin_time, end_time=file_reader.end_time,
            swath_definition=swath_definition, fill_value=fill_value,
            swath_rows=shape[0], swath_columns=shape[1], data_type=data_type, swath_data=filename,
            source_filenames=file_reader.filepaths, data_kind=product_def.data_kind, rows_per_scan=rows_per_scan
        )
        return one_swath

    def create_secondary_swath_object(self, product_name, swath_definition, filename, data_type, products_created):
        product_def = PRODUCTS[product_name]
        dep_objects = [products_created[dep_name] for dep_name in product_def.dependencies]
        filepaths = sorted(set([filepath for swath in dep_objects for filepath in swath["source_filenames"]]))

        s = dep_objects[0]
        one_swath = containers.SwathProduct(
            product_name=product_name, description=product_def.description, units=product_def.units,
            satellite=s["satellite"], instrument=s["instrument"],
            begin_time=s["begin_time"], end_time=s["end_time"],
            swath_definition=swath_definition, fill_value=numpy.nan,
            swath_rows=s["swath_rows"], swath_columns=s["swath_columns"], data_type=data_type, swath_data=filename,
            source_filenames=filepaths, data_kind=product_def.data_kind, rows_per_scan=s["rows_per_scan"]
        )
        return one_swath

    def create_scene(self, products=None, **kwargs):
        LOG.debug("Loading scene data...")
        # If the user didn't provide the products they want, figure out which ones we can create
        if products is None:
            LOG.debug("No products specified to frontend, will try to load logical defaults")
            products = self.default_products

        # Do we actually have all of the files needed to create the requested products?
        products = self.loadable_products(products)

        # Needs to be ordered (least-depended product -> most-depended product)
        products_needed = PRODUCTS.dependency_ordered_products(products)
        geo_pairs_needed = PRODUCTS.geo_pairs_for_products(products_needed, self.available_file_types)
        # both lists below include raw products that need extra processing/masking
        raw_products_needed = (p for p in products_needed if PRODUCTS.is_raw(p, geo_is_raw=False))
        secondary_products_needed = [p for p in products_needed if PRODUCTS.needs_processing(p)]
        for p in secondary_products_needed:
            if p not in self.secondary_product_functions:
                msg = "Product (secondary or extra processing) required, but not sure how to make it: '%s'" % (p,)
                LOG.error(msg)
                raise ValueError(msg)

        # final scene object we'll be providing to the caller
        scene = containers.SwathScene()
        # Dictionary of all products created so far (local variable so we don't hold on to any product objects)
        products_created = {}
        swath_definitions = {}

        # Load geolocation files
        for geo_pair_name in geo_pairs_needed:
            ### Lon Product ###
            lon_product_name = GEO_PAIRS[geo_pair_name].lon_product
            LOG.info("Creating navigation product '%s'", lon_product_name)
            lon_swath = products_created[lon_product_name] = self.create_raw_swath_object(lon_product_name, None)
            if lon_product_name in products:
                scene[lon_product_name] = lon_swath

            ### Lat Product ###
            lat_product_name = GEO_PAIRS[geo_pair_name].lat_product
            LOG.info("Creating navigation product '%s'", lat_product_name)
            lat_swath = products_created[lat_product_name] = self.create_raw_swath_object(lat_product_name, None)
            if lat_product_name in products:
                scene[lat_product_name] = lat_swath

            # Create the SwathDefinition
            swath_def = self.create_swath_definition(lon_swath, lat_swath)
            swath_definitions[swath_def["swath_name"]] = swath_def

        # Create each raw products (products that are loaded directly from the file)
        for product_name in raw_products_needed:
            if product_name in products_created:
                # already created
                continue

            try:
                LOG.info("Creating data product '%s'", product_name)
                swath_def = swath_definitions[PRODUCTS[product_name].get_geo_pair_name(self.available_file_types)]
                one_swath = products_created[product_name] = self.create_raw_swath_object(product_name, swath_def)
            except StandardError:
                LOG.error("Could not create raw product '%s'", product_name)
                if self.exit_on_error:
                    raise
                continue

            if product_name in products:
                # the user wants this product
                scene[product_name] = one_swath

        # Dependent products and Special cases (i.e. non-raw products that need further processing)
        for product_name in reversed(secondary_products_needed):
            product_func = self.secondary_product_functions[product_name]
            swath_def = swath_definitions[PRODUCTS[product_name].get_geo_pair_name(self.available_file_types)]

            try:
                LOG.info("Creating secondary product '%s'", product_name)
                one_swath = product_func(product_name, swath_def, products_created)
            except StandardError:
                LOG.error("Could not create product (unexpected error): '%s'", product_name)
                LOG.debug("Could not create product (unexpected error): '%s'", product_name, exc_info=True)
                if self.exit_on_error:
                    raise
                del scene[product_name]
                continue

            if one_swath is None:
                LOG.debug("Secondary product function did not produce a swath product")
                if product_name in scene:
                    LOG.debug("Removing original swath that was created before")
                    del scene[product_name]
                continue
            products_created[product_name] = one_swath
            if product_name in products:
                # the user wants this product
                scene[product_name] = one_swath

        return scene

    def _mask_band3(self, product_name, swath_def, products_created):
        product_def = PRODUCTS[product_name]
        # Get the file reader for this product (make sure to check all available file readers for the best match)
        file_reader = self.file_readers[product_def.get_file_type(self.file_readers.keys())]
        # mask is True if band is 3b, False if 3a
        band_mask = file_reader.get_swath_data(readers.K_BAND3_MASK)
        base_product = products_created[product_name]
        shape = (base_product["swath_rows"], base_product["swath_columns"])
        # inplace data modifications (not a usual case so not supported by SwathProduct object)
        product_data = numpy.memmap(base_product["swath_data"], dtype=base_product["data_type"], shape=shape)

        # Handle band 3 products
        if product_name in [PRODUCT_BAND3A_VIS]:
            # if every pixel we have is a band 3B pixel then we don't want to create this product
            if numpy.all(band_mask):
                LOG.info("No band 3A visible data available, will not create the '%s' product", product_name)
                return None

            # where the data is for 3B make it invalid with a NaN fill value
            product_data[band_mask] = numpy.nan
        else:
            # band 3b products
            # if every pixel we have is a band 3A pixel then we don't want to create this product
            if numpy.all(band_mask == 0):
                LOG.info("No band 3B reflectance data available, will not create the '%s' product", product_name)
                return None

            # where the data is for 3A or the value is less than 0.1 then mask it with a NaN fill value
            # Note: this logic was taken from the mpop aapp1b.py module
            product_data[(band_mask == 0) | (product_data < 0.1)] = numpy.nan

        # best way to close the memmap?
        del product_data

        return products_created[product_name]


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    from polar2grid.core.script_utils import ExtendAction
    # Set defaults for other components that may be used in polar2grid processing
    parser.set_defaults(remap_method="nearest")

    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                        help="List available frontend products")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    group.add_argument("-p", "--products", dest="products", nargs="*", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    return ["Frontend Initialization", "Frontend Swath Extraction"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, setup_logging, create_exc_handler
    parser = create_basic_parser(description="Extract image data from AVHRR files and print JSON scene dictionary")
    subgroup_titles = add_frontend_argument_groups(parser)
    parser.add_argument('-f', dest='data_files', nargs="+", default=[],
                        help="List of data files and directories to get extract data from")
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
