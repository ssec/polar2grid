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

from satpy.composites import SingleBandCompositor, enhance2dataset


class SingleEnhancedBandCompositor(SingleBandCompositor):
    """Produce a pre-enhanced version of the single provided dependency.

    .. warning::

        This does **NOT** stop Satpy from enhancing this dataset again. The
        metadata provided to this compositor must make the DataArray match
        another "no-op" enhancement on the backend.

    """

    def __call__(self, projectables, nonprojectables=None, **attrs):
        """Build the composite."""
        if len(projectables) != 1:
            raise ValueError("Can't have more than one band in a single-band composite")

        data = projectables[0]
        new_attrs = data.attrs.copy()
        data = enhance2dataset(data)
        data.attrs = new_attrs
        if isinstance(data.attrs.get('sensor'), set) and len(data.attrs['sensor']) == 1:
            data.attrs['sensor'] = list(data.attrs['sensor'])[0]
        return super().__call__([data], **attrs)


class SubBandCompositor(SingleBandCompositor):
    """Get a single band from a provided multi-band DataArray."""

    def __init__(self, name, prerequisites=None, optional_prerequisites=None,
                 band_index=None, **kwargs):
        super().__init__(name, prerequisites=prerequisites,
                         optional_prerequisites=optional_prerequisites,
                         **kwargs)
        if band_index is None:
            raise ValueError("'band_index' must be provided.")
        self._band_index = band_index

    def __call__(self, projectables, nonprojectables=None, **attrs):
        """Index the provided DataArray and create a single band composite from it."""
        if len(projectables) != 1:
            raise ValueError("Can't have more than one band in a single-band composite")

        data = projectables[0]
        if 'bands' not in data.dims:
            raise ValueError("Provided data has no 'bands' dimension.")

        band_index = self._band_index
        if isinstance(band_index, int):
            band_index = data.dims['bands'][band_index]
        data = data.sel(bands=band_index)
        return super().__call__([data], **attrs)
