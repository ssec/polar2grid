#!/usr/bin/env python
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
"""Utilities for handling legacy behavior with Satpy interfaces."""

from __future__ import annotations

import logging

import argparse
from typing import Union, Iterable, Generator, Optional
from satpy import Scene, DataID, DataQuery

logger = logging.getLogger(__name__)


def convert_old_p2g_date_frmts(frmt):
    """Convert old P2G output pattern date formats."""
    dt_frmts = {
        "_YYYYMMDD": ":%Y%m%d",
        "_YYMMDD": ":%y%m%d",
        "_HHMMSS": ":%H%M%S",
        "_HHMM": ":%H%M",
    }

    for old_frmt, new_frmt in dt_frmts.items():
        old_start = "start_time{}".format(old_frmt)
        new_start = "start_time{}".format(new_frmt)
        frmt = frmt.replace(old_start, new_start)

        old_begin = "begin_time{}".format(old_frmt)
        frmt = frmt.replace(old_begin, new_start)

        old_end = "end_time{}".format(old_frmt)
        new_end = "end_time{}".format(new_frmt)
        frmt = frmt.replace(old_end, new_end)

    return frmt


def output_pattern_parser_error(value):
    raise DeprecationWarning("--output-pattern is deprecated, use --output-filename")


def convert_p2g_pattern_to_satpy(pattern):
    """Convert old P2G output patterns to new format."""

    replacements = {
        "satellite": "platform_name",
        "instrument": "sensor",
        "begin_time": "start_time",
        "product_name": "p2g_name",
    }
    for p2g_kw, satpy_kw in replacements.items():
        pattern = pattern.replace(p2g_kw, satpy_kw)
    pattern = convert_old_p2g_date_frmts(pattern)

    return pattern


