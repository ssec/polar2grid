#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
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
"""Polar2Grid frontend for extracting data and metadata from files processed by the
Advanced Clear-Sky Processor for Oceans (ACSPO) system.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import os
import sys
import logging
from datetime import datetime, timedelta
import numpy
from netCDF4 import Dataset

from polar2grid.core import roles
from polar2grid.core.fbf import FileAppender
from polar2grid.core import containers

LOG = logging.getLogger(__name__)

# File types (only one for now)
FT_BASIC = "ACSPO_BASIC"  # need more?
# File variables
SST_VAR = "sea_surface_temperature"
LAT_VAR = "latitude"
LON_VAR = "longitude"


class ProductDefinition(object):
    def __init__(self, name, data_kind, file_type, file_key, dependencies=None, description=None, units=None,
                 is_geoproduct=False):
        self.file_type = file_type
        self.file_key = file_key
        self.is_geoproduct = is_geoproduct
        self.name = name
        self.data_kind = data_kind
        self.dependencies = dependencies or []
        self.description = description or ""
        self.units = units or ""


class ProductDict(dict):
    def __init__(self, base_class=ProductDefinition):
        self.base_class = base_class
        super(ProductDict, self).__init__()

    def add_product(self, *args, **kwargs):
        pd = self.base_class(*args, **kwargs)
        self[pd.name] = pd

PRODUCT_SST = "acspo_sst"
PRODUCT_LATITUDE = "acspo_latitude"
PRODUCT_LONGITUDE = "acspo_longitude"

PRODUCTS = ProductDict(base_class=ProductDefinition)
# FUTURE: Add a "geoproduct_pair" field and have a second geoproduct list for the pairs
PRODUCTS.add_product(PRODUCT_LATITUDE, "latitude", FT_BASIC, LAT_VAR,
                     description="Latitude", units="degrees", is_geoproduct=True)
PRODUCTS.add_product(PRODUCT_LONGITUDE, "longitude", FT_BASIC, LON_VAR,
                     description="Longitude", units="degrees", is_geoproduct=True)
PRODUCTS.add_product(PRODUCT_SST, "sea_surface_temperature", FT_BASIC, SST_VAR,
                     description="Rain Rate", units="mm/hr")
GEO_PAIRS = (
    (PRODUCT_LONGITUDE, PRODUCT_LATITUDE),
)

### I/O Operations ###


class FileReader(object):
    """Basic ACSPO file reader.

    If there are alternate formats/structures for ACSPO files then new classes should be made.
    """
    FILE_TYPE = FT_BASIC

    GLOBAL_FILL_ATTR_NAME = "MISSING_VALUE_REAL4"
    # Constant -> (var_name, scale_attr_name, fill_attr_name)
    FILE_STRUCTURE = {
        SST_VAR: ("sst_regression", None, None),
        LAT_VAR: ("latitude", None, None),
        LON_VAR: ("longitude", None, None),
    }

    # best case nadir resolutions in meters (could be made per band):
    INST_NADIR_RESOLUTION = {
    }

    # worst case nadir resolutions in meters (could be made per band):
    INST_LIMB_RESOLUTION = {
    }

    def __init__(self, filepath):
        self.filename = os.path.basename(filepath)
        self.filepath = os.path.realpath(filepath)
        self.nc_obj = Dataset(self.filepath, "r")
        # Not supported in older version of NetCDF4 library
        #self.nc_obj.set_auto_maskandscale(False)
        if not self.handles_file(self.nc_obj):
            LOG.error("Unknown file format for file %s" % (self.filename,))
            raise ValueError("Unknown file format for file %s" % (self.filename,))

        self.satellite = self.nc_obj.SATELLITE.lower()
        self.instrument = self.nc_obj.SENSOR.lower()
        self.begin_time = datetime.strptime(self.nc_obj.TIME_COVERAGE_START, "%Y-%m-%dT%H:%M:%SZ")
        self.end_time = datetime.strptime(self.nc_obj.TIME_COVERAGE_END, "%Y-%m-%dT%H:%M:%SZ")

        if self.instrument in self.INST_NADIR_RESOLUTION:
            self.nadir_resolution = self.INST_NADIR_RESOLUTION.get(self.instrument, None)
        else:
            self.nadir_resolution = None

        if self.instrument in self.INST_LIMB_RESOLUTION:
            self.limb_resolution = self.INST_LIMB_RESOLUTION.get(self.instrument, None)
        else:
            self.limb_resolution = None

    @classmethod
    def handles_file(cls, fn_or_nc_obj):
        """Validate that the file this object represents is something that we actually know how to read.
        """
        try:
            if isinstance(fn_or_nc_obj, str):
                nc_obj = Dataset(fn_or_nc_obj, "r")
            else:
                nc_obj = fn_or_nc_obj

            assert(hasattr(nc_obj, "PROCESSOR") and nc_obj.PROCESSOR.startswith("ACSPO"))
            return True
        except AssertionError:
            LOG.debug("File Validation Exception Information: ", exc_info=True)
            return False

    def __getitem__(self, item):
        if item in self.FILE_STRUCTURE:
            var_name = self.FILE_STRUCTURE[item][0]
            nc_var = self.nc_obj.variables[var_name]
            nc_var.set_auto_maskandscale(False)
            return nc_var
        return self.nc_obj.variables[item]

    def get_fill_value(self, item):
        fill_value = None
        if item in self.FILE_STRUCTURE:
            var_name = self.FILE_STRUCTURE[item][0]
            fill_attr_name = self.FILE_STRUCTURE[item][2]
            if fill_attr_name:
                fill_value = getattr(self.nc_obj.variables[var_name], fill_attr_name)
        if fill_value is None:
            fill_value = getattr(self.nc_obj, self.GLOBAL_FILL_ATTR_NAME, None)

        LOG.debug("File fill value for '%s' is '%f'", item, float(fill_value))
        return fill_value

    def get_scale_value(self, item):
        scale_value = None
        if item in self.FILE_STRUCTURE:
            var_name = self.FILE_STRUCTURE[item][0]
            scale_attr_name = self.FILE_STRUCTURE[item][1]
            if scale_attr_name:
                scale_value = float(self.nc_obj.variables[var_name].getncattr(scale_attr_name))
                LOG.debug("File scale value for '%s' is '%f'", item, float(scale_value))
        return scale_value

    def get_swath_data(self, item, dtype=numpy.float32, fill=numpy.nan):
        """Get swath data from the file. Usually requires special processing.
        """
        var_data = self[item][:].astype(dtype)

        file_fill = self.get_fill_value(item)
        file_scale = self.get_scale_value(item)

        bad_mask = None
        if file_fill:
            if numpy.isnan(file_fill):
                bad_mask = numpy.isnan(var_data)
            else:
                bad_mask = var_data == file_fill
            var_data[bad_mask] = fill
        if file_scale:
            var_data = var_data.astype(dtype)
            if bad_mask is not None:
                var_data[~bad_mask] = var_data[~bad_mask] / file_scale
            else:
                var_data = var_data / file_scale

        return var_data

    def _compare(self, other, method):
        try:
            return method(self.begin_time, other.start_time)
        except AttributeError:
            raise NotImplemented

    def __lt__(self, other):
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        return self._compare(other, lambda s, o: s == o)

    def __ge__(self, other):
        return self._compare(other, lambda s, o: s >= o)

    def __gt__(self, other):
        return self._compare(other, lambda s, o: s > o)

    def __ne__(self, other):
        return self._compare(other, lambda s, o: s != o)


class MultiReader(object):
    SINGLE_FILE_CLASS = FileReader
    FILE_TYPE = SINGLE_FILE_CLASS.FILE_TYPE

    def __init__(self, filenames=None):
        self.file_readers = []
        self._files_finalized = False
        if filenames:
            self.add_files(filenames)
            self.finalize_files()

    def __len__(self):
        return len(self.file_readers)

    @classmethod
    def handles_file(cls, fn_or_nc_obj):
        return cls.SINGLE_FILE_CLASS.handles_file(fn_or_nc_obj)

    def add_file(self, fn):
        if self._files_finalized:
            LOG.error("File reader has been finalized and no more files can be added")
            raise RuntimeError("File reader has been finalized and no more files can be added")
        self.file_readers.append(self.SINGLE_FILE_CLASS(fn))

    def add_files(self, filenames):
        for fn in filenames:
            self.add_file(fn)

    def finalize_files(self):
        self.file_readers = sorted(self.file_readers)
        if not all(fr.instrument == self.file_readers[0].instrument for fr in self.file_readers):
            LOG.error("Can't concatenate files because they are not for the same instrument")
            raise RuntimeError("Can't concatenate files because they are not for the same instrument")
        if not all(fr.satellite == self.file_readers[0].satellite for fr in self.file_readers):
            LOG.error("Can't concatenate files because they are not for the same satellite")
            raise RuntimeError("Can't concatenate files because they are not for the same satellite")
        self._files_finalized = True

    def write_var_to_flat_binary(self, item, filename, dtype=numpy.float32):
        """Write the data from multiple files to one flat binary file.

        :param item: Variable name to retrieve
        :param filename: Filename filename if the file should follow traditional FBF naming conventions
        """
        LOG.info("Writing binary data for %s to file %s", item, filename)
        try:
            with open(filename, "w") as file_obj:
                file_appender = FileAppender(file_obj, dtype)
                for file_reader in self.file_readers:
                    single_array = file_reader.get_swath_data(item)
                    file_appender.append(single_array)
        except StandardError:
            if os.path.isfile(filename):
                os.remove(filename)
            raise

        LOG.debug("File %s has shape %r", filename, file_appender.shape)
        return file_appender.shape

    @property
    def satellite(self):
        return self.file_readers[0].satellite

    @property
    def instrument(self):
        return self.file_readers[0].instrument

    @property
    def begin_time(self):
        return self.file_readers[0].begin_time

    @property
    def end_time(self):
        return self.file_readers[-1].end_time

    @property
    def nadir_resolution(self):
        return self.file_readers[0].nadir_resolution

    @property
    def limb_resolution(self):
        return self.file_readers[0].limb_resolution

    @property
    def filepaths(self):
        return [fr.filepath for fr in self.file_readers]


FILE_CLASSES = {
    FT_BASIC: MultiReader,
}


def get_file_type(filepath):
    LOG.debug("Checking file type for %s", filepath)
    if not filepath.endswith(".nc"):
        return None

    nc_obj = Dataset(filepath, "r")
    for file_kind, file_class in FILE_CLASSES.items():
        if file_class.handles_file(nc_obj):
            return file_kind

    LOG.info("File doesn't match any known file types: %s", filepath)
    return None


class Frontend(roles.FrontendRole):
    """Polar2Grid Frontend object for handling ACSPO files.
    """
    def __init__(self, search_paths=None,
                 overwrite_existing=False, keep_intermediate=False, exit_on_error=False, **kwargs):
        super(Frontend, self).__init__(**kwargs)
        self.overwrite_existing = overwrite_existing
        self.keep_intermediate = keep_intermediate
        self.exit_on_error = exit_on_error
        if not search_paths:
            LOG.info("No files or paths provided as input, will search the current directory...")
            search_paths = ['.']

        self._load_files(search_paths)

    def _load_files(self, search_paths):
        recognized_files = {}
        for file_kind, filepath in self.find_all_files(search_paths):
            if file_kind not in recognized_files:
                recognized_files[file_kind] = []
            recognized_files[file_kind].append(filepath)

        self.file_readers = {}
        for file_type, filepaths in recognized_files.items():
            file_reader_class = FILE_CLASSES[file_type]
            file_reader = file_reader_class(filenames=filepaths)
            if len(file_reader):
                self.file_readers[file_reader.FILE_TYPE] = file_reader

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

    def find_all_files(self, search_paths):
        for p in search_paths:
            if os.path.isdir(p):
                LOG.debug("Searching '%s' for useful files", p)
                for fn in os.listdir(p):
                    fp = os.path.join(p, fn)
                    file_type = get_file_type(fp)
                    if file_type is not None:
                        LOG.debug("Recognize file %s as file type %s", fp, file_type)
                        yield (file_type, os.path.realpath(fp))
            elif os.path.isfile(p):
                file_type = get_file_type(p)
                if file_type is not None:
                    LOG.debug("Recognize file %s as file type %s", p, file_type)
                    yield (file_type, os.path.realpath(p))
                else:
                    LOG.error("File is not a valid ACSPO file: %s", p)
            else:
                LOG.error("File or directory does not exist: %s", p)

    @property
    def available_product_names(self):
        # Right now there is only one type of file that has all products in it, so all products are available
        # in the future this might have to change
        return [k for k, v in PRODUCTS.items() if not v.dependencies and not v.is_geoproduct]

    @property
    def all_product_names(self):
        return PRODUCTS.keys()

    @property
    def begin_time(self):
        return self.file_readers[self.file_readers.keys()[0]].begin_time

    @property
    def end_time(self):
        return self.file_readers[self.file_readers.keys()[0]].end_time

    def create_swath_definition(self, lon_product, lat_product):
        product_def = PRODUCTS[lon_product["product_name"]]
        lon_file_reader = self.file_readers[product_def.file_type]
        product_def = PRODUCTS[lat_product["product_name"]]
        lat_file_reader = self.file_readers[product_def.file_type]

        # sanity check
        for k in ["data_type", "swath_rows", "swath_columns", "rows_per_scan", "fill_value"]:
            if lon_product[k] != lat_product[k]:
                if k == "fill_value" and numpy.isnan(lon_product[k]) and numpy.isnan(lat_product[k]):
                    # NaN special case: NaNs can't be compared normally
                    continue
                LOG.error("Longitude and latitude products do not have equal attributes: %s", k)
                raise RuntimeError("Longitude and latitude products do not have equal attributes: %s" % (k,))

        swath_name = lon_product["product_name"] + "_" + lat_product["product_name"]
        swath_definition = containers.SwathDefinition(
            swath_name=swath_name, longitude=lon_product["swath_data"], latitude=lat_product["swath_data"],
            data_type=lon_product["data_type"], swath_rows=lon_product["swath_rows"],
            swath_columns=lon_product["swath_columns"], rows_per_scan=lon_product["rows_per_scan"],
            source_filenames=sorted(set(lon_file_reader.filepaths + lat_file_reader.filepaths)),
            nadir_resolution=lon_file_reader.nadir_resolution, limb_resolution=lat_file_reader.limb_resolution,
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
        file_reader = self.file_readers[product_def.file_type]
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        # TODO: Get the data type from the data or allow the user to specify
        try:
            shape = file_reader.write_var_to_flat_binary(product_def.file_key, filename)
        except StandardError:
            LOG.error("Could not extract data from file")
            LOG.debug("Extraction exception: ", exc_info=True)
            raise

        one_swath = containers.SwathProduct(
            product_name=product_name, description=product_def.description, units=product_def.units,
            satellite=file_reader.satellite, instrument=file_reader.instrument,
            begin_time=file_reader.begin_time, end_time=file_reader.end_time,
            swath_definition=swath_definition, fill_value=numpy.nan,
            swath_rows=shape[0], swath_columns=shape[1], data_type=numpy.float32, swath_data=filename,
            source_filenames=file_reader.filepaths, data_kind=product_def.data_kind, rows_per_scan=0
        )
        return one_swath

    def create_scene(self, products=None, nprocs=1, **kwargs):
        if nprocs != 1:
            raise NotImplementedError("The ACSPO frontend does not support multiple processes yet")
        if products is None:
            products = self.available_product_names
        orig_products = set(products)
        available_products = self.available_product_names
        doable_products = orig_products & set(available_products)
        for p in (orig_products - doable_products):
            LOG.warning("Missing proper data files to create product: %s", p)
        products = list(doable_products)
        if not products:
            LOG.debug("Original Products:\n\t%r", orig_products)
            LOG.debug("Available Products:\n\t%r", available_products)
            LOG.debug("Doable (final) Products:\n\t%r", products)
            LOG.error("Can not create any of the requested products (missing required data files)")
            raise RuntimeError("Can not create any of the requested products (missing required data files)")

        LOG.debug("Extracting data to create the following products:\n\t%s", "\n\t".join(products))

        scene = containers.SwathScene()

        # Figure out any dependencies
        raw_products = []
        for product_name in products:
            if product_name not in PRODUCTS:
                LOG.error("Unknown product name: %s", product_name)
                raise ValueError("Unknown product name: %s" % (product_name,))
            if PRODUCTS[product_name].dependencies:
                raise NotImplementedError("Don't know how to handle products dependent on other products")
            raw_products.append(product_name)

        # Load geographic products - every product needs a geo-product
        products_created = {}
        swath_definitions = {}
        for geo_product_pair in GEO_PAIRS:
            lon_product_name, lat_product_name = geo_product_pair
            # longitude
            if lon_product_name not in products_created:
                one_lon_swath = self.create_raw_swath_object(lon_product_name, None)
                products_created[lon_product_name] = one_lon_swath
                if lon_product_name in raw_products:
                    # only process the geolocation product if the user requested it that way
                    scene[lon_product_name] = one_lon_swath
            else:
                one_lon_swath = products_created[lon_product_name]

            # latitude
            if lat_product_name not in products_created:
                one_lat_swath = self.create_raw_swath_object(lat_product_name, None)
                products_created[lat_product_name] = one_lat_swath
                if lat_product_name in raw_products:
                    # only process the geolocation product if the user requested it that way
                    scene[lat_product_name] = one_lat_swath
            else:
                one_lat_swath = products_created[lat_product_name]

            swath_definitions[geo_product_pair] = self.create_swath_definition(one_lon_swath, one_lat_swath)

        # Load raw products
        for raw_product in raw_products:
            # FUTURE: Get this info from the product definition
            geo_pair = GEO_PAIRS[0]
            if raw_product not in products_created:
                try:
                    one_lat_swath = self.create_raw_swath_object(raw_product, swath_definitions[geo_pair])
                    products_created[raw_product] = one_lat_swath
                    scene[raw_product] = one_lat_swath
                except StandardError:
                    LOG.error("Could not create raw product '%s'", raw_product)
                    if self.exit_on_error:
                        raise
                    continue

        return scene


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    # FIXME: This may not be true for all instruments handled by MIRS. Proper fix is to have remapping controlled by configuration files.
    parser.set_defaults(fornav_D=40, fornav_d=2)

    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                        help="List available frontend products")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    group.add_argument("-p", "--products", dest="products", nargs="*", default=None, choices=PRODUCTS.keys(),
                       help="Specify frontend products to process")
    return ["Frontend Initialization", "Frontend Swath Extraction"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, setup_logging, create_exc_handler
    parser = create_basic_parser(description="Extract image data from ACSPO files and print JSON scene dictionary")
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
    f = Frontend(args.data_files, **args.subgroup_args["Frontend Initialization"])

    if list_products:
        print("\n".join(f.available_product_names))
        return 0

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
