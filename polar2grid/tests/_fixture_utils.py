#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2022 Space Science and Engineering Center (SSEC),
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
"""Shared utilities between fixtures."""
from __future__ import annotations

from datetime import datetime

from satpy import DatasetDict, Scene
from satpy.readers.yaml_reader import FileYAMLReader

START_TIME = datetime(2021, 1, 1, 12, 0, 0)


class _FakeReader(FileYAMLReader):
    """Fake reader to avoid loading real files during testing."""

    def __init__(self, reader_name, dataset_dict, all_dataset_ids, available_dataset_ids):
        self._name = reader_name
        self._forced_all_ids = all_dataset_ids
        self._forced_available_ids = available_dataset_ids
        self._forced_products = DatasetDict(dataset_dict)

    @property
    def start_time(self):
        return START_TIME

    @property
    def end_time(self):
        return START_TIME

    @property
    def sensor_names(self):
        return {
            "viirs_sdr": {"viirs"},
            "abi_l1b": {"abi"},
        }[self._name]

    @property
    def all_dataset_ids(self):
        return self._forced_all_ids

    @property
    def available_dataset_ids(self):
        return self._forced_available_ids

    def load(self, dataset_keys, previous_datasets=None, **kwargs):
        new_result = DatasetDict()
        for data_query in dataset_keys:
            try:
                data_arr = self._forced_products[data_query]
            except KeyError:
                continue
            data_arr.attrs.update(data_query.to_dict())
            new_result[data_query] = data_arr
        return new_result


class _TestingScene(Scene):
    """Special Scene class to mimic a real Scene that would be created during normal execution."""

    def __init__(self, *args, data_array_dict=None, all_dataset_ids=None, available_dataset_ids=None, **kwargs):
        self._forced_all_ids = all_dataset_ids
        self._forced_available_ids = available_dataset_ids
        self._forced_products = data_array_dict

        super().__init__(*args, **kwargs)

    def _create_reader_instances(self, filenames=None, reader=None, reader_kwargs=None):
        if reader is None or filenames is None or self._forced_all_ids is None or self._forced_available_ids is None:
            return {}
        return {
            reader: _FakeReader(reader, self._forced_products, self._forced_all_ids, self._forced_available_ids),
        }