class AliasHandler:
    """Utility class for converting internal Satpy names to user-facing Polar2Grid names.

    Polar2Grid and Geo2Grid currently only allows users to specify the name of
    products to load as a string. For compatibility with older versions of
    Polar2Grid or for basic aesthetic differences, Polar2Grid sometimes has
    different names for products. There are also cases where Polar2Grid needs
    to provide a single name for a more complex Satpy product that normally
    requires a `DataID`.

    This class provides the ability to convert between these different forms
    of naming. If a user provides a Satpy name then this class will **not**
    replace it with a P2G alias (if it exists). This should lead to the least
    amount of surprises for users.

    """

    def __init__(
        self,
        all_aliases: dict[str, Union[str, DataQuery]],
        user_products: list[str],
    ):

        self._all_aliases = all_aliases
        self._user_products = user_products

    def remove_unknown_user_products(
        self,
        known_dataset_names: Iterable[str],
    ) -> list[str]:
        """Remove user products that aren't known to the Scene.

        This is for a Satpy reader that dynamically determines what datasets
        it knows about based on what is in the files it is provided. If the
        user (or more likely a P2G reader's default products) asks for a
        product that isn't known, we need to remove it so Satpy doesn't error
        out. For example, the MiRS reader doesn't know what BT bands are known
        until it knows what files are being read. Polar2Grid needs to default
        to all possible BT bands or else we can't load specific BT bands.

        """
        satpy_names = self.convert_p2g_name_to_satpy(self._user_products)
        new_user_products = []
        for user_name, satpy_name in zip(self._user_products, satpy_names):
            # convert DataID/DataQuery to string
            satpy_name = satpy_name if isinstance(satpy_name, str) else satpy_name["name"]
            if satpy_name not in known_dataset_names:
                continue
            new_user_products.append(user_name)
        self._user_products = new_user_products
        return new_user_products

    @property
    def satpy_ids(self):
        """All user provided product names as Satpy identifiers."""
        return list(self.convert_p2g_name_to_satpy())

    def convert_p2g_name_to_satpy(
        self,
        products: Optional[Iterable[str]] = None,
    ) -> Generator[Union[str, DataID], None, None]:
        """Convert P2G names to corresponding Satpy name or DataID."""
        if products is None:
            products = self._user_products
        for product_name in products:
            yield self._all_aliases.get(product_name, product_name)

    def convert_satpy_to_p2g_name(
        self,
        satpy_products: Iterable[Union[DataID]],
        possible_p2g_names: Optional[list[str]] = None,
    ):
        """Get the P2G name for a series of Satpy names or DataIDs.

        If a Satpy DataID does not have a Polar2Grid compatible name then
        ``None`` is yielded. A name is not compatible if requesting it would
        produce a different product than the original DataID.

        """
        from satpy import DatasetDict

        if possible_p2g_names is None:
            possible_p2g_names = self._user_products
        satpy_id_dict = DatasetDict({x: x for x in satpy_products})
        satpy_id_to_p2g_name = {}
        for p2g_name in possible_p2g_names:
            satpy_data_query = self._all_aliases.get(p2g_name, p2g_name)
            try:
                matching_satpy_id = satpy_id_dict[satpy_data_query]
            except KeyError:
                continue

            if matching_satpy_id in satpy_id_to_p2g_name:
                logger.warning("Multiple product names map to the same identifier in Satpy")
                print(matching_satpy_id, satpy_id_to_p2g_name[matching_satpy_id], p2g_name)
            satpy_id_to_p2g_name[matching_satpy_id] = p2g_name

        for satpy_product in satpy_products:
            satpy_id_name = satpy_product["name"]
            satpy_id_as_p2g_name = satpy_id_to_p2g_name.get(satpy_product)
            satpy_name_is_p2g_name = satpy_id_name in possible_p2g_names
            satpy_name_does_not_round_trip = satpy_id_dict[satpy_product] != satpy_product
            if satpy_id_as_p2g_name is None:
                # We can't yield this name if it is also a P2G name or if
                # asking Satpy for the name doesn't return the same DataID
                # product. Otherwise users would ask for X and not get X.
                if satpy_name_is_p2g_name or satpy_name_does_not_round_trip:
                    yield None
                else:
                    yield satpy_id_name
                continue

            yield satpy_id_to_p2g_name.get(satpy_product, satpy_id_name)

    def apply_p2g_name_to_scene(
        self,
        scn: Scene,
    ):
        """Assign a new 'p2g_name' string attribute to every DataArray.

        This is typically done just before writing the 'Scene' output to disk so
        that the `filename` pattern used in `Scene.save_datasets` has access to
        the user-facing "P2G name" rather than the internal Satpy name or DataID.

        """
        all_ids = list(scn.keys())
        all_p2g_names = list(self.convert_satpy_to_p2g_name(all_ids))
        for data_id, p2g_name in zip(all_ids, all_p2g_names):
            if p2g_name is None:
                # the Satpy ID doesn't have a Polar2Grid compatible name
                logger.debug("Satpy DataID %s does not have a compatible polar2grid name.", data_id)
                continue
            scn[data_id].attrs["p2g_name"] = p2g_name
            logger.debug("Mapping Satpy ID to P2G name: %s -> %s", data_id, p2g_name)

    def available_product_names(
        self, all_p2g_products: list[str], available_satpy_ids: list[DataID]
    ) -> tuple[list[str], list[str]]:
        """Get separate lists of available Satpy products and Polar2Grid products."""
        available_ids_as_p2g_names = list(self.convert_satpy_to_p2g_name(available_satpy_ids, all_p2g_products))
        satpy_id_to_p2g_name = dict(zip(available_satpy_ids, available_ids_as_p2g_names))
        available_p2g_names = []
        available_satpy_names = []
        for satpy_id in available_satpy_ids:
            p2g_name = satpy_id_to_p2g_name[satpy_id]
            if p2g_name is None:
                # no Polar2Grid compatible name
                continue
            if p2g_name in all_p2g_products:
                available_p2g_names.append(p2g_name)
            else:
                available_satpy_names.append(satpy_id["name"])

        available_satpy_names = sorted(set(available_satpy_names))
        return available_satpy_names, available_p2g_names
