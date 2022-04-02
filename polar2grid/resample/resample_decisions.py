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
"""Decision utilties for resampling."""

import logging
import os

import yaml
from pyresample.geometry import SwathDefinition
from satpy._config import config_search_paths
from satpy.utils import recursive_dict_update
from satpy.writers import DecisionTree

logger = logging.getLogger(__name__)


class ResamplerDecisionTree(DecisionTree):
    """Helper class to determine resampler algorithm and other options."""

    def __init__(self, *decision_dicts, **kwargs):
        """Init the decision tree."""
        match_keys = kwargs.pop(
            "match_keys",
            (
                "name",
                "platform_name",
                "sensor",
                "standard_name",
                "area_type",
                "reader",
                "units",
            ),
        )
        self.prefix = kwargs.pop("config_section", "resampling")
        multival_keys = kwargs.pop("multival_keys", ["sensor"])
        super(ResamplerDecisionTree, self).__init__(decision_dicts, match_keys, multival_keys)

    @classmethod
    def from_configs(cls, config_filename="resampling.yaml"):
        config_paths = config_search_paths(config_filename)
        return cls(*config_paths)

    def add_config_to_tree(self, *config_files):
        """Add configuration to tree."""
        conf = {}
        for config_file in config_files:
            if os.path.isfile(config_file):
                with open(config_file) as fd:
                    resample_config = yaml.load(fd, Loader=yaml.UnsafeLoader)
                    if resample_config is None:
                        # empty file
                        continue
                    resampling_section = resample_config.get(self.prefix, {})
                    if not resampling_section:
                        logging.debug("Config '{}' has no '{}' section or it is empty".format(config_file, self.prefix))
                        continue
                    conf = recursive_dict_update(conf, resampling_section)
            elif isinstance(config_file, dict):
                conf = recursive_dict_update(conf, config_file)
            else:
                logger.debug("Loading resampling config string")
                d = yaml.load(config_file, Loader=yaml.UnsafeLoader)
                if not isinstance(d, dict):
                    raise ValueError("YAML file doesn't exist or string is not YAML dict: {}".format(config_file))
                conf = recursive_dict_update(conf, d)
        self._build_tree(conf)

    def find_match(self, **query_dict):
        """Find a match."""
        query_dict["area_type"] = "swath" if isinstance(query_dict["area"], SwathDefinition) else "area"

        try:
            return super().find_match(**query_dict)
        except KeyError:
            # give a more understandable error message
            raise KeyError(f"No resampling configuration found for {query_dict['area_type']=} | {query_dict['name']=}")
