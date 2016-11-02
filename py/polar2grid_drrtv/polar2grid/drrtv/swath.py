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
# Written by David Hoese    November 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""The Dual Regression Retrieval (DR-RTV) frontend reads HDF5 files created by DR-RTV software
created by Bill Smith Sr., Elisabeth Wiessz, and Nadia Smith at the Space Science and Engineering Center.

Note that Dual Regression products are indexed differently than other satellite-based products:
  [in-track, cross-track] for 2D variables
  [level, in-track, cross-track] for 3D variables

The frontend provides the products listed below. Some products are extracted per pressure level and has special
suffixes. Suffixes are "_100mb", "_200mb", "_300mb", "_400mb", "_500mb", "_600mb", "_700mb", and "_800mb".


    +--------------------+--------------------------------------------+
    | Product Name       | Description                                |
    +====================+============================================+
    | CAPE               | Convective Available Potential Energy      |
    +--------------------+--------------------------------------------+
    | CO2_Amount         | Carbon Dioxide Amount                      |
    +--------------------+--------------------------------------------+
    | COT                | Cloud Optical Thickness                    |
    +--------------------+--------------------------------------------+
    | CTP                | Cloud Top Pressure                         |
    +--------------------+--------------------------------------------+
    | CTT                | Cloud Top Temperature                      |
    +--------------------+--------------------------------------------+
    | CldEmis            | Cloud Emissivity                           |
    +--------------------+--------------------------------------------+
    | Cmask              | Cloud Mask                                 |
    +--------------------+--------------------------------------------+
    | Lifted_Index       | Lifted Index                               |
    +--------------------+--------------------------------------------+
    | SurfPres           | Surface Pressure                           |
    +--------------------+--------------------------------------------+
    | TSurf              | Surface Temperature                        |
    +--------------------+--------------------------------------------+
    | totH2O             | Total Water                                |
    +--------------------+--------------------------------------------+
    | totO3              | Total Ozone                                |
    +--------------------+--------------------------------------------+
    | *Level based products*                                          |
    +--------------------+--------------------------------------------+
    | Dewpnt_100mb       | Dewpoint Temperature                       |
    +--------------------+--------------------------------------------+
    | H2OMMR_100mb       | Water Mixing Ratio                         |
    +--------------------+--------------------------------------------+
    | O3VMR_100mb        | Ozone Mixing Ratio                         |
    +--------------------+--------------------------------------------+
    | RelHum_100mb       | Relative Humidity                          |
    +--------------------+--------------------------------------------+
    | TAir_100mb         | Air Temperature                            |
    +--------------------+--------------------------------------------+

|

:author:       Ray Garcia (rayg)
:author:       David Hoese (davidh)
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012-2015 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2014
:license:      GNU GPLv3


