#!/usr/bin/env python
# encoding: utf-8
"""polar2grid backend to take polar-orbitting satellite data arrays
and place it into a geotiff.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3

Copyright (C) 2013 Space Science and Engineering Center (SSEC),
 University of Wisconsin-Madison.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

This file is part of the polar2grid software package. Polar2grid takes
satellite observation data, remaps it, and writes it to a file format for
input into another program.
Documentation: http://www.ssec.wisc.edu/software/polar2grid/

    Written by David Hoese    January 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

from osgeo import gdal
import osr
import numpy

from polar2grid.core.rescale import Rescaler, Rescaler2
from polar2grid.core.constants import *
from polar2grid.core import roles
from polar2grid.core.dtype import normalize_dtype_string, clip_to_data_type, str_to_dtype

import sys
import logging

log = logging.getLogger(__name__)

gtiff_driver = gdal.GetDriverByName("GTIFF")

DEFAULT_RCONFIG      = "rescale_configs/rescale.ini"
DEFAULT_8BIT_RCONFIG      = "rescale_configs/rescale.8bit.conf"
DEFAULT_16BIT_RCONFIG     = "rescale_configs/rescale.16bit.conf"
DEFAULT_INC_8BIT_RCONFIG  = "rescale_configs/rescale_inc.8bit.conf"
DEFAULT_INC_16BIT_RCONFIG = "rescale_configs/rescale_inc.16bit.conf"
DEFAULT_OUTPUT_PATTERN = "%(sat)s_%(instrument)s_%(kind)s_%(band)s_%(start_time)s_%(grid_name)s.tif"
DEFAULT_OUTPUT_PATTERN2 = "%(satellite)s_%(instrument)s_%(product_name)s_%(begin_time)s_%(grid_name)s.tif"

def _proj4_to_srs(proj4_str):
    """Helper function to convert a proj4 string
    into a GDAL compatible srs.  Mainly a function
    so if used multiple times it only has to be changed
    once for special cases.
    """
    srs = osr.SpatialReference()
    if proj4_str[:4].lower() == "epsg":
        epsg_code = int(proj4_str[5:]) # ex. "EPSG:3857"
        result = srs.ImportFromEPSG(epsg_code)
    else:
        result = srs.ImportFromProj4(proj4_str)
    if result != 0:
        log.error("Could not convert Proj4 string '%s' into a GDAL SRS" % (proj4_str,))
        raise ValueError("Could not convert Proj4 string '%s' into a GDAL SRS" % (proj4_str,))
    return srs

def create_geotiff(data, output_filename, proj4_str, geotransform,
        etype=gdal.GDT_UInt16):
    """Function that creates a geotiff from the information provided.
    """
    log_level = logging.getLogger('').handlers[0].level or 0
    log.info("Creating geotiff '%s'" % (output_filename,))

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
        log.error(msg)
        raise ValueError(msg)

    if num_bands == 1:
        photometric = "PHOTOMETRIC=MINISBLACK"
    elif num_bands == 3:
        photometric = "PHOTOMETRIC=RGB"
    elif num_bands == 4:
        photometric = "PHOTOMETRIC=RGB"

    # Creating the file will truncate any pre-existing file
    if num_bands == 1:
        gtiff = gtiff_driver.Create(output_filename,
                data.shape[1], data.shape[0],
                bands=num_bands, eType=etype, options = [ photometric ])
    else:
        gtiff = gtiff_driver.Create(output_filename,
                data[0].shape[1], data[0].shape[0],
                bands=num_bands, eType=etype, options = [ photometric ])

    gtiff.SetGeoTransform(geotransform)
    srs = _proj4_to_srs(proj4_str)
    gtiff.SetProjection(srs.ExportToWkt())

    for idx in range(num_bands):
        gtiff_band = gtiff.GetRasterBand(idx + 1)

        if num_bands == 1: band_data = data
        else: band_data = data[idx]

        # Clip data to datatype, otherwise let it go and see what happens
        # XXX: This might need to operate on colors as a whole or
        # do a linear scaling. No one should be scaling data to outside these
        # ranges anyway
        if etype == gdal.GDT_UInt16:
            band_data = clip_to_data_type(band_data, DTYPE_UINT16)
        elif etype == gdal.GDT_Byte:
            band_data = clip_to_data_type(band_data, DTYPE_UINT8)
        if log_level <= logging.DEBUG:
            log.debug("Data min: %f, max: %f" % (band_data.min(),band_data.max()))

        # Write the data
        if gtiff_band.WriteArray(band_data) != 0:
            log.error("Could not write band 1 data to geotiff '%s'" % (output_filename,))
            raise ValueError("Could not write band 1 data to geotiff '%s'" % (output_filename,))
    # Garbage collection/destructor should close the file properly

dtype2etype = {
        DTYPE_UINT16  : gdal.GDT_UInt16,
        DTYPE_UINT8   : gdal.GDT_Byte
        }

np2etype = {
    numpy.uint16: gdal.GDT_UInt16,
    numpy.uint8: gdal.GDT_Byte,
}

class Backend(roles.BackendRole):
    removable_file_patterns = [
            "*_*_*_*_????????_??????_*.tif"
            ]

    def __init__(self, output_pattern=None,
            rescale_config=None, fill_value=DEFAULT_FILL_VALUE,
            data_type=None, inc_by_one=False):
        """
            - data_type:
                Specify the polar2grid data type, which will determine the
                'etype' of the geotiff. Default 8bit unsigned integers.
            - rescale_config:
                Rescaling configuration file to be used in scaling the data
            - inc_by_one:
                Used by the Rescaler to add one to the scaled data.  See
                `Rescaler` documentation for more information.
            - output_pattern:
                Specify the python output dictionary formatting string
            - fill_value:
                Specify the fill value of the incoming data.
        """
        self.output_pattern = output_pattern or DEFAULT_OUTPUT_PATTERN
        self.data_type = data_type or DTYPE_UINT8
        self.etype     = dtype2etype[self.data_type]

        # Use predefined rescaling configurations if we weren't told what to do
        if rescale_config is None:
            if self.etype == gdal.GDT_UInt16:
                if inc_by_one:
                    rescale_config = DEFAULT_INC_16BIT_RCONFIG
                else:
                    rescale_config = DEFAULT_16BIT_RCONFIG
            elif self.etype == gdal.GDT_Byte:
                if inc_by_one:
                    rescale_config = DEFAULT_INC_8BIT_RCONFIG
                else:
                    rescale_config = DEFAULT_8BIT_RCONFIG
        self.rescale_config = rescale_config

        # Instantiate the rescaler
        self.fill_in = fill_value
        self.fill_out = DEFAULT_FILL_VALUE
        self.rescaler = Rescaler(self.rescale_config,
                fill_in=self.fill_in, fill_out=self.fill_out,
                inc_by_one=inc_by_one
                )

    def can_handle_inputs(self, sat, instrument, nav_set_uid, kind, band, data_kind):
        """Function for backend-calling script to ask if the backend
        will be able to handle the data that will be processed.
        For the geotiff backend it can handle any kind or band with a proj4
        projection.

        It is also assumed that rescaling will be able to handle the `data_kind`
        provided.
        """
        return GRIDS_ANY_PROJ4

    def create_product(self, sat, instrument, nav_set_uid, kind, band, data_kind, data,
            start_time=None, end_time=None, grid_name=None,
            proj4_str=None, grid_origin_x=None, grid_origin_y=None,
            pixel_size_x=None, pixel_size_y=None,
            output_filename=None, data_type=None, fill_value=None,
            rotate_x=0, rotate_y=0, inc_by_one=None):
        """Function to be called from a connecting script to interpret the
        information provided and create a geotiff.

        Most arguments are keywords to fit the backend interface, but some
        of these keywords are required:

            - start_time (required if `output_filename` is not):
                Parameter to make the output filename more specific
            - grid_name (required if `output_filename` is not):
                Parameter to make the output filename more specific.
                Does not have to equal an actual grid_name in a configuration
                file.
            - proj4_str:
                Used to set the projection in the geotiff file
            - grid_origin_x:
                Used in the geotransform of the geotiff. No value checking is done
                for this value, so an understanding of GDAL geotiff geotransforms
                is required.
            - grid_origin_y:
                Used in the geotransform of the geotiff. No value checking is done
                for this value, so an understanding of GDAL geotiff geotransforms
                is required.
            - pixel_size_x:
                Used in the geotransform of the geotiff. No value checking is done
                for this value, so an understanding of GDAL geotiff geotransforms
                is required.
            - pixel_size_y:
                Used in the geotransform of the geotiff. No value checking is done
                for this value, so an understanding of GDAL geotiff geotransforms
                is required.

        Optional keywords:

            - end_time (used if `output_filename` is not):
                Parameter to make the output filename more specific, added to
                start_time to produce "YYYYMMDD_HHMMSS_YYYYMMDD_HHMMSS"
            - output_filename:
                Force the filename of the geotiff being produced
            - rotate_x (not part of the backend interface):
                Parameter that can be used in GDAL geotransforms, but is rarely
                useful.
            - rotate_y (not part of the backend interface):
                Parameter that can be used in GDAL geotransforms, but is rarely
                useful.
            - inc_by_one:
                See __init__ documentation or Rescaler documentation
        """
        data_type = data_type or self.data_type
        etype = dtype2etype[data_type] or self.etype
        fill_in = fill_value or self.fill_in

        # Create the filename if it wasn't provided
        if output_filename is None:
            output_filename = self.create_output_filename(self.output_pattern,
                    sat, instrument, nav_set_uid, kind, band, data_kind,
                    start_time  = start_time,
                    end_time    = end_time,
                    grid_name   = grid_name,
                    data_type   = data_type,
                    cols        = data.shape[1],
                    rows        = data.shape[0]
                    )

        # Rescale the data based on the configuration that was loaded earlier
        data = self.rescaler(sat, instrument, nav_set_uid, kind, band, data_kind, data,
                fill_in=fill_in, fill_out=self.fill_out, inc_by_one=inc_by_one)
        # If the data is incremented by one the data filters in create_geotiff
        # will cause the fill value to be set to zero (so positive fills won't
        # work)

        # Create the geotiff
        geotransform = (grid_origin_x, pixel_size_x, rotate_x, grid_origin_y, rotate_y, pixel_size_y)
        create_geotiff(data, output_filename, proj4_str, geotransform, etype=etype)


class Backend2(roles.BackendRole2):
    def __init__(self, rescale_configs=None):
        self.rescale_configs = rescale_configs or [DEFAULT_RCONFIG]
        self.rescaler = Rescaler2(*self.rescale_configs)

    def create_output_from_scene(self, gridded_scene, output_pattern=None, inc_by_one=None):
        output_filenames = []
        for product_name, gridded_product in gridded_scene.items():
            output_fn = self.create_output_from_product(gridded_product, output_pattern=output_pattern,
                                                        inc_by_one=inc_by_one)
            output_filenames.append(output_fn)
        return output_filenames

    def create_output_from_product(self, gridded_product, output_pattern=None,
                                   data_type=None, inc_by_one=None, fill_value=0):
        data_type = data_type or DTYPE_UINT8
        data_type = str_to_dtype(data_type)
        etype = np2etype[data_type]
        inc_by_one = inc_by_one or False
        grid_def = gridded_product["grid_definition"]
        if not output_pattern:
            output_pattern = DEFAULT_OUTPUT_PATTERN2
        if "%" in output_pattern:
            # format the filename
            kwargs = gridded_product.copy()
            kwargs["data_type"] = data_type
            output_filename = self.create_output_filename(output_pattern,
                                                          grid_name=grid_def["grid_name"],
                                                          rows=grid_def["height"],
                                                          columns=grid_def["width"],
                                                          **gridded_product)
        else:
            output_filename = output_pattern

        log.info("Scaling %s data to fit in geotiff...", gridded_product["product_name"])
        data = self.rescaler.rescale_product(gridded_product, data_type, inc_by_one=inc_by_one, fill_value=fill_value)

        # Create the geotiff
        # X and Y rotation are 0 in most cases so we just hard-code it
        geotransform = (grid_def["origin_x"], grid_def["cell_width"], 0,
                        grid_def["origin_y"], 0, grid_def["cell_height"])
        create_geotiff(data, output_filename, grid_def["proj4_definition"], geotransform, etype=etype)
        return output_filename


def _type_dt(datestring):
    from datetime import datetime
    return datetime.strptime(datestring, "%Y%m%d_%H%M%S")

def _type_datakind(kind_str):
    from polar2grid.core.constants import DKIND_REFLECTANCE,DKIND_RADIANCE,DKIND_BTEMP,DKIND_FOG
    kind_str = kind_str.lower()
    if kind_str in ["reflectance"]:
        return DKIND_REFLECTANCE
    elif kind_str in ["radiance"]:
        return DKIND_RADIANCE
    elif kind_str in ["btemp","brightness temperature"]:
        return DKIND_BTEMP
    elif kind_str in ["fog"]:
        return DKIND_FOG
    raise ValueError("Unknown data kind '%s'" % kind_str)

def _type_band(band_str):
    if band_str in ["NA", "None", "none"]:
        return NOT_APPLICABLE
    return band_str

def _bits_to_etype(bits_str):
    if bits_str is None:
        return None

    bits = int(bits_str)

    if bits == 8:
        etype=gdal.GDT_Byte
    elif bits == 16:
        etype=gdal.GDT_UInt16
    else:
        print "Don't know how to handle %d bits" % bits
        print "Defaulting to 16"
        etype=gdal.GDT_UInt16

    return etype

def old_main():
    from polar2grid.core import Workspace
    from argparse import ArgumentParser

    description = """
