#!/usr/bin/env python
# encoding: utf-8
"""Module to provide the NinJo backend to a polar2grid chain.  This module
takes reprojected image data and other parameters required by NinJo and
places them correctly in to the modified geotiff format accepted by NinJo.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         June 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from polar2grid.core import Workspace,utc_now
from polar2grid.core.constants import DKIND_RADIANCE,DKIND_REFLECTANCE,DKIND_BTEMP,DKIND_FOG
from polar2grid import libtiff
from polar2grid.libtiff import TIFF,TIFFFieldInfo,TIFFDataType,FIELD_CUSTOM,add_tags
from polar2grid.rescale import unlinear_scale,ubyte_filter
import numpy

import os
import sys
import logging
import calendar

log = logging.getLogger(__name__)

ninjo_tags = []
ninjo_tags.append(TIFFFieldInfo(33922, 6, 6, TIFFDataType.TIFF_DOUBLE, FIELD_CUSTOM, True, False, "ModelTiePoint"))
ninjo_tags.append(TIFFFieldInfo(33550, 2, 2, TIFFDataType.TIFF_DOUBLE, FIELD_CUSTOM, True, False, "ModelPixelScale"))
ninjo_tags.append(TIFFFieldInfo(50000, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "TransparentPixel"))

ninjo_tags.append(TIFFFieldInfo(40000, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "NinjoName")) # Not in spreadsheet, but in files
ninjo_tags.append(TIFFFieldInfo(40001, 1, 1, TIFFDataType.TIFF_LONG, FIELD_CUSTOM, True, False, "SatelliteNameID"))
ninjo_tags.append(TIFFFieldInfo(40002, 1, 1, TIFFDataType.TIFF_LONG, FIELD_CUSTOM, True, False, "DateID"))
ninjo_tags.append(TIFFFieldInfo(40003, 1, 1, TIFFDataType.TIFF_LONG, FIELD_CUSTOM, True, False, "CreationDateID"))
ninjo_tags.append(TIFFFieldInfo(40004, 1, 1, TIFFDataType.TIFF_LONG, FIELD_CUSTOM, True, False, "ChannelID"))
ninjo_tags.append(TIFFFieldInfo(40005, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "HeaderVersion"))
ninjo_tags.append(TIFFFieldInfo(40006, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "Filename"))
ninjo_tags.append(TIFFFieldInfo(40007, 5, 5, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "DataType")) # 4 chars + NUL character
ninjo_tags.append(TIFFFieldInfo(40008, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "SatelliteNumber"))
ninjo_tags.append(TIFFFieldInfo(40009, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "ColorDepth"))
ninjo_tags.append(TIFFFieldInfo(40010, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "DataSource"))
ninjo_tags.append(TIFFFieldInfo(40011, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "XMinimum"))
ninjo_tags.append(TIFFFieldInfo(40012, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "XMaximum"))
ninjo_tags.append(TIFFFieldInfo(40013, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "YMinimum"))
ninjo_tags.append(TIFFFieldInfo(40014, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "YMaximum"))
ninjo_tags.append(TIFFFieldInfo(40015, 5, 5, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "Projection")) # Always 4 long + NUL character
ninjo_tags.append(TIFFFieldInfo(40016, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "MeridianWest"))
ninjo_tags.append(TIFFFieldInfo(40017, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "MeridianEast"))
ninjo_tags.append(TIFFFieldInfo(40018, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "EarthRadiusLarge"))
ninjo_tags.append(TIFFFieldInfo(40019, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "EarthRadiusSmall"))

ninjo_tags.append(TIFFFieldInfo(40020, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "GeodeticDate")) # Max 20
ninjo_tags.append(TIFFFieldInfo(40021, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "ReferenceLatitude1"))
ninjo_tags.append(TIFFFieldInfo(40022, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "ReferenceLatitude2"))
ninjo_tags.append(TIFFFieldInfo(40023, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "CentralMeridian"))
ninjo_tags.append(TIFFFieldInfo(40024, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "PhysicValue")) # Max 10
ninjo_tags.append(TIFFFieldInfo(40025, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "PhysicUnit")) # Max 10
ninjo_tags.append(TIFFFieldInfo(40026, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "MinGrayValue"))
ninjo_tags.append(TIFFFieldInfo(40027, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "MaxGrayValue"))
ninjo_tags.append(TIFFFieldInfo(40028, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "Gradient"))
ninjo_tags.append(TIFFFieldInfo(40029, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "AxisIntercept"))
ninjo_tags.append(TIFFFieldInfo(40030, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "ColorTable"))
ninjo_tags.append(TIFFFieldInfo(40031, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "Description"))
ninjo_tags.append(TIFFFieldInfo(40032, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "OverflightDirection"))
ninjo_tags.append(TIFFFieldInfo(40033, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "GeoLatitude"))
ninjo_tags.append(TIFFFieldInfo(40034, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "GeoLongitude"))
ninjo_tags.append(TIFFFieldInfo(40035, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "Altitude"))
ninjo_tags.append(TIFFFieldInfo(40036, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "AOSAzimuth"))
ninjo_tags.append(TIFFFieldInfo(40037, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "LOSAzimuth"))
ninjo_tags.append(TIFFFieldInfo(40038, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "MaxElevation"))
ninjo_tags.append(TIFFFieldInfo(40039, 1, 1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "OverFlightTime"))
ninjo_tags.append(TIFFFieldInfo(40040, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "IsBlackLinesCorrection"))
ninjo_tags.append(TIFFFieldInfo(40041, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "IsAtmosphereCorrected"))
ninjo_tags.append(TIFFFieldInfo(40042, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "IsCalibrated"))
ninjo_tags.append(TIFFFieldInfo(40043, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "IsNormalized"))
ninjo_tags.append(TIFFFieldInfo(40044, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "OriginalHeader")) # Max 256
#ninjo_tags.append(TIFFFieldInfo(40045, -1, -1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "IsValueTableAvailable"))
#ninjo_tags.append(TIFFFieldInfo(40046, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "ValueTableStringField"))
#ninjo_tags.append(TIFFFieldInfo(40047, -1, -1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "ValueTableFloatField"))

ninjo_extension = add_tags(ninjo_tags)

dkind2physical = {
        DKIND_RADIANCE : ("\0", "\0"),
        DKIND_REFLECTANCE : ("ALBEDO", "%"),
        DKIND_BTEMP : ("T", "CELSIUS")
        #DKIND_FOG : ("T", "CELSIUS")
        }

dkind2grad = {
        DKIND_RADIANCE : (1.0, 0.0),
        DKIND_REFLECTANCE : (0.490196,0.0),
        DKIND_BTEMP : (-0.5, 0.0)
        #DKIND_FOG : (-0.5, 0.0)
        }

def get_default_lw_colortable():
    # Long wave or SVI04 or SVI05 or brightness temp
    cmap = [
        1,6,10,13,16,19,21,23,25,27,29,31,33,35,37,39,40,42,44,45,47,48,50,
        51,53,54,56,57,58,60,61,63,64,65,67,68,69,70,72,73,74,75,
        77,78,79,80,81,83,84,85,86,87,88,89,91,92,93,94,95,96,97,98,99,100,
        101,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,
        125,126,127,128,129,130,131,132,133,134,135,136,137,138,138,139,140,141,142,143,144,145,146,146,147,
        148,149,150,151,152,153,153,154,155,156,157,158,159,159,160,161,162,
        163,164,164,165,166,167,168,169,169,170,171,172,173,173,174,175,176,
        177,177,178,179,180,181,181,182,183,184,185,185,186,187,188,188,189,
        190,191,192,192,193,194,195,195,196,197,198,198,199,200,201,201,202,203,
        204,204,205,206,207,207,208,209,210,210,211,212,213,213,214,215,215,216,217,
        218,218,219,220,220,221,222,223,223,224,225,225,226,227,228,228,229,230,230,
        231,232,232,233,234,235,235,236,237,237,238,239,239,240,241,241,242,243,244,
        244,245,246,246,247,248,248,249,250,250,251,252,252,253,254,254,255
    ]
    cmap = [cmap]*3
    return cmap

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
            image data, such as DKIND_REFLECTANCE or DKIND_BTEMP. This is optional,
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
        data_type : str
            NinJo specific data type
                data_type[0] = P (polar) or G (geostat)
                data_type[1] = O (original) or P (product)
                data_type[2:4] = RN or RB or RA or RN or AN (Raster, Bufr, ASCII, NIL)
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
    log.info("Creating output file '%s'" % (output_fn,))
    out_tiff = TIFF.open(output_fn, "w")

    if image_data.dtype != numpy.uint8:
        log.warning("NinJo image data must be uint8, converting...")
        image_data = image_data.astype(numpy.uint8)

    # Extract keyword arguments
    data_kind = kwargs.pop("data_kind", None) # called as a backend
    if data_kind is not None and (data_kind not in dkind2physical or data_kind not in dkind2grad):
        # Must do the check here since it matters when pulling out physic value
        log.warning("'data_kind' is not known to the ninjo tiff creator, it will be ignored")
        data_kind = None
    cmap = kwargs.pop("cmap", None)
    sat_id = int(kwargs.pop("sat_id"))
    chan_id = int(kwargs.pop("chan_id"))
    data_source = str(kwargs.pop("data_source"))
    tile_width = int(kwargs.pop("tile_width", 512))
    tile_length = int(kwargs.pop("tile_length", 512))
    data_type = str(kwargs.pop("data_type", "PORN"))
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
        if data_kind == DKIND_BTEMP or data_kind == DKIND_FOG:
            cmap = get_default_lw_colortable()
        else:
            cmap = get_default_sw_colortable()
    elif len(cmap) != 3:
        log.error("Colormap (cmap) must be a list of 3 lists (RGB), not %d" % len(cmap))

    if len(data_type) != 4:
        log.error("NinJo data type must be 4 characters")
        raise ValueError("NinJo data type must be 4 characters")
    if data_type[0] not in ["P", "G"]:
        log.error("NinJo data type's first character must be 'P' or 'G' not '%s'" % data_type[0])
        raise ValueError("NinJo data type's first character must be 'P' or 'G' not '%s'" % data_type[0])
    if data_type[1] not in ["O", "P"]:
        log.error("NinJo data type's second character must be 'O' or 'P' not '%s'" % data_type[1])
        raise ValueError("NinJo data type's second character must be 'O' or 'P' not '%s'" % data_type[1])
    if data_type[2:4] not in ["RN","RB","RA","BN","AN"]:
        log.error("NinJo data type's last 2 characters must be one of %s not '%s'" % ("['RN','RB','RA','BN','AN']", data_type[2:4]))
        raise ValueError("NinJo data type's last 2 characters must be one of %s not '%s'" % ("['RN','RB','RA','BN','AN']", data_type[2:4]))

    if description is not None and len(description) >= 1000:
        log.error("NinJo description must be less than 1000 characters")
        raise ValueError("NinJo description must be less than 1000 characters")

    file_dt = utc_now()
    file_epoch = calendar.timegm(file_dt.timetuple())
    image_epoch = calendar.timegm(image_dt.timetuple())

    def _write_oneres(image_data, pixel_xres, pixel_yres, subfile=False):
        log.info("Writing tag data for a resolution of the output file '%s'" % (output_fn,))

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
        out_tiff.SetField("DataType", data_type)
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

    log.info("Successfully created a NinJo tiff file: '%s'" % (output_fn,))

    return

def scale_data(image_data, data_kind, *args, **kwargs):
    kwargs["fill_out"] = 0
    if "fill" in kwargs:
        kwargs["fill_in"] = kwargs["fill"]

    if data_kind == DKIND_REFLECTANCE:
        # Extra 100 to turn reflectance 0-1 into albedo
        return unlinear_scale(image_data, 0.490196/100.0, 0, *args, **kwargs)
    elif data_kind == DKIND_RADIANCE:
        return unlinear_scale(image_data, 1/255.0, 0, *args, **kwargs)
    elif data_kind == DKIND_BTEMP:
        # Extra 273.15 to convert to C from K
        return unlinear_scale(image_data, -0.5, 40+273.15, *args, **kwargs)
    elif data_kind == DKIND_FOG:
        # Extra 273.15 to convert to C from K
        return unlinear_scale(image_data, -0.5, 40+273.15, *args, **kwargs)
    else:
        log.error("NinJo backend does not know how to scale data of kind %d" % data_kind)
        raise ValueError("NinJo backend does not know how to scale data of kind %d" % data_kind)

def ninjo_backend(input_fn, output_fn, **kwargs):
    # Extract keyword arguments
    try:
        kind = kwargs["kind"]
        band = kwargs["band"]
        data_kind = kwargs["data_kind"]
    except KeyError:
        log.error("Couldn't get required keyword for ninjo backend")
        raise

    try:
        W = Workspace(".")
        image_attr = os.path.split(input_fn)[1].split('.')[0]
        image_data = getattr(W, image_attr)
        image_data = image_data.copy()
    except StandardError:
        log.error("Could not open input file %s" % input_fn)
        raise

    try:
        rescaled_data = scale_data(image_data,
                **kwargs)
        log.debug("Data min: %f, Data max: %f" % (rescaled_data.min(), rescaled_data.max()))
    except StandardError:
        log.error("Unexpected error while rescaling data")
        raise

    log.info("Clipping the scaled data to a 0 - 255 range")
    rescaled_data = ubyte_filter(rescaled_data)

    return create_ninjo_tiff(rescaled_data, output_fn, **kwargs)

def test_write_tags(*args):
    """Create a sample NinJo file that writes all ninjo tags and a fake data
    array to a new tiff file.
    """
    if len(args) == 0:
        tiff_fn = "test_ninjo.tif"
    else:
        tiff_fn = args[0]

    # Represents original high resolution data array
    #data_array = numpy.zeros((5,5), dtype=numpy.uint8)
    data_array = numpy.zeros((2500,2500), dtype=numpy.uint8)

    # Open file
    tiff_file = TIFF.open(tiff_fn, "w")
    tiff_file.SetDirectory(0)

    ### Write first set of tags ###
    print "ModelTiePoint"
    tiff_file.SetField("ModelTiePoint", [1,2,3,4,5,6])
    print "ModelPixelScale"
    tiff_file.SetField("ModelPixelScale", [1,2])
    print "TransparentPixel"
    tiff_file.SetField("TransparentPixel", 1)
    print "NinjoName"
    tiff_file.SetField("NinjoName", "NINJO")
    print "SatelliteNameID"
    tiff_file.SetField("SatelliteNameID", 1234)
    print "DateID"
    tiff_file.SetField("DateID", 1234)
    print "CreationDateID"
    tiff_file.SetField("CreationDateID", 1234)
    print "ChannelID"
    tiff_file.SetField("ChannelID", 1234)
    print "HeaderVersion"
    tiff_file.SetField("HeaderVersion", 2)
    print "Filename"
    tiff_file.SetField("Filename", "a_fake_satellite_file.h5")
    print "DataType"
    tiff_file.SetField("DataType", "PORN")
    print "SatelliteNumber"
    tiff_file.SetField("SatelliteNumber", "7") #?
    print "ColorDepth"
    tiff_file.SetField("ColorDepth", 8)
    print "DataSource"
    tiff_file.SetField("DataSource", "PDUS")
    print "XMinimum"
    tiff_file.SetField("XMinimum", 0)
    print "XMaximum"
    tiff_file.SetField("XMaximum", 2500)
    print "YMinimum"
    tiff_file.SetField("YMinimum", 0)
    print "YMaximum"
    tiff_file.SetField("YMaximum", 2500)
    print "Projection"
    tiff_file.SetField("Projection", "NPOL")
    print "MeridianWest"
    tiff_file.SetField("MeridianWest", -180.0)
    print "MeridianEast"
    tiff_file.SetField("MeridianEast", 180.0)
    print "EarthRadiusLarge"
    tiff_file.SetField("EarthRadiusLarge", 6370000.0)
    print "EarthRadiusSmall"
    tiff_file.SetField("EarthRadiusSmall", 6370000.0)

    ### Write second set of tags ###
    print "GeodeticDate"
    tiff_file.SetField("GeodeticDate", "wgs84")
    print "ReferenceLatitude1"
    tiff_file.SetField("ReferenceLatitude1", 45.0)
    print "ReferenceLatitude2"
    tiff_file.SetField("ReferenceLatitude2", 45.0)
    print "CentralMeridian"
    tiff_file.SetField("CentralMeridian", 0.0)
    print "PhysicValue"
    tiff_file.SetField("PhysicValue", "T")
    print "PhysicUnit"
    tiff_file.SetField("PhysicUnit", "CELSIUS")
    print "MinGrayValue"
    tiff_file.SetField("MinGrayValue", 0)
    print "MaxGrayValue"
    tiff_file.SetField("MaxGrayValue", 255)
    print "Gradient"
    tiff_file.SetField("Gradient", 5.0)
    print "AxisIntercept"
    tiff_file.SetField("AxisIntercept", 0.0)
    print "ColorTable"
    tiff_file.SetField("ColorTable", "some color table")
    print "Description"
    tiff_file.SetField("Description", "this is a fake/test/sample ninjo tiff file")
    print "OverflightDirection"
    tiff_file.SetField("OverflightDirection", "S")
    print "GeoLatitude"
    tiff_file.SetField("GeoLatitude", 0.0)
    print "GeoLongitude"
    tiff_file.SetField("GeoLongitude", 0.0)
    print "Altitude"
    tiff_file.SetField("Altitude", 10000.0)
    print "AOSAzimuth"
    tiff_file.SetField("AOSAzimuth", 180.0)
    print "LOSAzimuth"
    tiff_file.SetField("LOSAzimuth", 180.0)
    print "MaxElevation"
    tiff_file.SetField("MaxElevation", 45.0)
    print "OverFlightTime"
    tiff_file.SetField("OverFlightTime", 1000.0)
    print "IsBlackLinesCorrection"
    tiff_file.SetField("IsBlackLinesCorrection", 0)
    print "IsAtmosphereCorrected"
    tiff_file.SetField("IsAtmosphereCorrected", 0)
    print "IsCalibrated"
    tiff_file.SetField("IsCalibrated", 0)
    print "IsNormalized"
    tiff_file.SetField("IsNormalized", 0)
    print "OriginalHeader"
    tiff_file.SetField("OriginalHeader", "some header")
    #print "IsValueTableAvailable"
    #tiff_file.SetField("IsValueTableAvailable", 0)
    #print "ValueTableStringField"
    #tiff_file.SetField("ValueTableStringField", "Cirrus")
    #print "ValueTableFloatField"
    #tiff_file.SetField("ValueTableFloatField", 0)

    print "Writing image data..."
    tiff_file.write_image(data_array)
    print "SUCCESS"

def test_read_tags(*args):
    if len(args) == 0:
        tiff_fn = "test_ninjo.tif"
    else:
        tiff_fn = args[0]

    if not os.path.exists(tiff_fn):
        log.error("TIFF input file %s doesn't exists" % (tiff_fn,))
        return -1

    a = TIFF.open(tiff_fn, "r")

    image = a.read_image()
    print "Image data has shape %r" % (image.shape,)
    print "Tag %s: %s" % ("ModelTiePoint", a.GetField("ModelTiePoint"))

def test_write(*args):
    """Recreate a simple NinJo compatible tiff file from an original
    GOESE example.

    Mainly a test of the tags.
    """
    if len(args) == 0:
        tiff_fn = "test_ninjo.tif"
    else:
        tiff_fn = args[0]

    # Represents original high resolution data array
    #data_array = numpy.zeros((2500,2500), dtype=numpy.uint8)
    data_array = numpy.tile(range(500), (2500,5)).astype(numpy.uint8)
    print data_array.shape

    # Open file
    tiff_file = TIFF.open(tiff_fn, "w")

    ### Write first directory and tags ###
    tiff_file.SetDirectory(0)
    tiff_file.SetField("ImageWidth", 2500)
    tiff_file.SetField("ImageLength", 2500)
    tiff_file.SetField("BITspersample", 8)
    tiff_file.SetField("compression", libtiff.COMPRESSION_LZW)
    #FIXME: Sample file used colormap
    #tiff_file.SetField("PHOTOMETRIC", libtiff.PHOTOMETRIC_MINISBLACK)
    tiff_file.SetField("PHOTOMETRIC", libtiff.PHOTOMETRIC_PALETTE)
    tiff_file.SetField("ORIENTATION", libtiff.ORIENTATION_TOPLEFT)
    tiff_file.SetField("SamplesPerPixel", 1)
    tiff_file.SetField("SMinSampleValue", 0)
    tiff_file.SetField("SMaxsampleValue", 255)
    tiff_file.SetField("Planarconfig", libtiff.PLANARCONFIG_CONTIG)
    #tiff_file.SetField("ColorMap", [ [ x*256 for x in range(256) ],[0]*256,[0]*256 ])
    tiff_file.SetField("ColorMap", [[ x*256 for x in range(256) ]]*3)
    tiff_file.SetField("TILEWIDTH", 512)
    tiff_file.SetField("TILELENGTH", 512)
    tiff_file.SetField("sampleformat", libtiff.SAMPLEFORMAT_UINT)

    ### NINJO SPECIFIC ###
    tiff_file.SetField("ModelPixelScale", [0.071957,0.071957])
    tiff_file.SetField("ModelTiePoint", [0.0, 0.0, 0.0, -164.874313, 89.874321, 0.0])
    tiff_file.SetField("NinjoName", "NINJO")
    tiff_file.SetField("SatelliteNameID", 7300014)
    tiff_file.SetField("DateID", 1337169600)
    tiff_file.SetField("CreationDateID", 1337171130)
    tiff_file.SetField("ChannelID", 900015)
    tiff_file.SetField("HeaderVersion", 2)
    tiff_file.SetField("FileName", "GOESE_AMERIKA_IR107_nq075W8km_1205161200.tif")
    tiff_file.SetField("DataType", "GORN")
    tiff_file.SetField("SatelliteNumber", "\x00") # Hardcoded to 0
    tiff_file.SetField("ColorDepth", 16) #Um 8? hardcoded to 8, but 16?
    tiff_file.SetField("DataSource", "EUMCAST")
    tiff_file.SetField("XMinimum", 1)
    tiff_file.SetField("XMaximum", 2500)
    tiff_file.SetField("YMinimum", 1)
    tiff_file.SetField("YMaximum", 2500)
    tiff_file.SetField("Projection", "PLAT")
    tiff_file.SetField("MeridianWest", 0.0)
    tiff_file.SetField("MeridianEast", 0.0)
    tiff_file.SetField("EarthRadiusLarge", 6370000.0)
    tiff_file.SetField("EarthRadiusSmall", 6370000.0)
    tiff_file.SetField("GeodeticDate", "\x00") # ---?
    tiff_file.SetField("ReferenceLatitude1", 0.0)
    tiff_file.SetField("ReferenceLatitude2", 0.0)
    tiff_file.SetField("CentralMeridian", -75.000)
    tiff_file.SetField("PhysicValue", "T")
    tiff_file.SetField("PhysicUnit", "CELSIUS")
    tiff_file.SetField("MinGrayValue", 0)
    tiff_file.SetField("MaxGrayValue", 255)
    tiff_file.SetField("Gradient", -0.5)
    tiff_file.SetField("AxisIntercept", 40.0)
    tiff_file.SetField("Altitude", 42164.0)
    tiff_file.SetField("IsCalibrated", 1)
    tiff_file.SetField("IsNormalized", 0)

    tiff_file.write_tiles(data_array)
    tiff_file.WriteDirectory()

    ### Directory 2 ###
    #tiff_file.SetDirectory(1)
    #tiff_file.SetField("ModelTiePoint", write_list([0.0, 0.0, 0.0, -164.838348, 89.838341, 0.0], ctypes.c_double))
    #tiff_file.write_image(data_array[::2, ::2])

    return 0

def test_read(*args):
    pass

TESTS = {
    "test_write" : test_write,
    "test_read" : test_read,
    "test_write_tags" : test_write_tags
    }
def main():
    import optparse
    usage = "%prog [options] <fbf image file> <quoted proj4 string> <output tiff name>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--debug", dest="show_debug", action="store_true", default=False,
            help="Show additional debug messages")
    parser.add_option("-t", "--test", dest="run_test", default=None,
            help="Run specified test [test_write, test_read, etc]")
    options,args = parser.parse_args()

    if options.show_debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    if options.run_test is not None:
        if options.run_test not in TESTS:
            parser.print_usage()
            print "Available tests:\n\t%s" % ("\n\t".join(TESTS.keys()))
            return -1
        return TESTS[options.run_test](*args)

    if len(args) == 3:
        image_fn = args[0]
        proj4_str = args[1]
        tiff_fn = args[2]
    else:
        parser.print_usage()
        return -1

    # Get the image data to be put into the ninjotiff
    W = Workspace(".")
    image_data = getattr(W, image_fn.split(".")[0])

    # Create the ninjotiff
    create_ninjo_tiff(image_data, tiff_fn, proj4_dict=from_proj4(proj4_str))

if __name__ == "__main__":
    sys.exit(main())

