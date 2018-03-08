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
# Written by David Hoese    October 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""The NinJo backend is used to create NinJo compatible TIFF files, also
known as NinJoTIFFs. The NinJo Workstation Project is a meteorological
workstation system for
viewing weather data. NinJo is the operational weather visualization 
and analysis tool used by a number of countries throughout the world.

The NinJo backend for Polar2Grid was specifically developed to assist the
"Deutscher Wetterdienst" (DWD) in displaying Suomi NPP VIIRS data in NinJo.
This partnership between the DWD and |ssec| lead to a fairly specialized
system that creates NinJo compatible TIFF images. NinJo allows for
multiple "readers" or plugins to its system to allow for various formats
to be read. The polar2grid backend is specifically for the TIFF reader
used by the DWD. These files are different
from regular TIFF images in that they have a number of tags for describing
the data and the location of that data to NinJo.

The NinJo backend must be configured to support a specific grid and is
currently only configured for the DWD Germany grid (dwd_germany) and the
Alaska (203) grid.

"""
__docformat__ = "restructuredtext en"

import sys

import logging
import numpy
import os

from polar2grid.core import roles
from polar2grid.core.dtype import clip_to_data_type, dtype_to_str, DTYPE_UINT8
from polar2grid.core.rescale import Rescaler
from polar2grid.ninjo.ninjotiff_tifffile import write as ninjo_write

LOG = logging.getLogger(__name__)

DEFAULT_NINJO_RCONFIG = "polar2grid.ninjo:rescale_ninjo.ini"
DEFAULT_NINJO_CONFIG = "ninjo_backend.ini"
DEFAULT_OUTPUT_PATTERN = "{satellite}_{instrument}_{product_name}_{begin_time}_{grid_name}.tif"

dkind2mpop_physical = {
    "equalized_radiance": "Unknown",
    "reflectance": "%",
    # our P2G scaling always makes them celsius even if they are Kelvin
    "brightness_temperature": "C",
    "crefl_true_color": "Unknown",
    "crefl_false_color": "Unknown",
    "corrected_reflectance": "Unknown",
}

dkind2physical = {
        "equalized_radiance": ("\0", "\0"),
        "reflectance": ("ALBEDO", "%"),
        "brightness_temperature": ("T", "CELSIUS"),
}

dkind2grad = {
        "equalized_radiance": (1.0, 0.0),
        "reflectance": (0.490196, 0.0),
        "brightness_temperature": (-0.5, 40.0),
        "crefl_true_color": (1.0, 0.0),
        "crefl_false_color": (1.0, 0.0),
        "corrected_reflectance": (1.0, 0.0),
}


class FakeAreaDef(object):
    def __init__(self, grid_def):
        """Convert from a Polar2Grid Grid Definition to something that behaves like a mpop area definition.
        """
        self.grid_def = grid_def

    @property
    def y_size(self):
        return self.grid_def["height"]

    @property
    def x_size(self):
        return self.grid_def["width"]

    def get_lonlat(self, x, y):
        return self.grid_def.get_lonlat(x, y)

    @property
    def shape(self):
        return self.y_size, self.x_size

    @property
    def proj_dict(self):
        return self.grid_def.proj4_dict

    @property
    def pixel_size_x(self):
        # mpop requires that pixel size must always be positive
        return abs(self.grid_def["cell_width"])

    @property
    def pixel_size_y(self):
        # mpop requires that pixel size must always be positive
        return abs(self.grid_def["cell_height"])


def save(data, grid_def, filename, ninjo_product_name=None, **kwargs):
    """MPOP's interface to Ninjo TIFF writer. Temporary work around until mpop is fully integrated.

    :Parameters:
        geo_image : mpop.imageo.geo_image.GeoImage
            See MPOP's documentation.
        filename : str
            The name of the TIFF file to be created
    :Keywords:
        ninjo_product_name : str
            Optional index to Ninjo configuration file.
        kwargs : dict
            See _write
    """
    data = clip_to_data_type(data, DTYPE_UINT8)
    area_def = FakeAreaDef(grid_def)

    # Some Ninjo tiff names
    kwargs['gradient'], kwargs['axis_intercept'] = dkind2grad[kwargs["data_kind"]]
    kwargs['physic_unit'] = dkind2mpop_physical[kwargs["data_kind"]]
    kwargs['image_dt'] = kwargs.pop("begin_time")
    kwargs['transparent_pix'] = kwargs.pop("fill_value")
    kwargs['is_calibrated'] = True
    kwargs['ninjo_product_name'] = kwargs.pop("product_name")

    # reorder data to (Y, X, 3) from (3, Y, X)
    if data.ndim > 2:
        data = numpy.dstack(data)

    ninjo_write(data, filename, area_def, ninjo_product_name, **kwargs)


class NinjoBandConfigReader(roles.INIConfigReader):
    id_fields = (
        "product_name",
        "data_type",
        "data_kind",
        "satellite",
        "instrument",
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("int_kwargs", ("band_id",))
        kwargs.setdefault("section_prefix", "ninjo_product:")
        super(NinjoBandConfigReader, self).__init__(*args, **kwargs)


class NinJoSatConfigReader(roles.SimpleINIConfigReader):
    def __init__(self, *config_files, **kwargs):
        self.section_prefix = kwargs.pop("section_prefix", "ninjo_satellite:")
        super(NinJoSatConfigReader, self).__init__(*config_files, **kwargs)

    def get_satellite_id(self, product_info):
        section_name = self.section_prefix + product_info["satellite"]
        if self.config_parser.has_section(section_name):
            return self.config_parser.getint(section_name, "satellite_id")
        raise RuntimeError("No satellite section for the provided product with satellite: {}".format(product_info["satellite"]))


class Backend(roles.BackendRole):
    def __init__(self, backend_configs=None, rescale_configs=None, **kwargs):
        self.rescale_configs = rescale_configs or [DEFAULT_NINJO_RCONFIG]
        self.backend_configs = backend_configs or [DEFAULT_NINJO_CONFIG]
        self.rescaler = Rescaler(*self.rescale_configs)
        self.band_config_reader = NinjoBandConfigReader(*self.backend_configs)
        self.sat_config_reader = NinJoSatConfigReader(*self.backend_configs)
        super(Backend, self).__init__(**kwargs)

    @property
    def known_grids(self):
        # should work regardless of grid
        return None

    def create_output_from_product(self, gridded_product, output_pattern=None,
                                   data_type=None, inc_by_one=None, fill_value=0, **kwargs):
        # FIXME: Previous version had -999.0 as the fill value...really?
        grid_def = gridded_product["grid_definition"]
        data_type = data_type or numpy.uint8
        inc_by_one = inc_by_one or False
        band_config_info = self.band_config_reader.get_config_options(
            product_name=gridded_product["product_name"],
            satellite=gridded_product["satellite"],
            instrument=gridded_product["instrument"],
            data_type=gridded_product["data_type"],
            data_kind=gridded_product["data_kind"],
            allow_default=False,
        )
        band_config_info["satellite_id"] = self.sat_config_reader.get_satellite_id(gridded_product)

        if not output_pattern:
            output_pattern = DEFAULT_OUTPUT_PATTERN
        if "{" in output_pattern:
            # format the filename
            of_kwargs = gridded_product.copy(as_dict=True)
            of_kwargs["data_type"] = dtype_to_str(data_type)
            output_filename = self.create_output_filename(output_pattern,
                                                          grid_name=grid_def["grid_name"],
                                                          rows=grid_def["height"],
                                                          columns=grid_def["width"],
                                                          **of_kwargs)
        else:
            output_filename = output_pattern

        if os.path.isfile(output_filename):
            if not self.overwrite_existing:
                LOG.error("NinJo TIFF file already exists: %s", output_filename)
                raise RuntimeError("NinJo TIFF file already exists: %s" % (output_filename,))
            else:
                LOG.warning("NinJo TIFF file already exists, will overwrite: %s", output_filename)

        try:
            LOG.debug("Scaling %s data to fit in ninjotiff...", gridded_product["product_name"])
            data = self.rescaler.rescale_product(gridded_product, data_type,
                                                 inc_by_one=inc_by_one, fill_value=fill_value)

            # Create the geotiff
            save(data, grid_def, output_filename,
                 sat_id=band_config_info["satellite_id"],
                 chan_id=band_config_info["band_id"],
                 data_source=band_config_info["data_source"],
                 data_cat=band_config_info["data_category"],
                 fill_value=fill_value,
                 data_kind=gridded_product["data_kind"],
                 begin_time=gridded_product["begin_time"],
                 product_name=gridded_product["product_name"],
                 )
        except StandardError:
            if not self.keep_intermediate and os.path.isfile(output_filename):
                os.remove(output_filename)
            raise

        return output_filename


def add_backend_argument_groups(parser):
    parser.set_defaults(forced_grids=None)
    group = parser.add_argument_group(title="Backend Initialization")
    group.add_argument('--rescale-configs', nargs="*", dest="rescale_configs",
                       help="alternative rescale configuration files")
    group.add_argument('--backend-configs', nargs="*", dest="backend_configs",
                       help="alternative backend configuration files")
    group = parser.add_argument_group(title="Backend Output Creation")
    group.add_argument("--output-pattern", default=DEFAULT_OUTPUT_PATTERN,
                       help="output filenaming pattern")
    group.add_argument('--dont-inc', dest="inc_by_one", default=True, action="store_false",
                       help="do not increment data by one (ex. 0-254 -> 1-255 with 0 being fill)")
    return ["Backend Initialization", "Backend Output Creation"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    from polar2grid.core.script_utils import GriddedScene, GriddedProduct
    parser = create_basic_parser(description="Create NinJo files from provided gridded scene or product data")
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
