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
viewing various weather images. NinJo in some ways is like AWIPS is to
the United States Nation Weather Service (NWS), but is used by various
countries around the world.

The NinJo backend for polar2grid was specifically developed to assist the
"Deutscher Wetterdienst" (DWD) in displaying NPP VIIRS data in NinJo.
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

:author:       David Hoese (davidh)
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012-2015 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

from polar2grid.core import roles
from polar2grid.core.rescale import Rescaler
from polar2grid.core.dtype import clip_to_data_type, dtype_to_str, DTYPE_UINT8
from polar2grid.ninjo.ninjotiff_tifffile import write as ninjo_write
import numpy

import os
import sys
import logging
import calendar
from datetime import datetime

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
        "reflectance": (0.490196,0.0),
        "brightness_temperature": (-0.5, 40.0),
        "crefl_true_color": (1.0, 0.0),
        "crefl_false_color": (1.0, 0.0),
        "corrected_reflectance": (1.0, 0.0),
}


def get_default_lw_colortable():
    # Long wave or SVI04 or SVI05 or brightness temp
    #cmap = [
    #    1,6,10,13,16,19,21,23,25,27,29,31,33,35,37,39,40,42,44,45,47,48,50,
    #    51,53,54,56,57,58,60,61,63,64,65,67,68,69,70,72,73,74,75,
    #    77,78,79,80,81,83,84,85,86,87,88,89,91,92,93,94,95,96,97,98,99,100,
    #    101,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,
    #    125,126,127,128,129,130,131,132,133,134,135,136,137,138,138,139,140,141,142,143,144,145,146,146,147,
    #    148,149,150,151,152,153,153,154,155,156,157,158,159,159,160,161,162,
    #    163,164,164,165,166,167,168,169,169,170,171,172,173,173,174,175,176,
    #    177,177,178,179,180,181,181,182,183,184,185,185,186,187,188,188,189,
    #    190,191,192,192,193,194,195,195,196,197,198,198,199,200,201,201,202,203,
    #    204,204,205,206,207,207,208,209,210,210,211,212,213,213,214,215,215,216,217,
    #    218,218,219,220,220,221,222,223,223,224,225,225,226,227,228,228,229,230,230,
    #    231,232,232,233,234,235,235,236,237,237,238,239,239,240,241,241,242,243,244,
    #    244,245,246,246,247,248,248,249,250,250,251,252,252,253,254,254,255
    #]
    #cmap = [cmap]*3
    #return cmap

    # LW colortable is now the same as the SW table
    return get_default_sw_colortable()


def get_default_sw_colortable():
    # Short wave or SVI01 or SVI03 or reflectance
    cmap = [[ x*256 for x in range(256) ]]*3
    return cmap


