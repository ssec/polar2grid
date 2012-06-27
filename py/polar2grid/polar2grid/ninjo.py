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

from polar2grid.tiff import tag_array,add_tags,TIFFFieldInfo,TIFFDataType,FIELD_CUSTOM,write_list,read_list
from libtiff import libtiff_ctypes as lc
from libtiff import TIFF

import os
import sys
import logging
import ctypes

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
ninjo_tags.append(TIFFFieldInfo(40005, 2, 2, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "HeaderVersion"))
ninjo_tags.append(TIFFFieldInfo(40006, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "Filename"))
ninjo_tags.append(TIFFFieldInfo(40007, 4, 4, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "DataType"))
ninjo_tags.append(TIFFFieldInfo(40008, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "SatelliteNumber"))
ninjo_tags.append(TIFFFieldInfo(40009, 2, 2, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "ColorDepth"))
ninjo_tags.append(TIFFFieldInfo(40010, 4, 4, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "DataSource"))
ninjo_tags.append(TIFFFieldInfo(40011, 6, 6, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "XMinimum"))
ninjo_tags.append(TIFFFieldInfo(40012, 6, 6, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "XMaximum"))
ninjo_tags.append(TIFFFieldInfo(40013, 6, 6, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "YMinimum"))
ninjo_tags.append(TIFFFieldInfo(40014, 6, 6, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "YMaximum"))
ninjo_tags.append(TIFFFieldInfo(40015, 4, 4, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "Projection")) # Always 4 long
ninjo_tags.append(TIFFFieldInfo(40016, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "MeridianWest"))
ninjo_tags.append(TIFFFieldInfo(40017, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "MeridianEast"))
ninjo_tags.append(TIFFFieldInfo(40018, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "EarthRadiusLarge"))
ninjo_tags.append(TIFFFieldInfo(40019, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "EarthRadiusSmall"))

ninjo_tags.append(TIFFFieldInfo(40020, 20, 20, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "GeodeticDate"))
ninjo_tags.append(TIFFFieldInfo(40021, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "ReferenceLatitude1"))
ninjo_tags.append(TIFFFieldInfo(40022, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "ReferenceLatitude2"))
ninjo_tags.append(TIFFFieldInfo(40023, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "CentralMeridian"))
ninjo_tags.append(TIFFFieldInfo(40024, 10, 10, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "PhysicValue"))
ninjo_tags.append(TIFFFieldInfo(40025, 10, 10, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "PhysicUnit"))
ninjo_tags.append(TIFFFieldInfo(40026, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "MinGrayValue"))
ninjo_tags.append(TIFFFieldInfo(40027, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "MaxGrayValue"))
ninjo_tags.append(TIFFFieldInfo(40028, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "Gradient"))
ninjo_tags.append(TIFFFieldInfo(40029, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "AxisIntercept"))
ninjo_tags.append(TIFFFieldInfo(40030, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "ColorTable"))
ninjo_tags.append(TIFFFieldInfo(40031, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "Description"))
ninjo_tags.append(TIFFFieldInfo(40032, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "OverflightDirection"))
ninjo_tags.append(TIFFFieldInfo(40033, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "GeoLatitude"))
ninjo_tags.append(TIFFFieldInfo(40034, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "GeoLongitude"))
ninjo_tags.append(TIFFFieldInfo(40035, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "Altitude"))
ninjo_tags.append(TIFFFieldInfo(40036, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "AOSAzimuth"))
ninjo_tags.append(TIFFFieldInfo(40037, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "LOSAzimuth"))
ninjo_tags.append(TIFFFieldInfo(40038, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "MaxElevation"))
ninjo_tags.append(TIFFFieldInfo(40039, 8, 8, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "OverFlightTime"))
ninjo_tags.append(TIFFFieldInfo(40040, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "IsBlackLinesCorrection"))
ninjo_tags.append(TIFFFieldInfo(40041, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "IsAtmosphereCorrected"))
ninjo_tags.append(TIFFFieldInfo(40042, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "IsCalibrated"))
ninjo_tags.append(TIFFFieldInfo(40043, 1, 1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "IsNormalized"))
ninjo_tags.append(TIFFFieldInfo(40044, 256, 256, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "OriginalHeader"))
#ninjo_tags.append(TIFFFieldInfo(40045, -1, -1, TIFFDataType.TIFF_SLONG, FIELD_CUSTOM, True, False, "IsValueTableAvailable"))
#ninjo_tags.append(TIFFFieldInfo(40046, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "ValueTableStringField"))
#ninjo_tags.append(TIFFFieldInfo(40047, -1, -1, TIFFDataType.TIFF_FLOAT, FIELD_CUSTOM, True, False, "ValueTableFloatField"))

