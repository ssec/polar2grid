#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2022 Space Science and Engineering Center (SSEC),
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
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
"""Helper script for generating debug AWIPS Tiled files for verifying AWIPS client behavior."""

import contextlib
import os
import sys
import tempfile
from datetime import datetime

import dask.array as da
import numpy as np
import satpy
import xarray as xr
import yaml
from pyresample import create_area_def
from satpy import Scene

from polar2grid.utils.config import add_polar2grid_config_paths

SCALE_FACTOR = 0.25
ADD_OFFSET = 2000.0


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Create single AWIPS tile example file for debugging")
    parser.add_argument(
        "physical_element_prefix", help="Name of the product in AWIPS. No spaces or special characters allowed."
    )
    parser.add_argument(
        "--units", default="1", help="CF-compatible units. Will be converted if necessary to AWIPS-compatible units."
    )
    parser.add_argument(
        "--idtype", default="uint16", help="Numpy data type of the data created and then stored in the NetCDF file."
    )
    parser.add_argument(
        "--odtype", default="int16", help="Numpy data type of the data created and then stored in the NetCDF file."
    )
    parser.add_argument(
        "--ounsigned",
        action="store_true",
        help="Whether or not to include the special 'Unsigned' flag in the NetCDF file. No effect if odtype "
        "isn't signed.",
    )
    args = parser.parse_args()

    add_polar2grid_config_paths()

    start_time = datetime.utcnow()
    idtype_str = args.idtype
    idtype = getattr(np, idtype_str)
    odtype_str = args.odtype
    set_unsigned = args.ounsigned
    set_unsigned_str = "U" if set_unsigned else ""
    units = args.units
    physical_element = (
        args.physical_element_prefix.replace(" ", "-") + f"-{units}-{idtype_str}-{set_unsigned_str}{odtype_str}"
    )

    data = _gradient_data(dtype=idtype)
    area = create_area_def(
        "fakelcc",
        {"proj": "lcc", "lon_0": -95.0, "lat_0": 25, "lat_1": 25},
        shape=data.shape,
        resolution=(10000.0, 10000.0),
        center=(0, 0),
    )
    data_arr = xr.DataArray(
        data,
        attrs={
            "platform_name": "P2G-DEBUG",
            "sensor": "P2G-INST",
            "name": physical_element,
            "start_time": start_time,
            "units": units,
            "area": area,
            "valid_range": _valid_range_for_idtype(idtype),
        },
        dims=("y", "x"),
    )
    scn = Scene()
    scn[physical_element] = data_arr

    os.environ["ORGANIZATION"] = "P2G_DEBUG_ORG"
    with add_fake_awips_template(physical_element, odtype_str, set_unsigned):
        scn.save_datasets(
            writer="awips_tiled",
            sector_id="LCC",
            tile_count=(4, 4),
            source_name="SSEC",
        )


@contextlib.contextmanager
def add_fake_awips_template(product_name, odtype_str, set_unsigned):
    with tempfile.TemporaryDirectory(prefix="p2g_awips_debug_") as tdir:
        writers_dir = os.path.join(tdir, "writers")
        os.makedirs(writers_dir)
        yaml_filename = os.path.join(writers_dir, "awips_tiled.yaml")
        with open(yaml_filename, "w") as yaml_file:
            var_config = {
                "name": product_name,
                "var_name": "data",
                "attributes": {
                    "physical_element": {"value": "{name}"},
                    "units": {},
                },
                "encoding": {
                    "dtype": odtype_str,
                    # "scale_factor": SCALE_FACTOR,
                    # "add_offset": ADD_OFFSET,
                    # "_FillValue": 10,
                },
            }
            if set_unsigned:
                var_config["encoding"]["_Unsigned"] = "true"
            yaml.dump(
                {
                    "templates": {
                        "polar": {
                            "variables": {
                                "my_fake_var": var_config,
                            },
                        },
                    },
                },
                yaml_file,
            )

        with satpy.config.set(config_path=[tdir] + satpy.config.get("config_path")):
            yield


def _valid_range_for_idtype(dtype):
    min_val = np.iinfo(dtype).min
    max_val = np.iinfo(dtype).max
    return [min_val, max_val]


def _gradient_data(dtype):
    num_rows = 300
    num_cols = 100
    min_val, max_val = _valid_range_for_idtype(dtype)
    unscaled_min = min_val * SCALE_FACTOR + ADD_OFFSET
    unscaled_max = max_val * SCALE_FACTOR + ADD_OFFSET
    data = np.repeat(np.linspace(unscaled_min, unscaled_max, num_cols)[np.newaxis, :], num_rows, axis=0)
    half_row = num_rows // 2
    half_col = num_cols // 2
    data[half_row - 5 : half_row + 5, half_col - 5 : half_col + 5] = np.nan
    return da.from_array(data)


if __name__ == "__main__":
    sys.exit(main())