def create_ninjo_tiff(image_data, output_fn, **kwargs):
    """Create a NinJo compatible TIFF file with the tags used
    by the DWD's version of NinJo.  Also stores the image as tiles on disk
    and creates a multi-resolution/pyramid/overview set of images
    (deresolution: 2,4,8,16).

    :Parameters:
        image_data : 2D numpy array
            Satellite image data to be put into the NinJo compatible tiff
        output_fn : str
            The name of the TIFF file to be created

    :Keywords:
        data_kind : int
            polar2grid constant describing the sensor type of the
            image data, such as DKIND_REFLECTANCE or DKIND_BTEMP. This is
            optional,
            but if not specified then certain keywords below are required. If
            it is specified then a default can be determined for some of the
            keywords (such as `physic_value`).
        cmap : tuple/list of 3 lists of uint16's
            Individual RGB arrays describing the color value for the
            corresponding data value.  For example, image data with a data
            type of unsigned 8-bit integers have 256 possible values (0-255).
            So each list in cmap will have 256 values ranging from 0 to
            65535 (2**16 - 1). (default linear B&W colormap)
        sat_id : int
            DWD NinJo Satellite ID number
        chan_id : int
            DWD NinJo Satellite Channel ID number
        data_source : str
            String describing where the data came from (SSEC, EUMCAST)
        tile_width : int
            Width of tiles on disk (default 512)
        tile_length : int
            Length of tiles on disk (default 512)
        data_cat : str
            NinJo specific data category
                - data_cat[0] = P (polar) or G (geostat)
                - data_cat[1] = O (original) or P (product)
                - data_cat[2:4] = RN or RB or RA or RN or AN (Raster, Bufr, ASCII, NIL)

            Example: 'PORN' or 'GORN' or 'GPRN' or 'PPRN'
            (default 'PORN')
        pixel_xres : float
            Nadir view pixel resolution in degrees longitude
        pixel_yres : float
            Nadir view pixel resolution in degrees latitude
        origin_lat : float
            Top left corner latitude
        origin_lon : float
            Top left corner longitude
        image_dt : datetime object
            Python datetime object describing the date and time of the image
            data provided in UTC
        projection : str
            NinJo compatible projection name (NPOL,PLAT,etc.)
        meridian_west : float
            Western image border (default 0.0)
        meridian_east : float
            Eastern image border (default 0.0)
        radius_a : float
            Large/equatorial radius of the earth (default <not written>)
        radius_b : float
            Small/polar radius of the earth (default <not written>)
        ref_lat1 : float
            Reference latitude 1 (default <not written>)
        ref_lat2 : float
            Reference latitude 2 (default <not written>)
        central_meridian : float
            Central Meridian (default <not written>)
        physic_value : str
            Physical value type. Examples:
                - Temperature = 'T'
                - Albedo = 'ALBEDO'

            Defaults to appropriate value based on `data_kind`, see `itype2physical`
            Specifying this overrides the default of `itype2physical`. If `data_kind`
            is not specified then this keyword is required.
        physic_unit : str
            Physical value units. Examples:
                - 'CELSIUS'
                - '%'

            Defaults to appropriate value based on `data_kind`, see `itype2physical`
            Specifying this overrides the default of `itype2physical`. If `data_kind`
            is not specified then this keyword is required.
        min_gray_val : int
            Minimum gray value (default 0)
        max_gray_val : int
            Maximum gray value (default 255)
        gradient : float
            Gradient/Slope
            Defaults to appropriate value based on `data_kind`, see `itype2grad`
            Specifying this overrides the default of `itype2grad`. If `data_kind`
            is not specified then this keyword is required.
        axis_intercept : float
            Axis Intercept
            Defaults to appropriate value based on `data_kind`, see `itype2grad`
            Specifying this overrides the default of `itype2grad`. If `data_kind`
            is not specified then this keyword is required.
        altitude : float
            Altitude of the data provided (default 0.0)
        is_atmo_corrected : bool
            Is the data atmosphere corrected? (True/1 for yes) (default False/0)
        is_calibrated : bool
            Is the data calibrated? (True/1 for yes) (default False/0)
        is_normalized : bool
            Is the data normalized (True/1 for yes) (default False/0)
        description : str
            Description string to be placed in the output TIFF (optional)

    :Raises:
        KeyError :
            if required keyword is not provided
    """
    LOG.debug("Creating NinJo TIFF file '%s'" % (output_fn,))
    out_tiff = TIFF.open(output_fn, "w")

    image_data = clip_to_data_type(image_data, DTYPE_UINT8)

    # Extract keyword arguments
    data_kind = kwargs.pop("data_kind", None) # called as a backend
    if data_kind is not None and (data_kind not in dkind2physical or data_kind not in dkind2grad):
        # Must do the check here since it matters when pulling out physic value
        LOG.warning("'data_kind' is not known to the ninjo tiff creator, it will be ignored")
        data_kind = None
    cmap = kwargs.pop("cmap", None)
    sat_id = int(kwargs.pop("sat_id"))
    chan_id = int(kwargs.pop("chan_id"))
    data_source = str(kwargs.pop("data_source"))
    tile_width = int(kwargs.pop("tile_width", 512))
    tile_length = int(kwargs.pop("tile_length", 512))
    data_cat = str(kwargs.pop("data_cat", "PORN"))
    pixel_xres = float(kwargs.pop("pixel_xres"))
    pixel_yres = float(kwargs.pop("pixel_yres"))
    origin_lat = float(kwargs.pop("origin_lat"))
    origin_lon = float(kwargs.pop("origin_lon"))
    image_dt = kwargs.pop("image_dt")
    projection = kwargs.pop("projection")
    meridian_west = float(kwargs.pop("meridian_west", 0.0))
    meridian_east = float(kwargs.pop("meridian_east", 0.0))
    radius_a = kwargs.pop("radius_a", None)
    radius_b = kwargs.pop("radius_b", None)
    ref_lat1 = kwargs.pop("ref_lat1", None)
    ref_lat2 = kwargs.pop("ref_lat2", None)
    central_meridian = kwargs.pop("central_meridian", None)
    min_gray_val = int(kwargs.pop("min_gray_val", 0))
    max_gray_val = int(kwargs.pop("max_gray_val", 255))
    altitude = float(kwargs.pop("altitude", 0.0))
    is_atmo_corrected = int(bool(kwargs.pop("is_atmo_corrected", 0)))
    is_calibrated = int(bool(kwargs.pop("is_calibrated", 0)))
    is_normalized = int(bool(kwargs.pop("is_normalized", 0)))
    description = kwargs.pop("description", None)

    # Special cases
    if data_kind is not None:
        physic_value,physic_unit = dkind2physical[data_kind]
        gradient,axis_intercept = dkind2grad[data_kind]
        physic_value = kwargs.pop("physic_value", physic_value)
        physic_unit = kwargs.pop("physic_unit", physic_unit)
        gradient = float(kwargs.pop("gradient", gradient))
        axis_intercept = float(kwargs.pop("axis_intercept", axis_intercept))
    else:
        physic_value = kwargs.pop("physic_value")
        physic_unit = kwargs.pop("physic_unit")
        gradient = float(kwargs.pop("gradient"))
        axis_intercept = float(kwargs.pop("axis_intercept"))

    # Keyword checks / verification
    if cmap is None:
        if data_kind == "brightness_temperature":
            cmap = get_default_lw_colortable()
        else:
            cmap = get_default_sw_colortable()
    elif len(cmap) != 3:
        LOG.error("Colormap (cmap) must be a list of 3 lists (RGB), not %d" % len(cmap))

    if len(data_cat) != 4:
        LOG.error("NinJo data type must be 4 characters")
        raise ValueError("NinJo data type must be 4 characters")
    if data_cat[0] not in ["P", "G"]:
        LOG.error("NinJo data type's first character must be 'P' or 'G' not '%s'" % data_cat[0])
        raise ValueError("NinJo data type's first character must be 'P' or 'G' not '%s'" % data_cat[0])
    if data_cat[1] not in ["O", "P"]:
        LOG.error("NinJo data type's second character must be 'O' or 'P' not '%s'" % data_cat[1])
        raise ValueError("NinJo data type's second character must be 'O' or 'P' not '%s'" % data_cat[1])
    if data_cat[2:4] not in ["RN","RB","RA","BN","AN"]:
        LOG.error("NinJo data type's last 2 characters must be one of %s not '%s'" % ("['RN','RB','RA','BN','AN']", data_cat[2:4]))
        raise ValueError("NinJo data type's last 2 characters must be one of %s not '%s'" % ("['RN','RB','RA','BN','AN']", data_cat[2:4]))

    if description is not None and len(description) >= 1000:
        LOG.error("NinJo description must be less than 1000 characters")
        raise ValueError("NinJo description must be less than 1000 characters")

    file_dt = datetime.utcnow()
    file_epoch = calendar.timegm(file_dt.timetuple())
    image_epoch = calendar.timegm(image_dt.timetuple())

    def _write_oneres(image_data, pixel_xres, pixel_yres, subfile=False):
        LOG.debug("Writing tag data for a resolution of the output file '%s'" % (output_fn,))

        ### Write Tag Data ###
        # Built ins
        out_tiff.SetField("ImageWidth", image_data.shape[1])
        out_tiff.SetField("ImageLength", image_data.shape[0])
        out_tiff.SetField("BitsPerSample", 8)
        out_tiff.SetField("Compression", libtiff.COMPRESSION_LZW)
        out_tiff.SetField("Photometric", libtiff.PHOTOMETRIC_PALETTE)
        out_tiff.SetField("Orientation", libtiff.ORIENTATION_TOPLEFT)
        out_tiff.SetField("SamplesPerPixel", 1)
        out_tiff.SetField("SMinSampleValue", 0)
        out_tiff.SetField("SMaxsampleValue", 255)
        out_tiff.SetField("PlanarConfig", libtiff.PLANARCONFIG_CONTIG)
        out_tiff.SetField("ColorMap", cmap) # Basic B&W colormap
        out_tiff.SetField("TileWidth", tile_width)
        out_tiff.SetField("TileLength", tile_length)
        out_tiff.SetField("SampleFormat", libtiff.SAMPLEFORMAT_UINT)

        # NinJo specific tags
        if description is not None:
            out_tiff.SetField("Description", description)

        out_tiff.SetField("ModelPixelScale", [pixel_xres,pixel_yres])
        out_tiff.SetField("ModelTiePoint", [0.0,  0.0, 0.0, origin_lon, origin_lat, 0.0])
        out_tiff.SetField("NinjoName", "NINJO")
        out_tiff.SetField("SatelliteNameID", sat_id)
        out_tiff.SetField("DateID", image_epoch)
        out_tiff.SetField("CreationDateID", file_epoch)
        out_tiff.SetField("ChannelID", chan_id)
        out_tiff.SetField("HeaderVersion", 2)
        out_tiff.SetField("FileName", output_fn)
        out_tiff.SetField("DataType", data_cat)
        out_tiff.SetField("SatelliteNumber", "\x00") # Hardcoded to 0
        out_tiff.SetField("ColorDepth", 8) # Hardcoded to 8
        out_tiff.SetField("DataSource", data_source)
        out_tiff.SetField("XMinimum", 1)
        out_tiff.SetField("XMaximum", image_data.shape[1])
        out_tiff.SetField("YMinimum", 1)
        out_tiff.SetField("YMaximum", image_data.shape[0])
        out_tiff.SetField("Projection", projection)
        out_tiff.SetField("MeridianWest", meridian_west)
        out_tiff.SetField("MeridianEast", meridian_east)
        if radius_a is not None:
            out_tiff.SetField("EarthRadiusLarge", float(radius_a))
        if radius_b is not None:
            out_tiff.SetField("EarthRadiusSmall", float(radius_b))
        out_tiff.SetField("GeodeticDate", "\x00") # ---?
        if ref_lat1 is not None:
            out_tiff.SetField("ReferenceLatitude1", ref_lat1)
        if ref_lat2 is not None:
            out_tiff.SetField("ReferenceLatitude2", ref_lat2)
        if central_meridian is not None:
            out_tiff.SetField("CentralMeridian", central_meridian)
        out_tiff.SetField("PhysicValue", physic_value) 
        out_tiff.SetField("PhysicUnit", physic_unit)
        out_tiff.SetField("MinGrayValue", min_gray_val)
        out_tiff.SetField("MaxGrayValue", max_gray_val)
        out_tiff.SetField("Gradient", gradient)
        out_tiff.SetField("AxisIntercept", axis_intercept)
        out_tiff.SetField("Altitude", altitude)
        out_tiff.SetField("IsAtmosphereCorrected", is_atmo_corrected)
        out_tiff.SetField("IsCalibrated", is_calibrated)
        out_tiff.SetField("IsNormalized", is_normalized)

        ### Write Base Data Image ###
        out_tiff.write_tiles(image_data)
        out_tiff.WriteDirectory()

    ### Write multi-resolution overviews ###
    out_tiff.SetDirectory(0)
    _write_oneres(image_data, pixel_xres, pixel_yres)
    out_tiff.SetDirectory(1)
    _write_oneres(image_data[::2,::2], pixel_xres*2, pixel_yres*2)
    out_tiff.SetDirectory(2)
    _write_oneres(image_data[::4,::4], pixel_xres*4, pixel_yres*4)
    out_tiff.SetDirectory(3)
    _write_oneres(image_data[::8,::8], pixel_xres*8, pixel_yres*8)
    out_tiff.SetDirectory(4)
    _write_oneres(image_data[::16,::16], pixel_xres*16, pixel_yres*16)
    out_tiff.close()

    LOG.info("Successfully created a NinJo tiff file: '%s'" % (output_fn,))

    return


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
        return self.grid_def["cell_width"]

    @property
    def pixel_size_y(self):
        return self.grid_def["cell_height"]


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