#ninjo_tags_struct = tag_array(1)(ninjo_tags[3])
ninjo_tags_struct = tag_array(len(ninjo_tags))(*ninjo_tags)
ninjo_extension = add_tags(ninjo_tags_struct)

def from_proj4(proj4_str):
    proj4_elements = proj4_str.split(" ")
    proj4_dict = dict([ y.split("=") for y in [ x.strip("+") for x in proj4_elements ] ])
    return proj4_dict

def to_proj4(proj4_dict):
    """Convert a dictionary of proj4 parameters back into a proj4 string.

    >>> proj4_str = "+proj=lcc +a=123456 +b=12345"
    >>> proj4_dict = from_proj4(proj4_str)
    >>> new_proj4_str = to_proj4(proj4_dict)
    >>> assert(new_proj4_str == proj4_str)
    """
    # Make sure 'proj' is first, some proj4 parsers don't accept it otherwise
    proj4_str = "+proj=%s" % proj4_dict.pop("proj")
    proj4_str = proj4_str + " " + " ".join(["+%s=%s" % (k,v) for k,v in proj4_dict.items()])
    return proj4_str

def create_ninjo_tiff(image_data, output_fn, **kwargs):
    pass

def SetField(t, value):
    """ Set TIFF field value with tag.

    tag can be numeric constant TIFFTAG_<tagname> or a
    string containing <tagname>.
    """
    data = ctypes.c_char_p(value)
    before_args = lc.libtiff.TIFFSetField.argtypes
    lc.libtiff.TIFFSetField.argtypes = lc.libtiff.TIFFSetField.argtypes[:-1] + [ctypes.c_uint32, ctypes.c_char_p]
    r = lc.libtiff.TIFFSetField(t, 40000, 2, data)
    lc.libtiff.TIFFSetField.argtypes = before_args
    return r