"""

__docformat__ = "restructuredtext en"

import h5py
import numpy as np
import os
import sys
import logging
import re
from datetime import datetime
from functools import partial
from scipy import interpolate

from polar2grid.core.roles import FrontendRole
from polar2grid.core.frontend_utils import ProductDict, GeoPairDict
from polar2grid.core import containers

LOG = logging.getLogger(__name__)

# Reliably chop filenames into identifying pieces
# e.g. IASI_d20130310_t152624_M02.atm_prof_rtv.h5
RE_DRRTV = re.compile(r'(?P<inst>[A-Za-z0-9]+)_d(?P<date>\d+)_t(?P<start_time>\d+)(?:_(?P<sat>[A-Za-z0-9]+))?.*?\.h5')

# whether or not to interpolate data to an exploded swath
DEFAULT_EXPLODE_SAMPLING = False
EXPLODE_FACTOR = 64

# GUIDEBOOK
# FUTURE: move this to another file when it grows large enough
# this table converts filename components to polar2grid identifiers (satellite, instrument, scan-line-grouping)
# scan-line grouping is significant to MS2GT components
# (sat, inst) => (p2g_sat, p2g_inst, rows_per_swath)
SAT_INST_TABLE = {
    (None, 'CRIS'): ("npp", "cris", 3),
    (None, 'CrIS'): ("npp", "cris", 3),
    ('M02', 'IASI'): ("metopa", "iasi", 0),
    ('M01', 'IASI'): ("metopb", "iasi", 0),
    # ('g195', 'AIRS'): (None, None, 0),  # FIXME this needs work
    (None, 'AIRS'): ("aqua", "airs", 0),
}


def _filename_info(pathname):
    """
    return a dictionary of metadata found in the filename
    :param pathname: dual retrieval HDF output file path
    :return: dictionary of polar2grid information found in the filename, or None if the file cannot be used
    """
    m = RE_DRRTV.match(os.path.split(pathname)[-1])
    if not m:
        LOG.debug('%s doesn\'t match DR-RTV file naming convention' % pathname)
        return None
    mgd = m.groupdict()
    when = datetime.strptime('%(date)s %(start_time)s' % mgd, '%Y%m%d %H%M%S')
    # fetch with preference toward satellite matching - failing that, check with sat=None case
    sat, inst, rps = SAT_INST_TABLE.get((mgd['sat'], mgd['inst']),
                                        SAT_INST_TABLE.get((None, mgd['inst'])))
    return { 'begin_time': when,
             'sat': sat,
             'instrument': inst,    # why is this not 'inst'? or 'sat' 'satellite'?
             'rows_per_scan': rps,
             'filepath': pathname,
             }

def _swath_shape(*h5s):
    """
    determine the shape of the retrieval swath
    :param h5s: list of hdf5 objects
    :return: (layers, rows, cols)
    """
    layers, rows, cols = 0, 0, 0
    for h5 in h5s:
        rh = h5['RelHum']
        l, r, c = rh.shape
        if layers == 0:
            layers = l
        if cols == 0:
            cols = c
        rows += r
    return layers, rows, cols


def _swath_info(*h5s):
    """
    return FrontEnd metadata found in attributes
    :param h5s: hdf5 object list
    :return: dictionary of metadata extracted from attributes, including extra '_plev' pressure variable
    """
    fn_info = _filename_info(h5s[0].filename)
    LOG.debug(repr(fn_info))
    layers, rows, cols = _swath_shape(*h5s)
    rps = fn_info['rows_per_scan']
    # fn_info['rows_per_scan'] = rows
    zult = {'swath_rows': rows,
            'swath_cols': cols,
            'swath_scans': rows / rps,
            '_plev': h5s[0]['Plevs'][:].squeeze()
            }
    zult.update(fn_info)
    return zult


def _explode(data, factor):
    rows,cols = data.shape
    r = np.arange(rows, dtype=np.float64)
    c = np.arange(cols, dtype=np.float64)
    rr = np.linspace(0.0, float(rows-1), rows*factor)
    cc = np.linspace(0.0, float(cols-1), cols*factor)
    spl = interpolate.RectBivariateSpline(r, c, data, kx=1, ky=1)
    return spl(rr,cc).astype(np.float32)


def _make_longitude_monotonic(lon_swath):
    """DEPRECATED!
    Modify longitude in place to be monotonic -180..180 or 0..360
    :param lon_swath: 2D numpy masked_array of longitude data
    :return: modified array
    """
    rows,cols = lon_swath.shape
    shift = False
    for r in range(rows):
        dif = np.abs(np.diff(lon_swath[r,:].squeeze()))
        if np.max(dif) > 180.0:
            shift = True
            break
    if shift:
        lon_swath[lon_swath < 0] += 360.0
    return lon_swath


def _swath_from_var(var_name, h5_var, tool=None):
    """
    given a variable by name, and its hdf5 variable object,
    return a normalized numpy masked_array with corrected indexing order
    :param var_name: variable name, used to consult internal guidebook
    :param h5_var: hdf5 object
    :return: numpy masked_array with missing data properly masked and dimensions corrected to
            [in-track, cross-track, layer] for 3D variables
    """
    if tool is not None:
        data = tool(h5_var)
    else:
        data = h5_var[:]
    shape = data.shape

    if len(shape) == 3:
        # roll the layer axis to the back, eg (101, 84, 60) -> (84, 60, 101)
        LOG.debug('rolling %s layer axis to last position' % var_name)
        data = np.rollaxis(data, 0, 3)

    if 'missing_value' in h5_var.attrs:
        mv = float(h5_var.attrs['missing_value'][0])
        LOG.debug('missing value for %s is %s' % (var_name, mv))
        mask = np.abs(data - mv) < 0.5
        data[mask] = np.nan  # FUTURE: we'd rather just deal with masked_array properly in output layer
        data = np.ma.masked_array(data, mask)  # FUTURE: convince scientists to use NaN. also world peace
        LOG.debug('min, max = %s, %s' % (np.min(data.flatten()), np.max(data.flatten())))
    else:
        LOG.warning('no missing_value attribute in %s' % var_name)
        data = np.ma.masked_array(data)

    return data


def _get_whole_var(h5s, var_name, tool, explode=DEFAULT_EXPLODE_SAMPLING, filter=None):
    "extract a swath to a FBF file and return the path"
    # these aren't huge arrays so it's fine to hold them all in memory
    sections = [_swath_from_var(var_name, h5[var_name], tool) for h5 in h5s]
    swath = np.concatenate(sections, axis=0)
    swarthy = swath if filter is None else filter(swath)
    data = _explode(swarthy, EXPLODE_FACTOR) if explode else swath
    if data.dtype != np.float32:
        data = data.astype(np.float32)

    return data


def _layer_at_pressure(h5v, plev=None, p=None, dex=None):
    """
    extract a layer of a variable assuming (layer, rows, cols) indexing and plev lists layer pressures
    this is used to construct slicing tools that are built into the manifest list
    :param h5v: hdf5 variable object
    :param plev: pressure array corresponding to layer dimension
    :param p: pressure level value to find
    :return: data slice from h5v
    """
    # dex = np.searchsorted(plev, p)
    if dex is None:
        dex = np.abs(plev - p).argmin()

        try:
            LOG.debug('using level %d=%f near %r as %f' % (dex, plev[dex], plev[dex-1:dex+2], p))
        except IndexError:
            pass
    return h5v[dex, :]


def _write_var_to_binary_file(filename, h5_files, var_name, pressure=None):
    if pressure is not None:
        plev = h5_files[0]["Plevs"][:].squeeze()
        dex = np.abs(plev - pressure).argmin()   # FUTURE: memo-ize this value since it shouldn't vary for DR-RTV files
        LOG.debug('using level %d=%f near %r as %f' % (dex, plev[dex], plev[dex-1:dex+2], pressure))
        tool = partial(_layer_at_pressure, dex=dex)
    else:
        tool = None
    data = _get_whole_var(h5_files, var_name, tool)

    if len(data.shape) != 2:
        LOG.warning('data %r shape is %r, ignoring' % (filename, data.shape))
        return None
    if hasattr(data, 'mask'):
        mask = data.mask
        LOG.debug('found mask for %s' % filename)
        data = np.array(data, dtype=np.float32)
        data[mask] = np.nan
    LOG.debug('writing to %s...' % filename)
    with file(filename, 'wb') as fp:
        data.tofile(fp)
    return data.shape


PRODUCT_CAPE = "CAPE"
PRODUCT_CO2_AMOUNT = "CO2_Amount"
PRODUCT_COT = "COT"
PRODUCT_CTP = "CTP"
PRODUCT_CTT = "CTT"
PRODUCT_CLOUD_EMISSIVITY = "CldEmis"
PRODUCT_CMASK = "Cmask"
PRODUCT_LI = "Lifted_Index"
PRODUCT_SURFPRES = "SurfPres"
PRODUCT_TSURF = "TSurf"
PRODUCT_TOT_WATER = "totH2O"
PRODUCT_TOT_OZONE = "totO3"
# Handle products with multiple levels later on when creating the product definitions
PRODUCT_DEWPOINT = "Dewpnt"
PRODUCT_WATER_MMR = "H2OMMR"
PRODUCT_OZONE_VMR = "O3VMR"
PRODUCT_RELHUM = "RelHum"
PRODUCT_TAIR = "TAir"
# geo products
# This assumes that we will never process more than one instrument at a time
PRODUCT_LON = "Longitude"
PRODUCT_LAT = "Latitude"

GEO_PAIRS = GeoPairDict()
BASE_PAIR = "drrtv_nav"
GEO_PAIRS.add_pair(BASE_PAIR, PRODUCT_LON, PRODUCT_LAT)

PRODUCTS = ProductDict()
FT_DRRTV = "file_type_drrtv"
# file keys are not specified here, they are determined above in another table (from previous version of this frontend)
PRODUCTS.add_product(PRODUCT_CAPE, BASE_PAIR, "CAPE", FT_DRRTV, "CAPE")
PRODUCTS.add_product(PRODUCT_CO2_AMOUNT, BASE_PAIR, "co2_amount", FT_DRRTV, "CO2_Amount")
PRODUCTS.add_product(PRODUCT_COT, BASE_PAIR, "cloud_optical_thickness", FT_DRRTV, "COT")
PRODUCTS.add_product(PRODUCT_CTP, BASE_PAIR, "cloud_top_pressure", FT_DRRTV, "CTP")
PRODUCTS.add_product(PRODUCT_CTT, BASE_PAIR, "cloud_top_temperature", FT_DRRTV, "CTT")
PRODUCTS.add_product(PRODUCT_CLOUD_EMISSIVITY, BASE_PAIR, "cloud_emissivity", FT_DRRTV, "CldEmis")
PRODUCTS.add_product(PRODUCT_CMASK, BASE_PAIR, "category", FT_DRRTV, "Cmask")
PRODUCTS.add_product(PRODUCT_LI, BASE_PAIR, "lifted_index", FT_DRRTV, "Lifted_Index")
PRODUCTS.add_product(PRODUCT_SURFPRES, BASE_PAIR, "surface_pressure", FT_DRRTV, "SurfPres")
PRODUCTS.add_product(PRODUCT_TSURF, BASE_PAIR, "surface_temperature", FT_DRRTV, "TSurf")
PRODUCTS.add_product(PRODUCT_TOT_WATER, BASE_PAIR, "total_water", FT_DRRTV, "totH2O")
PRODUCTS.add_product(PRODUCT_TOT_OZONE, BASE_PAIR, "total_ozone", FT_DRRTV, "totO3")
# geo products
PRODUCTS.add_product(PRODUCT_LON, BASE_PAIR, "longitude", FT_DRRTV, "Longitude")
PRODUCTS.add_product(PRODUCT_LAT, BASE_PAIR, "latitude", FT_DRRTV, "Latitude")
TAIR_PRODUCTS = []
DEWPOINT_PRODUCTS = []
WATER_MMR_PRODUCTS = []
OZONE_VMR_PRODUCTS = []
RELHUM_PRODUCTS = []
# All levels
all_lvl_ranges = [
    0.005, 0.0161, 0.0384, 0.0769, 0.137, 0.2244, 0.3454, 0.5064, 0.714,
    0.9753, 1.2972, 1.6872, 2.1526, 2.7009, 3.3398, 4.077, 4.9204,
    5.8776, 6.9567, 8.1655, 9.5119, 11.0038, 12.6492, 14.4559, 16.4318,
    18.5847, 20.9224, 23.4526, 26.1829, 29.121, 32.2744, 35.6505,
    39.2566, 43.1001, 47.1882, 51.5278, 56.126, 60.9895, 66.1253,
    71.5398, 77.2396, 83.231, 89.5204, 96.1138, 103.017, 110.237,
    117.777, 125.646, 133.846, 142.385, 151.266, 160.496, 170.078,
    180.018, 190.32, 200.989, 212.028, 223.441, 235.234, 247.408,
    259.969, 272.919, 286.262, 300, 314.137, 328.675, 343.618, 358.966,
    374.724, 390.893, 407.474, 424.47, 441.882, 459.712, 477.961,
    496.63, 515.72, 535.232, 555.167, 575.525, 596.306, 617.511, 639.14,
    661.192, 683.667, 706.565, 729.886, 753.628, 777.79, 802.371,
    827.371, 852.788, 878.62, 904.866, 931.524, 958.591, 986.067,
    1013.95, 1042.23, 1070.92, 1100
]
# Index 45 to 97
#lvl_range = all_lvl_ranges[45:98]
# Every 100
#lvl_range = [100, 200, 300, 400, 500, 600, 700, 800]
# lvl_range = all_lvl_ranges

def _add_level_based_products(lvl_range):
    for lvl_num in lvl_range:
        if lvl_num < 5.0:
            # Rounding doesn't work when there are multiple pressure levels per integer
            suffix = "_%0.03fmb" % (lvl_num,)
        else:
            suffix = "_%dmb" % (lvl_num,)

        PRODUCTS.add_product(PRODUCT_TAIR + suffix, BASE_PAIR, "air_temperature", FT_DRRTV, "TAir", pressure=lvl_num)
        PRODUCTS.add_product(PRODUCT_DEWPOINT + suffix, BASE_PAIR, "dewpoint_temperature", FT_DRRTV, "Dewpnt", pressure=lvl_num)
        PRODUCTS.add_product(PRODUCT_WATER_MMR + suffix, BASE_PAIR, "mixing_ratio", FT_DRRTV, "H2OMMR", pressure=lvl_num)
        PRODUCTS.add_product(PRODUCT_OZONE_VMR + suffix, BASE_PAIR, "mixing_ratio", FT_DRRTV, "O3VMR", pressure=lvl_num)
        PRODUCTS.add_product(PRODUCT_RELHUM + suffix, BASE_PAIR, "relative_humidity", FT_DRRTV, "RelHum", pressure=lvl_num)
        TAIR_PRODUCTS.append(PRODUCT_TAIR + suffix)
        DEWPOINT_PRODUCTS.append(PRODUCT_DEWPOINT + suffix)
        WATER_MMR_PRODUCTS.append(PRODUCT_WATER_MMR + suffix)
        OZONE_VMR_PRODUCTS.append(PRODUCT_OZONE_VMR + suffix)
        RELHUM_PRODUCTS.append(PRODUCT_RELHUM + suffix)


class Frontend(FrontendRole):
    FILE_EXTENSIONS = (".h5",)

    def __init__(self, level_index_range=(45, 98), **kwargs):
        _add_level_based_products(all_lvl_ranges[level_index_range[0]: level_index_range[1]])
        super(Frontend, self).__init__(**kwargs)
        self._load_files(self.find_files_with_extensions())

    def _load_files(self, file_paths):
        file_infos = []
        this_inst = None
        for fp in file_paths:
            file_info = _filename_info(fp)
            if not file_info:
                LOG.debug("Unrecognized file: %s", fp)
                continue
            if this_inst is None:
                this_inst = (file_info["sat"], file_info["instrument"])
            elif (file_info["sat"], file_info["instrument"]) != this_inst:
                LOG.error("More than one satellite/instrument's files found, can only process one at a time")
                raise ValueError("More than one satellite/instrument's files found, can only process one at a time")
            file_info["h5"] = h5py.File(fp, 'r')
            file_infos.append(file_info)
        file_infos.sort(key=lambda x: x["begin_time"])
        self._begin_time = file_infos[0]["begin_time"]
        # NOTE: this is technically not correct
        self._end_time = file_infos[-1]["begin_time"]
        self.rows_per_scan = file_infos[0]["rows_per_scan"]
        self.satellite = file_infos[0]["sat"]
        self.instrument = file_infos[0]["instrument"]
        self.file_objects = [x.pop("h5") for x in file_infos]
        self.filepaths = [x.pop("filepath") for x in file_infos]

    @property
    def begin_time(self):
        return self._begin_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def available_product_names(self):
        # as far as I know if you have any kind of DR-RTV file you should have all of the products available
        return PRODUCTS.keys()

    @property
    def default_products(self):
        not_defaults = [PRODUCT_CMASK, PRODUCT_LON, PRODUCT_LAT]
        defaults = [p for p in self.all_product_names if p not in not_defaults]
        return defaults

    @property
    def all_product_names(self):
        return PRODUCTS.keys()

    def create_raw_swath_object(self, product_name, swath_definition):
        product_def = PRODUCTS[product_name]
        # file_type = PRODUCTS.file_type_for_product(product_name, use_terrain_corrected=self.use_terrain_corrected)
        # file_key = PRODUCTS.file_key_for_product(product_name, use_terrain_corrected=self.use_terrain_corrected)
        # simple version
        file_key = product_def.file_key
        pressure = getattr(product_def, "pressure", None)
        LOG.debug("Getting file key '%s' for product '%s'", file_key, product_name)

        LOG.debug("Writing product '%s' data to binary file", product_name)
        filename = product_name + ".dat"
        if os.path.isfile(filename):
            if not self.overwrite_existing:
                LOG.error("Binary file already exists: %s" % (filename,))
                raise RuntimeError("Binary file already exists: %s" % (filename,))
            else:
                LOG.warning("Binary file already exists, will overwrite: %s", filename)

        try:
            filename = product_name + ".dat"
            shape = _write_var_to_binary_file(filename, self.file_objects, file_key, pressure=pressure)
            rows_per_scan = self.rows_per_scan
        except StandardError:
            LOG.error("Could not extract data from file")
            LOG.debug("Extraction exception: ", exc_info=True)
            raise

        one_swath = containers.SwathProduct(
            product_name=product_name, description=product_def.description, units=product_def.units,
            satellite=self.satellite, instrument=self.instrument,
            begin_time=self.begin_time, end_time=self.end_time,
            swath_definition=swath_definition, fill_value=np.nan,
            swath_rows=shape[0], swath_columns=shape[1], data_type=np.float32, swath_data=filename,
            source_filenames=self.filepaths, data_kind=product_def.data_kind, rows_per_scan=rows_per_scan
        )
        return one_swath

    def create_swath_definition(self, lon_product, lat_product):
        product_def = PRODUCTS[lon_product["product_name"]]

        # sanity check
        for k in ["data_type", "swath_rows", "swath_columns", "rows_per_scan", "fill_value"]:
            if lon_product[k] != lat_product[k]:
                if k == "fill_value" and np.isnan(lon_product[k]) and np.isnan(lat_product[k]):
                    # NaN special case: NaNs can't be compared normally
                    continue
                LOG.error("Longitude and latitude products do not have equal attributes: %s", k)
                raise RuntimeError("Longitude and latitude products do not have equal attributes: %s" % (k,))

        swath_name = GEO_PAIRS[product_def.geo_pair_name].name
        swath_definition = containers.SwathDefinition(
            swath_name=swath_name, longitude=lon_product["swath_data"], latitude=lat_product["swath_data"],
            data_type=lon_product["data_type"], swath_rows=lon_product["swath_rows"],
            swath_columns=lon_product["swath_columns"], rows_per_scan=lon_product["rows_per_scan"],
            source_filenames=self.filepaths,
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

    def create_scene(self, products=None, **kwargs):
        LOG.debug("Loading scene data...")
        # If the user didn't provide the products they want, figure out which ones we can create
        if products is None:
            LOG.debug("No products specified to frontend, will try to load logical defaults products")
            products = self.default_products

        # Do we actually have all of the files needed to create the requested products?
        products = self.loadable_products(products)

        # Needs to be ordered (least-depended product -> most-depended product)
        products_needed = PRODUCTS.dependency_ordered_products(products)
        # all of our current products are raw (other frontends have secondary products, but not us)
        raw_products_needed = products_needed

        # final scene object we'll be providing to the caller
        scene = containers.SwathScene()
        # Dictionary of all products created so far (local variable so we don't hold on to any product objects)
        products_created = {}

        # Load geolocation files
        # normally there are multiple resolutions provided by a frontend, but we only need one
        # swath_definitions = {}
        geo_pair_name = BASE_PAIR
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
        # swath_definitions[swath_def["swath_name"]] = swath_def

        # Create each raw products (products that are loaded directly from the file)
        for product_name in raw_products_needed:
            if product_name in products_created:
                # already created
                continue

            try:
                LOG.info("Creating data product '%s'", product_name)
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
    from polar2grid.core.script_utils import ExtendAction, ExtendConstAction
    # Set defaults for other components that may be used in polar2grid processing
    # remapping microwave data with EWA doesn't look very good, so default to nearest neighbor
    parser.set_defaults(fornav_D=40, fornav_d=1, share_remap_mask=False, remap_method="nearest")

    # Use the append_const action to handle adding products to the list
    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                       help="List available frontend products and exit")
    group.add_argument("--level-index-range", nargs=2, type=int, default=(45, 98),
                       help="Start(inclusive) and end(exclusive) index for level ranges to make available (0 -1 for all)")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    group.add_argument("-p", "--products", dest="products", nargs="+", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    group.add_argument('--tair-products', dest='products', action=ExtendConstAction, const=TAIR_PRODUCTS,
                       help="Add all TAir products to the list of products to create")
    group.add_argument('--dewpoint-products', dest='products', action=ExtendConstAction, const=DEWPOINT_PRODUCTS,
                       help="Add all dewpoint products to the list of products to create")
    group.add_argument('--water-mmr-products', dest='products', action=ExtendConstAction, const=WATER_MMR_PRODUCTS,
                       help="Add all Water MMR products to the list of products to create")
    group.add_argument('--ozone-vmr-products', dest='products', action=ExtendConstAction, const=OZONE_VMR_PRODUCTS,
                       help="Add all Ozone VMR products to the list of products to create")
    group.add_argument('--relhum-products', dest='products', action=ExtendConstAction, const=RELHUM_PRODUCTS,
                       help="Add all relative humidity products to the list of products to create")
    return ["Frontend Initialization", "Frontend Swath Extraction"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    parser = create_basic_parser(description="Extract DR-RTV swath data into binary files")
    subgroup_titles = add_frontend_argument_groups(parser)
    parser.add_argument('-f', dest='data_files', nargs="+", default=[],
                        help="List of data files or directories to extract data from")
    parser.add_argument('-o', dest="output_filename", default=None,
                        help="Output filename for JSON scene (default is to stdout)")
    parser.add_argument("-t", "--test", dest="run_test", default=None,
                        help="Run specified test [test_write, test_write_tags, etc]")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(subgroup_titles=subgroup_titles, global_keywords=global_keywords)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)
    LOG.debug("Starting script with arguments: %s", " ".join(sys.argv))

    if args.self_test:
        import doctest
        doctest.testmod()
        sys.exit(2)

    list_products = args.subgroup_args["Frontend Initialization"].pop("list_products")
    f = Frontend(search_paths=args.data_files, **args.subgroup_args["Frontend Initialization"])

    if list_products:
        print("\n".join(sorted(f.available_product_names)))
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
