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
"""Utilities for dynamically imported and accessing components."""

import importlib
from typing import Any


def _get_component_attr(component_type: str, component_name: str, attr_name: str, default: Any = None) -> Any:
    try:
        comp_mod = importlib.import_module(f"polar2grid.{component_type}.{component_name}")
    except ModuleNotFoundError:
        return default
    return getattr(comp_mod, attr_name, default)


def get_reader_attr(reader_name: str, attr_name: str, default: Any = None) -> Any:
    return _get_component_attr("readers", reader_name, attr_name, default=default)


def get_writer_attr(writer_name: str, attr_name: str, default: Any = None) -> Any:
    return _get_component_attr("writers", writer_name, attr_name, default=default)
