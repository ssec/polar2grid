#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2021 Space Science and Engineering Center (SSEC),
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
"""The Binary writer writes band data to a flat binary file.

By default it enhances the data based on the enhancement configuration file
and then saves the data to a flat binary file. The output data type will match
the input data for integer types (ex. uint8 -> uint8), but floating point types
will always be forced to 32-bit floats for consistency between readers and
changes in the low-level Satpy library. A different output type can be
specified using the ``--dtype`` flag. To turn off scaling of the data (a.k.a.
enhancements) the ``--no-enhance`` command line flag can be specified to write
the "raw" band data.

"""

from __future__ import annotations

import logging

import dask.array as da
import numpy as np
import xarray as xr
from satpy.writers import ImageWriter, get_enhanced_image

from polar2grid.core.dtype import (
    NUMPY_DTYPE_STRS,
    clip_to_data_type,
    dtype_to_str,
    int_or_float,
    str_to_dtype,
)
from polar2grid.core.script_utils import NumpyDtypeList

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_FILENAMES = {
    "polar2grid": {
        None: "{platform_name!l}_{sensor!l}_{p2g_name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.dat",
    },
    "geo2grid": {
        None: "{platform_name!u}_{sensor!u}_{p2g_name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.dat",
        "abi_l1b": "{platform_name!u}_{sensor!u}_{observation_type}{scene_abbr}_"
        "{p2g_name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.dat",
        "clavrx": "{platform_name!l}_{sensor!l}_{p2g_name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.dat",
    },
}


class FlatBinaryWriter(ImageWriter):
    """Write data to disk as flat binary files."""

    def save_dataset(
        self, dataset, filename=None, fill_value=None, overlay=None, decorate=None, compute=True, **kwargs
    ):
        """Save the ``dataset`` to a given ``filename``.

        This method creates an enhanced image using :func:`get_enhanced_image`.
        The image is then passed to :meth:`save_image`. See both of these
        functions for more details on the arguments passed to this method.

        """
        img = get_enhanced_image(
            dataset.squeeze(), enhance=self.enhancer, overlay=overlay, decorate=decorate, fill_value=fill_value
        )
        kwargs["dtype"] = kwargs.get("dtype") or self._get_default_dtype(dataset)
        return self.save_image(img, filename=filename, compute=compute, fill_value=fill_value, **kwargs)

    @staticmethod
    def _get_default_dtype(data_arr: xr.DataArray) -> np.dtype:
        if data_arr.dtype == np.float64:
            return np.float32
        return data_arr.dtype

    def save_image(self, img, filename=None, compute=True, dtype=None, fill_value=None, **kwargs):
        filename = filename or self.get_filename(
            data_type=dtype_to_str(dtype), rows=img.data.shape[0], columns=img.data.shape[1], **img.data.attrs
        )

        data = self._prep_data(img.data, dtype, fill_value)

        logger.info("Saving product %s to binary file %s", img.data.attrs["p2g_name"], filename)
        dst = np.memmap(filename, shape=img.data.shape, dtype=dtype, mode="w+")
        if compute:
            da.store(data, dst)
            return
        return [[data], [dst]]

    def _prep_data(self, data: xr.DataArray, dtype: np.dtype, fill_value) -> da.Array:
        fill = data.attrs.get("_FillValue", np.nan)
        if fill_value is None:
            fill_value = fill
        final_data = data.data
        if self.enhancer and np.issubdtype(data.dtype, np.floating) and not np.issubdtype(dtype, np.floating):
            # going from float -> int and the data was enhanced
            # scale the data to fit the integer dtype
            rmin, rmax = np.iinfo(dtype).min, np.iinfo(dtype).max
            final_data = final_data * (rmax - rmin) + rmin
        final_data = clip_to_data_type(final_data, dtype)

        same_fill = np.isnan(fill) and np.isnan(fill_value) or fill == fill_value
        if data.dtype == dtype and same_fill:
            return final_data

        final_data = final_data.astype(dtype)
        if same_fill:
            return final_data

        fill_mask = np.isnan(final_data) if np.isnan(fill) else final_data == fill
        final_data = da.where(fill_mask, fill_value, final_data)
        return final_data


def add_writer_argument_groups(parser, group=None):
    if group is None:
        group = parser.add_argument_group(title="Binary Writer")

    group.add_argument(
        "--output-filename",
        dest="filename",
        help="Custom file pattern to save dataset to",
    )
    group.add_argument(
        "--dtype",
        choices=NumpyDtypeList(NUMPY_DTYPE_STRS),
        type=str_to_dtype,
        help="Data type of the output file (8-bit unsigned " "integer by default - uint8)",
    )
    group.add_argument(
        "--no-enhance",
        dest="enhance",
        action="store_false",
        help="Don't try to enhance the data before saving it",
    )
    group.add_argument(
        "--fill-value",
        dest="fill_value",
        type=int_or_float,
        help="Instead of an alpha channel fill invalid "
        "values with this value. Turns LA or RGBA "
        "images in to L or RGB images respectively.",
    )
    return group, None