def test_write_tags(*args):
    """Create a sample NinJo file that writes all ninjo tags and a fake data
    array to a new tiff file.
    """
    if len(args) == 0:
        tiff_fn = "test_ninjo.tif"
    else:
        tiff_fn = args[0]

    import numpy
    # Represents original high resolution data array
    #data_array = numpy.zeros((5,5), dtype=numpy.uint8)
    data_array = numpy.zeros((2500,2500), dtype=numpy.uint8)

    # Open file
    tiff_file = TIFF.open(tiff_fn, "w")
    tiff_file.SetDirectory(0)

    ### Write first set of tags ###
    print "ModelTiePoint"
    tiff_file.SetField("ModelTiePoint", write_list([1,2,3,4,5,6], ctypes.c_double))
    print "ModelPixelScale"
    tiff_file.SetField("ModelPixelScale", write_list([1,2], ctypes.c_double))
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
    tiff_file.SetField("HeaderVersion", write_list([1,2], ctypes.c_int32))
    print "Filename"
    tiff_file.SetField("Filename", "a_fake_satellite_file.h5")
    print "DataType"
    tiff_file.SetField("DataType", "PORN")
    print "SatelliteNumber"
    tiff_file.SetField("SatelliteNumber", "7") #?
    print "ColorDepth"
    tiff_file.SetField("ColorDepth", write_list([8,8], ctypes.c_int32))
    print "DataSource"
    tiff_file.SetField("DataSource", "PDUS")
    print "XMinimum"
    tiff_file.SetField("XMinimum", write_list([0,1,2,3,4,5], ctypes.c_int32))
    print "XMaximum"
    tiff_file.SetField("XMaximum", write_list([5,4,3,2,1,0], ctypes.c_int32))
    print "YMinimum"
    tiff_file.SetField("YMinimum", write_list([0,1,2,3,4,5], ctypes.c_int32))
    print "YMaximum"
    tiff_file.SetField("YMaximum", write_list([5,4,3,2,1,0], ctypes.c_int32))
    print "Projection"
    tiff_file.SetField("Projection", "NPOL")
    print "MeridianWest"
    tiff_file.SetField("MeridianWest", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "MeridianEast"
    tiff_file.SetField("MeridianEast", write_list([0,1,2,3,4,5,6,7], ctypes.c_float))
    print "EarthRadiusLarge"
    tiff_file.SetField("EarthRadiusLarge", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "EarthRadiusSmall"
    tiff_file.SetField("EarthRadiusSmall", write_list([0,1,2,3,4,5,6,7], ctypes.c_float))

    ### Write second set of tags ###
    print "GeodeticDate"
    tiff_file.SetField("GeodeticDate", "wgs84")
    print "ReferenceLatitude1"
    tiff_file.SetField("ReferenceLatitude1", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "ReferenceLatitude2"
    tiff_file.SetField("ReferenceLatitude2", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "CentralMeridian"
    tiff_file.SetField("CentralMeridian", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "PhysicValue"
    tiff_file.SetField("PhysicValue", "T")
    print "PhysicUnit"
    tiff_file.SetField("PhysicUnit", "CELSIUS")
    print "MinGrayValue"
    tiff_file.SetField("MinGrayValue", 0)
    print "MaxGrayValue"
    tiff_file.SetField("MaxGrayValue", 255)
    print "Gradient"
    tiff_file.SetField("Gradient", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "AxisIntercept"
    tiff_file.SetField("AxisIntercept", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "ColorTable"
    tiff_file.SetField("ColorTable", "some color table")
    print "Description"
    tiff_file.SetField("Description", "this is a fake/test/sample ninjo tiff file")
    print "OverflightDirection"
    tiff_file.SetField("OverflightDirection", "S")
    print "GeoLatitude"
    tiff_file.SetField("GeoLatitude", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "GeoLongitude"
    tiff_file.SetField("GeoLongitude", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "Altitude"
    tiff_file.SetField("Altitude", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "AOSAzimuth"
    tiff_file.SetField("AOSAzimuth", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "LOSAzimuth"
    tiff_file.SetField("LOSAzimuth", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "MaxElevation"
    tiff_file.SetField("MaxElevation", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
    print "OverFlightTime"
    tiff_file.SetField("OverFlightTime", write_list([7,6,5,4,3,2,1,0], ctypes.c_float))
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

    import numpy
    # Represents original high resolution data array
    data_array = numpy.zeros((2500,2500), dtype=numpy.uint8)

    # Open file
    tiff_file = TIFF.open(tiff_fn, "w")

    ### Write first directory and tags ###
    tiff_file.SetDirectory(0)
    tiff_file.SetField("ModelTiePoint", write_list([0.0, 0.0, 0.0, -164.874313, 89.874321, 0.0], ctypes.c_double))
    tiff_file.write_image(data_array)

    ### Directory 2 ###
    tiff_file.SetDirectory(1)
    tiff_file.SetField("ModelTiePoint", write_list([0.0, 0.0, 0.0, -164.838348, 89.838341, 0.0], ctypes.c_double))
    tiff_file.write_image(data_array[::2, ::2])

    return 0

def test_read(*args):
    pass

TESTS = {
    "test_write" : test_write,
    "test_read" : test_read,
    "test_write_tags" : test_write_tags
    }
def main():
    from polar2grid.core import Workspace # used to import image data
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