class NinjoGridConfigReader(roles.INIConfigReader):
    id_fields = ("grid_name",)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("float_kwargs", ("xres", "yres"))
        kwargs.setdefault("section_prefix", "ninjo_grid:")
        super(NinjoGridConfigReader, self).__init__(*args, **kwargs)

    @property
    def known_grids(self):
        sections = (x[-1] for x in self.config)
        return list(set(self.config_parser.get(section_name, "grid_name") for section_name in sections))


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
        self.grid_config_reader = NinjoGridConfigReader(*self.backend_configs)
        self.sat_config_reader = NinJoSatConfigReader(*self.backend_configs)
        super(Backend, self).__init__(**kwargs)

    @property
    def known_grids(self):
        return self.grid_config_reader.known_grids

    def create_output_from_product(self, gridded_product, output_pattern=None,
                                   data_type=None, inc_by_one=None, fill_value=0, **kwargs):
        # FIXME: Previous version had -999.0 as the fill value...really?
        grid_def = gridded_product["grid_definition"]
        grid_name = grid_def["grid_name"]
        data_type = data_type or numpy.uint8
        inc_by_one = inc_by_one or False
        grid_config_info = self.grid_config_reader.get_config_options(grid_name=grid_name, allow_default=False)
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
            LOG.debug("Extracting additional information from grid projection")
            map_origin_lon, map_origin_lat = grid_def.lonlat_upperleft
            proj_dict = grid_def.proj4_dict
            equ_radius = proj_dict["a"]
            pol_radius = proj_dict["b"]
            central_meridian = proj_dict.get("lon_0", None)
            ref_lat1 = proj_dict.get("lat_ts", None)

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
            # create_ninjo_tiff(data, output_filename,
            #                   pixel_xres=grid_config_info["xres"],
            #                   pixel_yres=grid_config_info["yres"],
            #                   projection=grid_config_info["projection"],
            #                   origin_lat=map_origin_lat,
            #                   origin_lon=map_origin_lon,
            #                   radius_a=equ_radius,
            #                   radius_b=pol_radius,
            #                   central_meridian=central_meridian,
            #                   ref_lat1=ref_lat1,
            #                   is_calibrated=1,
            #                   sat_id=band_config_info["satellite_id"],
            #                   chan_id=band_config_info["band_id"],
            #                   data_source=band_config_info["data_source"],
            #                   data_cat=band_config_info["data_category"],
            #                   image_dt=gridded_product["begin_time"],
            #                   data_kind=gridded_product["data_kind"]
            #                   )
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
    group.add_argument('--backend-configs', nargs="*", dest="rescale_configs",
                       help="alternative backend configuration files")
    group = parser.add_argument_group(title="Backend Output Creation")
    group.add_argument("--output-pattern", default=DEFAULT_OUTPUT_PATTERN,
                       help="output filenaming pattern")
    # group.add_argument('--dont-inc', dest="inc_by_one", default=True, action="store_false",
    #                    help="do not increment data by one (ex. 0-254 -> 1-255 with 0 being fill)")
    return ["Backend Initialization", "Backend Output Creation"]


def main():
    from polar2grid.core.script_utils import create_basic_parser, create_exc_handler, setup_logging
    from polar2grid.core.containers import GriddedScene, GriddedProduct
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
