#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2021 Space Science and Engineering Center (SSEC),
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
"""Base class and other utilities for wrapping Satpy readers."""

from __future__ import annotations

import logging
from functools import cached_property
from typing import Optional, Union

from satpy import DataID, DataQuery, Scene

from polar2grid.utils.dynamic_imports import get_reader_attr
from polar2grid.utils.legacy_compat import AliasHandler

logger = logging.getLogger(__name__)


class ReaderProxyBase:
    """Helper to provide Polar2Grid-specific information about a reader.

    In the most common cases, a subclass should define the following:

    * **is_polar2grid_reader** or **is_geo2grid_reader**: If this reader
      should be used for Polar2Grid or Geo2Grid.
    * **get_default_products**: Get a list of Polar2Grid names (not Satpy
      names or DataQuery objects) that should be loaded if the user hasn't
      specified any.
    * **get_all_products**: Get all Polar2Grid names that this reader could
      possibly load. This list of products will be used by other methods to
      determine what available products for loading are custom or Satpy
      products and what products are "guaranteed" products from
      Polar2Grid/Geo2Grid.
    * **_aliases**: A property that returns a dictionary mapping Polar2Grid
      name for a product to a Satpy DataQuery or name.

    """

    is_polar2grid_reader: bool = False
    is_geo2grid_reader: bool = False

    def __init__(self, scn: Scene, user_products: list[str]):
        self.scn = scn
        self._orig_user_products = user_products

    @cached_property
    def _alias_handler(self):
        return self._create_alias_handler()

    @classmethod
    def from_reader_name(cls, reader_name: str, *args):
        reader_info_cls = get_reader_attr(reader_name, "ReaderProxy")
        if reader_info_cls is None:
            reader_info_cls = cls
        return reader_info_cls(*args)

    @property
    def _binary_name(self):
        if self.is_geo2grid_reader:
            return "geo2grid"
        return "polar2grid"

    @property
    def _aliases(self) -> dict[str, Union[DataQuery, str]]:
        return {}

    def get_default_products(self) -> list[str]:
        """Get products to load if user hasn't specified any others."""
        return []

    def get_all_products(self) -> list[str]:
        """Get all polar2grid products that could be loaded."""
        return []

    def get_available_products(
        self,
        p2g_product_names: Optional[list[str]] = None,
        possible_satpy_ids: Optional[list[DataID]] = None,
    ) -> tuple[list[str], list[str]]:
        """Get custom/satpy products and polar2grid products that are available for loading."""
        if possible_satpy_ids is None:
            possible_satpy_ids = self.scn.available_dataset_ids(composites=True)
        if p2g_product_names is None:
            p2g_product_names = self.get_all_products()
            if not p2g_product_names:
                logger.warning(
                    "Provided readers are not configured in %s. All "
                    "products will be listed with internal Satpy names.",
                    self._binary_name,
                )
                return sorted(set([x["name"] for x in possible_satpy_ids])), []
        return self._alias_handler.available_product_names(p2g_product_names, possible_satpy_ids)

    def apply_p2g_name_to_scene(
        self,
        scn: Scene,
    ):
        """Add a 'p2g_name' attribute to each DataArray in the provided Scene."""
        self._alias_handler.apply_p2g_name_to_scene(scn)

    def get_satpy_products_to_load(self) -> Optional[list[Union[DataQuery, str]]]:
        """Get Satpy product names and DataQuery objects to load."""
        no_handler = self._alias_handler is None
        no_user_products = not self._orig_user_products
        no_defaults = not self.get_default_products()
        if no_handler and no_user_products and no_defaults:
            logger.error(
                "Reader does not have a default set of products to load, "
                "please specify products to load with `--products`."
            )
            return None
        elif no_handler:
            # This shouldn't happen unless _create_alias_handler is changed
            raise RuntimeError("Converting to Satpy identifiers failed in an unexpected way.")

        products_to_load = list(self._alias_handler.convert_p2g_name_to_satpy())
        if not products_to_load and no_user_products and not no_defaults:
            msg = "Default products were not found in available file products."
            debug_msg = "Default products were not found in available file products:\n\t{}"
            debug_msg = debug_msg.format("\n\t".join(self.scn.all_dataset_names()))
            logger.error(msg)
            logger.debug(debug_msg)

        return products_to_load

    def _create_alias_handler(self, allow_empty_list=False):
        user_products = self._orig_user_products
        default_products = self.get_default_products()
        all_dataset_names = None
        use_defaults = not user_products and default_products
        if use_defaults:
            logger.info("Using default product list: {}".format(default_products))
            user_products = default_products
            all_dataset_names = self.scn.all_dataset_names(composites=True)
        elif not user_products and not allow_empty_list:
            return None

        alias_handler = AliasHandler(self._aliases, user_products)
        if all_dataset_names is not None:
            # only use defaults that actually exist for the provided files
            alias_handler.remove_unknown_user_products(all_dataset_names)
        return alias_handler