Create a geotiff from a polar2grid remapped dataset.
"""
    parser = ArgumentParser(description=description)
    parser.add_argument('sat',
            help="name or identifier of the satellite the instrument is on")
    parser.add_argument('instrument',
            help="instrument name")
    parser.add_argument('kind',
            help="kind of band of the data (ex. 'i','m','dnb')")
    parser.add_argument('band',
            help="band identifier (ex. '01','02','NA' for unused)")
    parser.add_argument('data_kind', type=_type_datakind,
            help="kind of the data (reflectance, btemp, radiance, etc)")
    parser.add_argument('geotransform', type=float, nargs=6,
            help="six numbers representing a GDAL GeoTransform, (xorigin, xpixelsize, 0, yorigin, 0, ypixelsize)")
    parser.add_argument('input_filename',
            help="name of the flat binary file to convert into a geotiff")
    parser.add_argument('--start_time', type=_type_dt, default=None, dest="start_time",
            help="Start time of the first scan line, YYYYMMDD_HHMMSS")
    parser.add_argument('--end_time', type=_type_dt, default=None, dest="end_time",
            help="End time of the last scan line, YYYYMMDD_HHMMSS")
    parser.add_argument('--grid_name', default=None, dest="grid_name",
            help="""name of the grid as it appears in grids.conf or any
