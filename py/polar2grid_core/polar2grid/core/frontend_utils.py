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
# Written by David Hoese    November 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Helper functions and classes for handling common polar2grid frontend problems.

TODO: Add basic frontend and boiler plate documentation here.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2014
:license:      GNU GPLv3

"""

from polar2grid.core.fbf import FileAppender
import numpy

import os
import logging

LOG = logging.getLogger(__name__)


class ProductDefinition(object):
    """Product definition for polar2grid frontends

    A product can fall in to one or more categories:

        - raw: Raw swath data straight from a file. Raw products may require simple scaling. If a raw product
               requires extra processing (filtering, masking, etc) then a dependency of `None` should be specified.
        - geo: Geolocation data straight from a file. All geo products are raw products and as such may require
               additional processing (dependency of `None`) for extra filtering, masking, or interpolation.
        - secondary: Product created from one or more raw products.

    Product definitions have the following parameters:

        :param name: Unique name of the product. Product names can not be shared between products of the same frontend.
        :param geo_pair_name: Name of the geolocation pair (see `GeoPair` and `GeoPairDict` for more information). If
                              multiple resolutions are possible (see 'file_type') then this value may be a tuple
                              of the different geo pairs for each 'file_type'.
        :param data_kind: Type of data the product represents (brightness_temperature, radiance,
                          sea_surface_temperature, etc). All 'geo' products should have a 'data_kind' of either
                          ``longitude`` or ``latitude``.
        :param file_type: Name of the type of file that this product's data comes from. This
                          is specific to the frontend being used. If a product could come from more than one file then
                          a tuple can be provided as 'file_type' and the `get_file_type` method can be used to get
                          the correct 'file_type' for the available files. Due to this 'file_type' sorting for
                          'geo_pair_name' and 'file_key' then some secondary products may specify 'file_type' for
                          sorting purposes, otherwise `None`.
        :param file_key: Name of the key representing how to get this product's data from the file (raw and geo products
                         only). This is specific to the frontend being used and usually mapped to a specific file
                         variable name somewhere in the frontend. If the 'file_key' used is dependent on the 'file_type'
                         available then a tuple matching the 'file_type' tuple may be used. The `get_file_key`
                         method should be used in either case.
        :param dependencies: List of products name this product depends on. Usually only used for secondary products,
                             but raw and geo products may have dependencies of ``[None]`` to indicate they require
                             further processing.
        :param description: String description of the product (optional)
        :param units: String units of the data ("kelvin", "mm/hr" , etc)

    All single word string parameters should be lowercase including `name` and `units`.

    Product definitions are usually created via the `ProductDict.add_product` method.
    """
    GEO_DATA_KINDS = ["longitude", "latitude"]

    def __init__(self, name, geo_pair_name, data_kind, file_type=None, file_key=None,
                 dependencies=None, description=None, units=None, **kwargs):
        self.name = name
        self.geo_pair_name = geo_pair_name
        self.data_kind = data_kind
        self.file_type = file_type
        self.file_key = file_key
        self.dependencies = dependencies or []
        self.description = description or ""
        self.units = units or ""
        self.dependents = []

        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def is_raw(self):
        return self.file_key is not None

    @property
    def is_geo(self):
        return self.data_kind in self.GEO_DATA_KINDS

    @property
    def is_secondary(self):
        return self.dependencies and self.dependencies[0] is not None

    @property
    def needs_processing(self):
        """This product is either a secondary/dependent product or a raw product needing further processing.
        """
        return bool(self.dependencies)

    def get_geo_pair_name(self, available_file_types):
        """Return the geo pair name that should be used for this product.

        See the class documentation for `ProductDefinition` for more information.

        :param available_file_types: file types available to the frontend
        """
        if not isinstance(self.geo_pair_name, (tuple, list)):
            return self.geo_pair_name

        if isinstance(self.file_type, (tuple, list)):
            for ft, gp in zip(self.file_type, self.geo_pair_name):
                if ft in available_file_types:
                    return gp
            else:
                raise RuntimeError("No usable file types found for product '%s'", self.name)

        LOG.warning("Multiple geo pair names specified for product '%s', but only one file type", self.name)
        return self.geo_pair_name[0]

    def get_file_type(self, available_file_types):
        """Return the file type that should be used for this product.

        See the class documentation for `ProductDefinition` for more information.

        :param available_file_types: file types available to the frontend
        """
        if isinstance(self.file_type, (tuple, list)):
            for ft in self.file_type:
                if ft in available_file_types:
                    return ft
            else:
                raise RuntimeError("No usable file types found for product '%s'", self.name)
        return self.file_type

    def get_file_key(self, available_file_types):
        """Return the file key that should be used for this product.

        See the class documentation for `ProductDefinition` for more information.

        .. note::

            This does not handle multiple file keys for the same file. File type information inside the frontend should
            handle this case. Otherwise, subclassing should be used if this functionality is required.

        :param available_file_types: file types available to the frontend
        """
        if not isinstance(self.file_key, (tuple, list)):
            return self.file_key

        if isinstance(self.file_type, (tuple, list)):
            for ft, fk in zip(self.file_type, self.file_key):
                if ft in available_file_types:
                    return fk
            else:
                raise RuntimeError("No usable file types/kinds found for product '%s'", self.name)

        LOG.warning("Multiple file keys specified for product '%s', but only one file type", self.name)
        return self.file_key[0]


class GeoPair(object):
    def __init__(self, name, lon_product, lat_product, rows_per_scan=0):
        self.name = name
        self.lon_product = lon_product
        self.lat_product = lat_product
        self.rows_per_scan = rows_per_scan


class ProductDict(dict):
    def __init__(self, raw_base_class=ProductDefinition):
        self.base_class = raw_base_class
        super(ProductDict, self).__init__()

    def add_product(self, *args, **kwargs):
        pd = self.base_class(*args, **kwargs)
        for dep in pd.dependencies:
            if dep is None:
                continue
            try:
                self[dep].dependents.append(pd.name)
            except KeyError:
                raise ValueError("Product %s depends on unknown product %s" % (pd.name, dep))
        self[pd.name] = pd

    @property
    def all_raw_products(self):
        return (p for p, p_def in self.items() if p_def.is_raw)

    @property
    def all_nongeo_raw_products(self):
        return (p for p, p_def in self.items() if p_def.is_raw and not p_def.is_geo)

    @property
    def all_geo_products(self):
        return (p for p, p_def in self.items() if p_def.is_geo)

    @property
    def all_secondary_products(self):
        return (p for p, p_def in self.items() if p_def.is_secondary)

    def is_raw(self, product_name, geo_is_raw=True):
        """Product is raw or not. If `geo_is_raw` is True (default), then geoproducts are considered raw products.
        """
        p_def = self[product_name]
        return p_def.is_raw and (geo_is_raw or not p_def.is_geo)

    def is_geo(self, product_name):
        return self[product_name].is_geo

    def needs_processing(self, product_name):
        """Does this product require additional processing beyond being loaded (and scaled) from the data files.

        This includes "secondary" products and raw products that require extra masking.
        """
        return bool(self[product_name].dependencies)

    def geo_pairs_for_products(self, product_names, available_file_types=None):
        if available_file_types is None:
            # there is only one possible geo pair name
            return list(set(self[p].geo_pair_name for p in product_names))
        else:
            return list(set(self[p].get_geo_pair_name(available_file_types) for p in product_names))

    def get_product_dependencies(self, product_name):
        """Recursive function to get all dependencies to create a single product.

        :param product_name: Valid product name for this frontend
        :returns: Stack-like list where the last element is the most depended (duplicates possible)

        """
        #
        _dependencies = []

        if product_name not in self:
            LOG.error("Requested information for unknown product: '%s'" % (product_name,))
            raise ValueError("Requested information for unknown product: '%s'" % (product_name,))

        for dependency_product in self[product_name].dependencies:
            if dependency_product is None:
                LOG.debug("Product Dependency: Additional processing will be required for product '%s'", product_name)
                continue

            LOG.info("Product Dependency: To create '%s', '%s' must be created first", product_name, dependency_product)
            _dependencies.append(dependency_product)
            _dependencies.extend(self.get_product_dependencies(dependency_product))

        # Check if the product_name is already in the set, if it is then we have a circular dependency
        if product_name in _dependencies:
            LOG.error("Circular dependency found in frontend, '%s' requires itself", product_name)
            raise RuntimeError("Circular dependency found in frontend, '%s' requires itself", product_name)

        return _dependencies

    def get_product_dependents(self, starting_products):
        """Recursively determine what products (secondary) can be made from the products provided.
        """
        # FUTURE: Make this non-recursive since that takes longer (could even be list comprehension)
        def _these_dependents(pname):
            my_dependents = set(self[pname].dependents)
            for p in self[pname].dependents:
                my_dependents |= _these_dependents(p)
            return my_dependents

        possible_products = set(starting_products[:])
        for product_name in starting_products:
            possible_products |= _these_dependents(product_name)

        return possible_products

    def dependency_ordered_products(self, product_names):
        """Returns ordered list from most independent to least independent product names.
        """
        products_needed = []
        # Check what products they asked for and see what we need to be able to create them
        for product_name in product_names:
            LOG.debug("Searching for dependencies for '%s'", product_name)
            if product_name in products_needed:
                # put in least-depended product -> most-depended product order
                products_needed.remove(product_name)
            products_needed.append(product_name)

            other_deps = self.get_product_dependencies(product_name)
            # only add products that aren't already account for
            for dep in other_deps:
                if dep in products_needed:
                    # put in least-depended product -> most-depended product order
                    products_needed.remove(dep)
                products_needed.append(dep)

        return products_needed


class GeoPairDict(dict):
    def __init__(self, base_class=GeoPair):
        self.base_class = base_class
        super(GeoPairDict, self).__init__()

    def add_pair(self, *args, **kwargs):
        gp = self.base_class(*args, **kwargs)
        self[gp.name] = gp

    def geoproducts_for_pairs(self, *pair_names):
        product_names = []
        for p in pair_names:
            product_names.append(self[p].lon_product)
            product_names.append(self[p].lat_product)
        return product_names


class BaseFileReader(object):
    """Base class for a basic file object wrapper.

    The file reader uses a dictionary `file_type_info` to map common key names to complex variable or attribute names
    and how to get them.

    This file reader must be subclassed and the following attributes are recommended unless otherwise stated:

        :attr begin_time: Datetime object for the first time represented in the file (required for proper sorting)
        :attr end_time: Datetime object for the last time represented in the file
        :attr instrument: Instrument that made the observations in this file
        :attr satellite: Satellite where the instrument is located

    """
    begin_time = None

    def __init__(self, file_handle, file_type_info):
        """Initialize the file reader with a file object (usually a wrapper around an HDF5 or NetCDF file).

        A common case is to provide the file object after deciding what "File Type" it belongs to and a dictionary
        mapping common key names (constants) and objects describing how to get that data out of the file. For example,
        given a HDF5 filepath, after opening the file it is possible to tell that the file has variables associated with
        file type "A". The subclass of `FileReader` can then be provided the file object and a dictionary of information
        we know about this file type. Now more complex and specific operations can be performed.

        :param file_handle: File wrapper implement `__getitem__` access to data and has 'filepath' and
                            'filename' attributes.
        :param file_type_info: Dictionary mapping constant strings to variable access information
        """
        self.file_handle = file_handle
        self.filepath = file_handle.filepath
        self.filename = file_handle.filename
        self.file_type_info = file_type_info

    def __getitem__(self, item):
        """Basic 'getitem' access that uses the `file_type_info` for matching keys first.

        Must be subclassed if `file_type_info` values are anything but strings to pass to the `file_handle`.
        """
        known_item = self.file_type_info.get(item, item)
        if known_item is None:
            raise KeyError("Key 'None' was not found")

        LOG.debug("Loading %s from %s", known_item, self.filename)
        return self.file_handle[known_item]

    def get_fill_value(self, item):
        """If the caller of `get_swath_data` doesn't force the output fill value then they need to know what it is now.
        Defaults version expects a 'data_type' attribute in the value returned from `file_type_info`.

            - Unsigned Integers: Highest valid integer (i.e. -1 converted to unsigned integer)
            - Signed Integers: -999
            - Float: NaN

        :raises: RuntimeError if unknown data type
        """
        var_info = self.file_type_info[item]
        if numpy.issubclass_(var_info.data_type, numpy.unsignedinteger):
            return var_info.data_type(-1)
        elif numpy.issubclass_(var_info.data_type, numpy.integer):
            return -999
        elif numpy.issubclass_(var_info.data_type, numpy.floating):
            return numpy.nan
        else:
            raise RuntimeError("Unknown data type for %s: %s" % (item, var_info.data_type))

    def get_data_type(self, item, default_dtype=numpy.float32):
        """Return the numpy data type for a specific item. This is needed if the data type isn't forced and there
        isn't direct access to the array data. Default version expects a 'data_type' attribute in the value returned
        from `file_type_info`.

        If the attribute is not found or is `None` the `default_dtype` keyword is returned.
        """
        var_info = self.file_type_info[item]
        if hasattr(var_info, "data_type"):
            return var_info.data_type or default_dtype
        return default_dtype

    def get_swath_data(self, item):
        """Retrieve the item asked for then set it to a logical data type, scale it (if needed), and mask any
        invalid data with a logical fill value (NaN or other). Most swath data in files requires extra processing so
        this method acts as a wrapper around all the "ugly" design decisions in a data file.

        :returns: numpy array for swath data specified

        """
        raise NotImplementedError("Frontend has not implemented this method yet")

    def _compare(self, other, method):
        try:
            return method(self.begin_time, other.begin_time)
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


class BaseMultiFileReader(object):
    """Base class for a file reader around multiple files.

    This class should be subclassed to provide the default `single_class` to `__init__` and any other custom
    functionality that may be required.

    The basic use of this class is as follows::

        class MultiFileReader(BaseMultiFileReader):
            def __init__(self, file_type_info):
                super(MultiFileReader, self).__init__(file_type_info, FileReader)

        file_type_A_info = {"example_var_key": "example_variable_name"}
        file_reader = MultiFileReader(file_type_A_info)
        file_handle = HDF5Reader(filepath)
        if is_file_type_A(file_handle):
            file_reader.add_file(file_handle)
        # ... and so on ...
        my_data = file_reader["example_var_key"]
        # or:
        data_shape = file_reader.write_var_to_flat_binary("example_var_key", "my_data.dat")

    """
    def __init__(self, file_type_info, single_class):
        self.file_readers = []
        self._files_finalized = False
        self.file_type_info = file_type_info
        self.single_class = single_class

    def add_file(self, fn):
        if self._files_finalized:
            LOG.error("File reader has been finalized and no more files can be added")
            raise RuntimeError("File reader has been finalized and no more files can be added")
        self.file_readers.append(self.single_class(fn, self.file_type_info))

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

    def __len__(self):
        return len(self.file_readers)

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

    def __getitem__(self, item):
        """Get multiple variables as one logical item.

        This function will try its best to concatenate arrays together. If it can't figure out what to do it will
        return a list of each file's contents.

        Current Rules:
            - If each file's item is one element, sum those elements and return the sum
        """
        try:
            # Get the data element from the file and get the actual value out of the h5py object
            individual_items = [f[item].get() for f in self.file_readers]
        except KeyError:
            LOG.error("Could not get '%s' from source files", item, exc_info=True)
            raise

        # This all assumes we are dealing with numpy arrays
        if isinstance(individual_items[0], numpy.ndarray) and len(individual_items[0]) == 1:
            # HDF5 gives us arrays with 1 element for some stuff, we don't need the array
            return numpy.array([x[0] for x in individual_items])
        else:
            return individual_items

    def get_fill_value(self, item):
        return self.file_readers[0].get_fill_value(item)

    def get_data_type(self, item):
        return self.file_readers[0].get_data_type(item)

    def write_var_to_flat_binary(self, item, filename, dtype=numpy.float32):
        """Write multiple variables to disk as one concatenated flat binary file.

        Data is written incrementally to reduce memory usage.

        :param item: Variable name to retrieve from these files
        :param filename: Filename to write to
        """
        LOG.debug("Writing binary data for '%s' to file '%s'", item, filename)
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
