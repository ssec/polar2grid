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
"""The MIRS frontend extracts data from files created by the Microwave Integrated Retrieval System (MIRS).
The frontend offers the following products:

    +--------------------+--------------------------------------------+
    | Product Name       | Description                                |
    +====================+============================================+
    | mirs_rain_rate     | Rain Rate                                  |
    +--------------------+--------------------------------------------+
    | mirs_btemp_90      | Brightness Temperature at 88.2GHz          |
    +--------------------+--------------------------------------------+

|

:author:       David Hoese (davidh)
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012-2015 University of Wisconsin SSEC. All rights reserved.
:date:         Sept 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import os
import sys
import logging
from datetime import datetime, timedelta
import numpy as np
from netCDF4 import Dataset

from polar2grid.core import roles
from polar2grid.core import containers
from polar2grid.core.frontend_utils import BaseMultiFileReader, BaseFileReader, ProductDict, GeoPairDict

try:
    # try getting setuptools/distribute's version of resource retrieval first
    from pkg_resources import resource_string as get_resource_string
except ImportError:
    from pkgutil import get_data as get_resource_string

LOG = logging.getLogger(__name__)

# File types (only one for now)
FT_IMG = "MIRS_IMG"
# File variables
RR_VAR = "rr_var"
BT_90_VAR = "bt_90_var"
FREQ_VAR = "freq_var"
LAT_VAR = "latitude_var"
LON_VAR = "longitude_var"

BT_VARS = [BT_90_VAR]


PRODUCT_RAIN_RATE = "mirs_rain_rate"
PRODUCT_BT_90 = "mirs_btemp_90"
PRODUCT_LATITUDE = "mirs_latitude"
PRODUCT_LONGITUDE = "mirs_longitude"

PAIR_MIRS_NAV = "mirs_nav"

PRODUCTS = ProductDict()
PRODUCTS.add_product(PRODUCT_LATITUDE, PAIR_MIRS_NAV, "latitude", FT_IMG, LAT_VAR, description="Latitude", units="degrees")
PRODUCTS.add_product(PRODUCT_LONGITUDE, PAIR_MIRS_NAV, "longitude", FT_IMG, LON_VAR, description="Longitude", units="degrees")
PRODUCTS.add_product(PRODUCT_RAIN_RATE, PAIR_MIRS_NAV, "rain_rate", FT_IMG, RR_VAR, description="Rain Rate", units="mm/hr")
PRODUCTS.add_product(PRODUCT_BT_90, PAIR_MIRS_NAV, "brightness_temperature", FT_IMG, BT_90_VAR, description="Channel Brightness Temperature at 88.2GHz", units="K")

GEO_PAIRS = GeoPairDict()
GEO_PAIRS.add_pair(PAIR_MIRS_NAV, PRODUCT_LONGITUDE, PRODUCT_LATITUDE, 0)

### I/O Operations ###

FILE_STRUCTURE = {
    RR_VAR: ("RR", ("scale", "scale_factor"), None, None),
    BT_90_VAR: ("BT", ("scale", "scale_factor"), None, 88.2),
    FREQ_VAR: ("Freq", None, None, None),
    LAT_VAR: ("Latitude", None, None, None),
    LON_VAR: ("Longitude", None, None, None),
    }


LIMB_SEA_FILE = os.environ.get("ATMS_LIMB_SEA", "polar2grid.mirs:limball_atmssea.txt")
LIMB_LAND_FILE = os.environ.get("ATMS_LIMB_LAND", "polar2grid.mirs:limball_atmsland.txt")


def read_atms_limb_correction_coefficients(fn):
    if os.path.isfile(fn):
        coeff_str = open(fn, "r").readlines()
    else:
        parts = fn.split(":")
        mod_part, file_part = parts if len(parts) == 2 else ("", parts[0])
        mod_part = mod_part or __package__  # self.__module__
        coeff_str = get_resource_string(mod_part, file_part).split("\n")
    # make it a generator
    coeff_str = (line.strip() for line in coeff_str)

    all_coeffs = np.zeros((22, 96, 22), dtype=np.float32)
    all_amean = np.zeros((22, 96, 22), dtype=np.float32)
    all_dmean = np.zeros(22, dtype=np.float32)
    all_nchx = np.zeros(22, dtype=np.int32)
    all_nchanx = np.zeros((22, 22), dtype=np.int32)
    all_nchanx[:] = -1
    # There should be 22 sections
    for chan_idx in range(22):
        # blank line at the start of each section
        _ = next(coeff_str)

        # section header
        nx, nchx, dmean = [x.strip() for x in next(coeff_str).split(" ") if x]
        nx = int(nx)
        all_nchx[chan_idx] = nchx = int(nchx)
        all_dmean[chan_idx] = float(dmean)

        # coeff locations (indexes to put the future coefficients in)
        locations = [int(x.strip()) for x in next(coeff_str).split(" ") if x]
        assert(len(locations) == nchx)
        for x in range(nchx):
            all_nchanx[chan_idx, x] = locations[x] - 1

        # Read 'nchx' coefficients for each of 96 FOV
        for fov_idx in range(96):
            # chan_num, fov_num, *coefficients, error
            coeff_line_parts = [x.strip() for x in next(coeff_str).split(" ") if x][2:]
            coeffs = [float(x) for x in coeff_line_parts[:nchx]]
            ameans = [float(x) for x in coeff_line_parts[nchx:-1]]
            error_val = float(coeff_line_parts[-1])
            for x in range(nchx):
                all_coeffs[chan_idx, fov_idx, all_nchanx[chan_idx, x]] = coeffs[x]
                all_amean[all_nchanx[chan_idx, x], fov_idx, chan_idx] = ameans[x]

    return all_dmean, all_coeffs, all_amean, all_nchx, all_nchanx

def apply_atms_limb_correction(datasets):
    pass


class NetCDFFileReader(object):
    def __init__(self, filepath):
        self.filename = os.path.basename(filepath)
        self.filepath = os.path.realpath(filepath)
        self.nc_obj = Dataset(self.filepath, "r")

    def __getattr__(self, item):
        return getattr(self.nc_obj, item)

    def __getitem__(self, item):
        return self.nc_obj.variables[item]


class MIRSFileReader(BaseFileReader):
    """Basic MIRS file reader.

    If there are alternate formats/structures for MIRS files then new classes should be made.
    """
    FILE_TYPE = FT_IMG

    GLOBAL_FILL_ATTR_NAME = "missing_value"
    # Constant -> (var_name, scale_attr_name, fill_attr_name, frequency)

    # best case nadir resolutions in meters (could be made per band):
    INST_NADIR_RESOLUTION = {
        "atms": 15800,
        "mhs": 20300,
    }

    # worst case nadir resolutions in meters (could be made per band):
    INST_LIMB_RESOLUTION = {
        "atms": 323100,
        "mhs": 323100,
    }

    def __init__(self, filepath, file_type_info):
        super(MIRSFileReader, self).__init__(NetCDFFileReader(filepath), file_type_info)
        # Not supported in older version of NetCDF4 library
        #self.file_handle.set_auto_maskandscale(False)
        if not self.handles_file(self.file_handle):
            LOG.error("Unknown file format for file %s" % (self.filename,))
            raise ValueError("Unknown file format for file %s" % (self.filename,))

        # IMG_SX.M1.D15238.S1614.E1627.B0000001.WE.HR.ORB.nc
        fn_parts = self.file_handle.filename.split(".")
        try:
            self.satellite = self.file_handle.satellite_name.lower()
            self.instrument = self.file_handle.instrument_name.lower()
            self.begin_time = datetime.strptime(self.file_handle.time_coverage_start, "%Y-%m-%dT%H:%M:%SZ")
            self.end_time = datetime.strptime(self.file_handle.time_coverage_end, "%Y-%m-%dT%H:%M:%SZ")
        except AttributeError:
            self.satellite = {
                "M1": "metopa",
                "M2": "metopb",
                "NN": "noaa18",
                "NP": "noaa19",
            }[fn_parts[1]]
            self.instrument = "mhs"  # actually combination of mhs and amsu
            self.begin_time = datetime.strptime(fn_parts[2][1:] + fn_parts[3][1:], "%y%j%H%M")
            self.end_time = datetime.strptime(fn_parts[2][1:] + fn_parts[4][1:], "%y%j%H%M")

        if self.instrument in self.INST_NADIR_RESOLUTION:
            self.nadir_resolution = self.INST_NADIR_RESOLUTION[self.instrument]
        else:
            self.nadir_resolution = None

        if self.instrument in self.INST_LIMB_RESOLUTION:
            self.limb_resolution = self.INST_LIMB_RESOLUTION[self.instrument]
        else:
            self.limb_resolution = None

    @classmethod
    def handles_file(cls, fn_or_nc_obj):
        """Validate that the file this object represents is something that we actually know how to read.
        """
        try:
            if isinstance(fn_or_nc_obj, str):
                nc_obj = NetCDFFileReader(fn_or_nc_obj, "r")
            else:
                nc_obj = fn_or_nc_obj

            return True
        except AssertionError:
            LOG.debug("File Validation Exception Information: ", exc_info=True)
            return False

    def __getitem__(self, item):
        known_item = self.file_type_info.get(item, item)
        if known_item is None:
            raise KeyError("Key 'None' was not found")

        LOG.debug("Loading %s from %s", known_item[0], self.filename)
        nc_var = self.file_handle[known_item[0]]
        nc_var.set_auto_maskandscale(False)
        return nc_var

    def get_fill_value(self, item):
        fill_value = None
        if item in FILE_STRUCTURE:
            var_name = FILE_STRUCTURE[item][0]
            fill_attr_name = FILE_STRUCTURE[item][2]
            if fill_attr_name:
                fill_value = getattr(self.file_handle[var_name], fill_attr_name)
        if fill_value is None:
            fill_value = getattr(self.file_handle, self.GLOBAL_FILL_ATTR_NAME, None)

        LOG.debug("File fill value for '%s' is '%f'", item, float(fill_value))
        return fill_value

    def get_scale_value(self, item):
        scale_value = None
        if item in FILE_STRUCTURE:
            var_name = FILE_STRUCTURE[item][0]
            scale_attr_name = FILE_STRUCTURE[item][1]
            if scale_attr_name:
                if isinstance(scale_attr_name, (str, unicode)):
                    scale_attr_name = [scale_attr_name]
                for x in scale_attr_name:
                    try:
                        scale_value = float(self.file_handle[var_name].getncattr(x))
                        LOG.debug("File scale value for '%s' is '%f'", item, float(scale_value))
                        break
                    except AttributeError:
                        pass
        return scale_value

    def filter_by_frequency(self, item, arr, freq):
        freq_var = self[FREQ_VAR]
        freq_idx = np.nonzero(freq_var[:] == freq)[0]
        # try getting something close
        if freq_idx.shape[0] == 0:
            freq_idx = np.nonzero(np.isclose(freq_var[:], freq, atol=1))[0]
        if freq_idx.shape[0] != 0:
            freq_idx = freq_idx[0]
        else:
            LOG.error("Frequency %f for variable %s does not exist" % (freq, item))
            raise ValueError("Frequency %f for variable %s does not exist" % (freq, item))

        freq_dim_idx = self[item].dimensions.index(freq_var.dimensions[0])
        idx_obj = [slice(x) for x in arr.shape]
        idx_obj[freq_dim_idx] = freq_idx
        return arr[idx_obj]

    def get_swath_data(self, item, dtype=np.float32, fill=np.nan):
        """Get swath data from the file. Usually requires special processing.
        """
        var_data = self[item][:].astype(dtype)
        freq = FILE_STRUCTURE[item][3]
        if freq:
            var_data = self.filter_by_frequency(item, var_data, freq)

        file_fill = self.get_fill_value(item)
        file_scale = self.get_scale_value(item)

        bad_mask = None
        if file_fill:
            if item == LON_VAR:
                # Because appaarently -999.79999877929688 is a fill value now
                bad_mask = (var_data == file_fill) | (var_data < -180) | (var_data > 180)
            elif item == LAT_VAR:
                # Because appaarently -999.79999877929688 is a fill value now
                bad_mask = (var_data == file_fill) | (var_data < -90) | (var_data > 90)
            else:
                bad_mask = var_data == file_fill
            var_data[bad_mask] = fill
        if file_scale:
            var_data = var_data.astype(dtype)
            if bad_mask is not None:
                var_data[~bad_mask] = var_data[~bad_mask] * file_scale
            else:
                var_data = var_data * file_scale

        return var_data


class MIRSMultiReader(BaseMultiFileReader):
    def __init__(self, filenames=None):
        super(MIRSMultiReader, self).__init__(FILE_STRUCTURE, MIRSFileReader)

    @classmethod
    def handles_file(cls, fn_or_nc_obj):
        return MIRSFileReader.handles_file(fn_or_nc_obj)

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
    FT_IMG: MIRSMultiReader,
}


def get_file_type(filepath):
    LOG.debug("Checking file type for %s", filepath)
    if not filepath.endswith(".nc"):
        return None

    nc_obj = Dataset(filepath, "r")
    for file_kind, file_class in FILE_CLASSES.items():
        if file_class.handles_file(nc_obj):
            return file_kind

    LOG.debug("File doesn't match any known file types: %s", filepath)
    return None


class Frontend(roles.FrontendRole):
    """Polar2Grid Frontend object for handling MIRS files.
    """
    FILE_EXTENSIONS = [".nc"]

    def __init__(self, **kwargs):
        super(Frontend, self).__init__(**kwargs)
        self._load_files(self.find_files_with_extensions())

    def _load_files(self, filepaths):
        self.file_readers = {}
        for filepath in filepaths:
            file_type = get_file_type(filepath)
            if file_type is None:
                LOG.debug("Unrecognized file: %s", filepath)
                continue

            if file_type in self.file_readers:
                file_reader = self.file_readers[file_type]
            else:
                self.file_readers[file_type] = file_reader = FILE_CLASSES[file_type]()
                self.file_readers[file_type]
            file_reader.add_file(filepath)

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
    def available_product_names(self):
        raw_products = [p for p in PRODUCTS.all_raw_products if self.raw_product_available(p)]
        return sorted(PRODUCTS.get_product_dependents(raw_products))

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

    @property
    def all_product_names(self):
        return PRODUCTS.keys()

    @property
    def default_products(self):
        if os.getenv("P2G_MIRS_DEFAULTS", None):
            return os.getenv("P2G_MIRS_DEFAULTS")

        return [PRODUCT_RAIN_RATE, PRODUCT_BT_90]

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
                if k == "fill_value" and np.isnan(lon_product[k]) and np.isnan(lat_product[k]):
                    # NaN special case: NaNs can't be compared normally
                    continue
                LOG.error("Longitude and latitude products do not have equal attributes: %s", k)
                raise RuntimeError("Longitude and latitude products do not have equal attributes: %s" % (k,))

        swath_name = lon_product["product_name"] + "_" + lat_product["product_name"]
        swath_definition = containers.SwathDefinition(
            swath_name=swath_name, longitude=lon_product["swath_data"], latitude=lat_product["swath_data"],
            data_type=lon_product["data_type"], swath_rows=lon_product["swath_rows"],
            swath_columns=lon_product["swath_columns"], rows_per_scan=lon_product["swath_rows"],
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
            swath_definition=swath_definition, fill_value=np.nan,
            swath_rows=shape[0], swath_columns=shape[1], data_type=np.float32, swath_data=filename,
            source_filenames=file_reader.filepaths, data_kind=product_def.data_kind, rows_per_scan=shape[0],
        )
        return one_swath

    def create_scene(self, products=None, nprocs=1, **kwargs):
        if nprocs != 1:
            raise NotImplementedError("The MIRS frontend does not support multiple processes yet")
        if products is None:
            LOG.debug("No products specified to frontend, will try to load logical defaults")
            products = self.default_products

        # Do we actually have all of the files needed to create the requested products?
        products = self.loadable_products(products)

        # Needs to be ordered (least-depended product -> most-depended product)
        products_needed = PRODUCTS.dependency_ordered_products(products)
        geo_pairs_needed = PRODUCTS.geo_pairs_for_products(products_needed, self.available_file_types)
        # both lists below include raw products that need extra processing/masking
        raw_products_needed = (p for p in products_needed if PRODUCTS.is_raw(p, geo_is_raw=True))
        secondary_products_needed = [p for p in products_needed if PRODUCTS.needs_processing(p)]
        for p in secondary_products_needed:
            if p not in self.secondary_product_functions:
                msg = "Product (secondary or extra processing) required, but not sure how to make it: '%s'" % (p,)
                LOG.error(msg)
                raise ValueError(msg)

        LOG.debug("Extracting data to create the following products:\n\t%s", "\n\t".join(products))
        # final scene object we'll be providing to the caller
        scene = containers.SwathScene()
        # Dictionary of all products created so far (local variable so we don't hold on to any product objects)
        products_created = {}
        swath_definitions = {}

        # Load geographic products - every product needs a geo-product
        for geo_pair_name in geo_pairs_needed:
            lon_product_name = GEO_PAIRS[geo_pair_name].lon_product
            lat_product_name = GEO_PAIRS[geo_pair_name].lat_product
            # longitude
            if lon_product_name not in products_created:
                one_lon_swath = self.create_raw_swath_object(lon_product_name, None)
                products_created[lon_product_name] = one_lon_swath
                if lon_product_name in products:
                    # only process the geolocation product if the user requested it that way
                    scene[lon_product_name] = one_lon_swath
            else:
                one_lon_swath = products_created[lon_product_name]

            # latitude
            if lat_product_name not in products_created:
                one_lat_swath = self.create_raw_swath_object(lat_product_name, None)
                products_created[lat_product_name] = one_lat_swath
                if lat_product_name in products:
                    # only process the geolocation product if the user requested it that way
                    scene[lat_product_name] = one_lat_swath
            else:
                one_lat_swath = products_created[lat_product_name]

            swath_definitions[geo_pair_name] = self.create_swath_definition(one_lon_swath, one_lat_swath)

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

        return scene


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    # parser.set_defaults(remap_method="ewa", fornav_D=100, fornav_d=1, maximum_weight_mode=True)
    parser.set_defaults(remap_method="ewa", fornav_D=100, fornav_d=1)

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
    parser = create_basic_parser(description="Extract image data from MIRS files and print JSON scene dictionary")
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