custom name if proj4_str is provided""")
    parser.add_argument('-p', '--proj4_str', default=None, dest='proj4_str',
            help="Proj4 string of the data, empty if 'grid_name' in grids.conf")
    parser.add_argument('--output_filename', default=None, nargs='?', dest="output_filename",
            help="name of the output geotiff, uses default naming scheme if not entered")
    parser.add_argument('--dtype', type=normalize_dtype_string, default="uint2", dest="data_type",
            help="number of bits in the geotiff, usually unsigned")
    parser.add_argument('--rescale-config', default=None, dest="rescale_config",
            help="alternative rescale configuration file")
    args = parser.parse_args()

    arg_list = []
    kwargs = {}
    print "Satellite Name: ",args.sat
    arg_list.append(args.sat)
    print "Instrument Name: ",args.instrument
    arg_list.append(args.instrument)
    print "Kind: ",args.kind
    arg_list.append(args.kind)
    print "Band: ",args.band
    arg_list.append(args.band)
    print "Data Kind: ",args.data_kind
    arg_list.append(args.data_kind)
    print "Start Time: %s" % args.start_time
    kwargs["start_time"] = args.start_time
    print "End Time: %s" % args.end_time
    kwargs["end_time"] = args.end_time
    print "Grid Name: ",args.grid_name
    kwargs["grid_name"] = args.grid_name

    # Get the proj4 string from the config file
    if args.proj4_str is None:
        raise NotImplementedError("Getting projection information from grids.conf is not implemented yet")
    print "Projection String: ",args.proj4_str
    kwargs["proj4_str"] = args.proj4_str
    print "GeoTransform: %r" % args.geotransform
    print "X Origin: ",args.geotransform[0]
    kwargs["grid_origin_x"] = args.geotransform[0]
    print "X Pixel Size: ",args.geotransform[1]
    kwargs["pixel_size_x"] = args.geotransform[1]
    print "Rotate X: ",args.geotransform[2]
    kwargs["rotate_x"] = args.geotransform[2]
    print "Y Origin: ",args.geotransform[3]
    kwargs["grid_origin_y"] = args.geotransform[3]
    print "Rotate Y: ",args.geotransform[4]
    kwargs["rotate_y"] = args.geotransform[4]
    print "Y Pixel Size: ",args.geotransform[5]
    kwargs["pixel_size_y"] = args.geotransform[5]

    print "Rescaling configuration file: ",args.rescale_config
    rescale_config = args.rescale_config

    print "Input Filename: ",args.input_filename
    W = Workspace('.')
    data = getattr(W, args.input_filename.split('.')[0]).copy()
    arg_list.append(data)
    print "Output Filename: ",args.output_filename

    backend = Backend(data_type=args.data_type, rescale_config=rescale_config)
    return backend.create_product(*arg_list, output_filename=args.output_filename, **kwargs)


def add_backend_argument_groups(parser):
    group = parser.add_argument_group(title="Backend Initialization")
    group.add_argument('--rescale-configs', nargs="*", dest="rescale_configs",
                       help="alternative rescale configuration file")
    group = parser.add_argument_group(title="Backend Output Creation")
    group.add_argument("-o", "--output-pattern", default=DEFAULT_OUTPUT_PATTERN2,
                       help="output filenaming pattern")
    group.add_argument('--dont_inc', dest="inc_by_one", default=True, action="store_false",
                        help="tell rescaler to not increment by one to scaled data can have a 0 fill value (ex. 0-254 -> 1-255 with 0 being fill)")
    return ["Backend Initialization", "Backend Output Creation"]


def main():
    from polar2grid.core.glue_utils import create_basic_parser, create_exc_handler, setup_logging
    parser = create_basic_parser()
    group_titles = add_backend_argument_groups(parser)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sys.exit(main())

