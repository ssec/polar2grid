#!/usr/bin/env python
# encoding: utf-8
"""Simple backend to just passively 'produce' the binary files that are
provided.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

from polar2grid.core.rescale import Rescaler
from polar2grid.core import roles
from polar2grid.core.dtype import convert_to_data_type,clip_to_data_type
from polar2grid.core.constants import *

DEFAULT_8BIT_RCONFIG      = "rescale_configs/rescale.8bit.conf"
DEFAULT_16BIT_RCONFIG     = "rescale_configs/rescale.16bit.conf"
DEFAULT_INC_8BIT_RCONFIG  = "rescale_configs/rescale_inc.8bit.conf"
DEFAULT_INC_16BIT_RCONFIG = "rescale_configs/rescale_inc.16bit.conf"
DEFAULT_OUTPUT_PATTERN = "%(sat)s_%(instrument)s_%(kind)s_%(band)s_%(start_time)s_%(grid_name)s.%(fbf_dtype)s.%(cols)s.%(rows)s"

class Backend(roles.BackendRole):
    def __init__(self, output_pattern=None,
            rescale_config=None, fill_value=DEFAULT_FILL_VALUE,
            data_type=None, inc_by_one=False):
        self.output_pattern = output_pattern or DEFAULT_OUTPUT_PATTERN
        self.data_type = data_type or DTYPE_FLOAT32

        # Use predefined rescaling configurations if we weren't told what to do
        if rescale_config is None:
            if self.data_type == DTYPE_UINT8:
                if inc_by_one:
                    rescale_config = DEFAULT_INC_8BIT_RCONFIG
                else:
                    rescale_config = DEFAULT_8BIT_RCONFIG
            elif self.data_type == DTYPE_UINT16:
                if inc_by_one:
                    rescale_config = DEFAULT_INC_16BIT_RCONFIG
                else:
                    rescale_config = DEFAULT_16BIT_RCONFIG
        self.rescale_config = rescale_config

        # Create the rescaler if we know what to do
        self.fill_in = fill_value
        self.fill_out = DEFAULT_FILL_VALUE
        if rescale_config is None:
            self.rescaler = None
        else:
            self.rescaler = Rescaler(config=self.rescale_config,
                    fill_in=self.fill_in, fill_out=self.fill_out,
                    inc_by_one=inc_by_one
                    )

    def can_handle_inputs(self, sat, instrument, kind, band, data_kind):
        return GRIDS_ANY

    def create_product(self, sat, instrument,
            kind, band, data_kind, data,
            output_filename=None, start_time=None, end_time=None,
            grid_name=None, data_type=None, inc_by_one=None,
            fill_value=None):
        fill_in = fill_value or self.fill_in
        data_type = data_type or self.data_type

        # Create the output filename if its not provided
        if output_filename is None:
            output_filename = self.create_output_filename(self.output_pattern,
                    sat, instrument, kind, band, data_kind,
                    start_time  = start_time,
                    end_time    = end_time,
                    grid_name   = grid_name,
                    data_type   = data_type,
                    cols        = data.shape[1],
                    rows        = data.shape[0]
                    )

        # Rescale the data based on the configuration that was loaded earlier
        if self.rescaler:
            data = self.rescaler(sat, instrument, kind, band, data_kind, data,
                    fill_in=fill_in, fill_out=self.fill_out,
                    inc_by_one=inc_by_one)

            # Clip to the proper data type range and convert to that data type
            if data_type is not None:
                data = clip_to_data_type(data, data_type)
        elif data_type is not None:
            # Convert to a certain data type
            data = convert_to_data_type(data, data_type)

        # Write the binary data to a file
        data.tofile(output_filename)

