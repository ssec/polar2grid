#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2012-2015 Space Science and Engineering Center (SSEC),
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
"""The Geotiff backend puts gridded image data into a standard geotiff file.  It
uses the GDAL python API to create the geotiff files. It can handle any grid that
can be described by PROJ.4 and understand by Geotiff.

:author:       David Hoese (davidh)
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

from osgeo import gdal
import osr
import numpy as np

from polar2grid.core.rescale import Rescaler, DEFAULT_RCONFIG
from polar2grid.core import roles
from polar2grid.core.dtype import clip_to_data_type, str_to_dtype

import os
import sys
import logging

LOG = logging.getLogger(__name__)

gtiff_driver = gdal.GetDriverByName("GTIFF")

DEFAULT_OUTPUT_PATTERN = "{satellite}_{instrument}_{product_name}_{begin_time}_{grid_name}.tif"


def _proj4_to_srs(proj4_str):
    """Helper function to convert a proj4 string
    into a GDAL compatible srs.  Mainly a function
    so if used multiple times it only has to be changed
    once for special cases.
    """
    try:
        srs = osr.SpatialReference()
        # GDAL doesn't like unicode
        result = srs.ImportFromProj4(str(proj4_str))
    except StandardError:
        LOG.error("Could not convert Proj4 string '%s' into a GDAL SRS" % (proj4_str,))
        LOG.debug("Exception: ", exc_info=True)
        raise ValueError("Could not convert Proj4 string '%s' into a GDAL SRS" % (proj4_str,))

    if result != 0:
        LOG.error("Could not convert Proj4 string '%s' into a GDAL SRS" % (proj4_str,))
        raise ValueError("Could not convert Proj4 string '%s' into a GDAL SRS" % (proj4_str,))

    return srs


def create_geotiff(data, output_filename, proj4_str, geotransform, etype=gdal.GDT_UInt16, compress=None,
                   quicklook=False, **kwargs):
    """Function that creates a geotiff from the information provided.
    """
    log_level = logging.getLogger('').handlers[0].level or 0
    LOG.info("Creating geotiff '%s'" % (output_filename,))

    # Find the number of bands provided
    if isinstance(data, (list, tuple)):
        num_bands = len(data)
    elif len(data.shape) == 2:
        num_bands = 1
    else:
        num_bands = data.shape[0]

    # We only know how to handle gray scale, RGB, and RGBA
    if num_bands not in [1, 3, 4]:
        msg = "Geotiff backend doesn't know how to handle data of shape '%r'" % (data.shape,)
        LOG.error(msg)
        raise ValueError(msg)

    options = []
    if num_bands == 1:
        options.append("PHOTOMETRIC=MINISBLACK")
    elif num_bands == 3:
        options.append("PHOTOMETRIC=RGB")
    elif num_bands == 4:
        options.append("PHOTOMETRIC=RGB")

    if compress is not None and compress != "NONE":
        options.append("COMPRESS=%s" % (compress,))

    # Creating the file will truncate any pre-existing file
    LOG.debug("Creation Geotiff with options %r", options)
    if num_bands == 1:
        gtiff = gtiff_driver.Create(output_filename, data.shape[1], data.shape[0],
                                    bands=num_bands, eType=etype, options=options)
    else:
        gtiff = gtiff_driver.Create(output_filename, data[0].shape[1], data[0].shape[0],
                                    bands=num_bands, eType=etype, options=options)

    gtiff.SetGeoTransform(geotransform)
    srs = _proj4_to_srs(proj4_str)
    gtiff.SetProjection(srs.ExportToWkt())

    for idx in range(num_bands):
        gtiff_band = gtiff.GetRasterBand(idx + 1)

        if num_bands == 1:
            band_data = data
        else:
            band_data = data[idx]

        # Clip data to datatype, otherwise let it go and see what happens
        # XXX: This might need to operate on colors as a whole or
        # do a linear scaling. No one should be scaling data to outside these
        # ranges anyway
        if etype == gdal.GDT_UInt16:
            band_data = clip_to_data_type(band_data, np.uint16)
        elif etype == gdal.GDT_Byte:
            band_data = clip_to_data_type(band_data, np.uint8)
        if log_level <= logging.DEBUG:
            LOG.debug("Data min: %f, max: %f" % (band_data.min(), band_data.max()))

        # Write the data
        if gtiff_band.WriteArray(band_data) != 0:
            LOG.error("Could not write band 1 data to geotiff '%s'" % (output_filename,))
            raise ValueError("Could not write band 1 data to geotiff '%s'" % (output_filename,))

    if quicklook:
        png_filename = output_filename.replace(os.path.splitext(output_filename)[1], ".png")
        png_driver = gdal.GetDriverByName("PNG")
        png_driver.CreateCopy(png_filename, gtiff)

    # Garbage collection/destructor should close the file properly


np2etype = {
    np.uint16: gdal.GDT_UInt16,
    np.uint8: gdal.GDT_Byte,
    np.float32: gdal.GDT_Float32,
}


class Backend(roles.BackendRole):
    def __init__(self, rescale_configs=None, **kwargs):
        self.rescale_configs = rescale_configs or [DEFAULT_RCONFIG]
        self.rescaler = Rescaler(*self.rescale_configs)
        super(Backend, self).__init__(**kwargs)

    @property
    def known_grids(self):
        # should work regardless of grid
        return None

    def create_output_from_product(self, gridded_product, output_pattern=None,
                                   data_type=None, inc_by_one=None, fill_value=0, **kwargs):
        data_type = data_type or np.uint8
        etype = np2etype[data_type]
        inc_by_one = inc_by_one or False
        grid_def = gridded_product["grid_definition"]
        if not output_pattern:
            output_pattern = DEFAULT_OUTPUT_PATTERN
        if "{" in output_pattern:
            # format the filename
            of_kwargs = gridded_product.copy(as_dict=True)
            of_kwargs["data_type"] = data_type
            output_filename = self.create_output_filename(output_pattern,
                                                          grid_name=grid_def["grid_name"],
                                                          rows=grid_def["height"],
                                                          columns=grid_def["width"],
                                                          **of_kwargs)
        else:
            output_filename = output_pattern

        if os.path.isfile(output_filename):
            if not self.overwrite_existing:
                LOG.error("Geotiff file already exists: %s", output_filename)
                raise RuntimeError("Geotiff file already exists: %s" % (output_filename,))
            else:
                LOG.warning("Geotiff file already exists, will overwrite: %s", output_filename)

        try:
            if np.issubdtype(data_type, np.floating):
                # assume they don't want to scale floating point
                data = gridded_product.get_data_array()
            else:
                LOG.debug("Scaling %s data to fit in geotiff...", gridded_product["product_name"])
                data = self.rescaler.rescale_product(gridded_product, data_type,
                                                     inc_by_one=inc_by_one, fill_value=fill_value)

            # Create the geotiff
            # X and Y rotation are 0 in most cases so we just hard-code it
            geotransform = gridded_product["grid_definition"].gdal_geotransform
            create_geotiff(data, output_filename, grid_def["proj4_definition"], geotransform,
                           etype=etype, **kwargs)
        except StandardError:
            if not self.keep_intermediate and os.path.isfile(output_filename):
                os.remove(output_filename)
            raise

        return output_filename


def add_backend_argument_groups(parser):
    parser.set_defaults(forced_grids=["wgs84_fit"])
    group = parser.add_argument_group(title="Backend Initialization")
    group.add_argument('--rescale-configs', nargs="*", dest="rescale_configs",
                       help="alternative rescale configuration files")
    group = parser.add_argument_group(title="Backend Output Creation")
    group.add_argument("--output-pattern", default=DEFAULT_OUTPUT_PATTERN,
                       help="output filenaming pattern")
    group.add_argument('--dont-inc', dest="inc_by_one", default=True, action="store_false",
                       help="do not increment data by one (ex. 0-254 -> 1-255 with 0 being fill)")
    group.add_argument("--compress", default="LZW", choices=["JPEG", "LZW", "PACKBITS", "DEFLATE", "NONE"],
                       help="Specify compression method for geotiff")
    group.add_argument("--png-quicklook", dest="quicklook", action="store_true",
                       help="Create a PNG version of the created geotiff")
    group.add_argument("--dtype", dest="data_type", type=str_to_dtype, default=None,
                        help="specify the data type for the backend to output")
    return ["Backend Initialization", "Backend Output Creation"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    from polar2grid.core.containers import GriddedScene, GriddedProduct
    parser = create_basic_parser(description="Create geotiff files from provided gridded scene or product data")
    subgroup_titles = add_backend_argument_groups(parser)
    parser.add_argument("--scene", required=True, help="JSON SwathScene filename to be remapped")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(subgroup_titles=subgroup_titles, global_keywords=global_keywords)

    # Logs are renamed once data the provided start date is known
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)

    LOG.info("Loading scene or product...")
    gridded_scene = GriddedScene.load(args.scene)

    LOG.info("Initializing backend...")
    backend = Backend(**args.subgroup_args["Backend Initialization"])
    if isinstance(gridded_scene, GriddedScene):
        backend.create_output_from_scene(gridded_scene, **args.subgroup_args["Backend Output Creation"])
    elif isinstance(gridded_scene, GriddedProduct):
        backend.create_output_from_product(gridded_scene, **args.subgroup_args["Backend Output Creation"])
    else:
        raise ValueError("Unknown Polar2Grid object provided")

if __name__ == "__main__":
    sys.exit(main())
