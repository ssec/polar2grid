"""polar2grid backend to take polar-orbitting satellite data arrays
and place it into a geotiff.
"""

from osgeo import gdal
import osr

from .rescale import load_config,rescale,uint16_filter,ubyte_filter
from polar2grid.core.constants import GRIDS_ANY_PROJ4

import os
import sys
import logging

log = logging.getLogger(__name__)

gtiff_driver = gdal.GetDriverByName("GTIFF")

DEF_FN_FORMAT = "%(sat)s_%(instrument)s_%(kindband)s_%(timestamp)s_%(grid_name)s.tif"
DEFAULT_8BIT_RCONFIG="rescale.8bit.conf"
DEFAULT_16BIT_RCONFIG="rescale.16bit.conf"

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

# Meet the interface requirement for backends (part 1)
def can_handle_inputs(sat, instrument, kind, band, data_kind):
    """Function for backend-calling script to ask if the backend
    will be able to handle the data that will be processed.
    For the geotiff backend it can handle any kind or band with a proj4
    projection.

    It is also assumed that rescaling will be able to handle the `data_kind`
    provided.
    """
    return GRIDS_ANY_PROJ4

def create_geotiff(data, output_filename, proj4_str, geotransform,
        etype=gdal.GDT_UInt16):
    """Function that creates a geotiff from the information provided.
    """
    log_level = logging.getLogger('').handlers[0].level or 0
    log.info("Creating geotiff '%s'" % (output_filename,))
    gtiff = gtiff_driver.Create(output_filename,
            data.shape[1], data.shape[0],
            bands=1, eType=etype)
    gtiff.SetGeoTransform(geotransform)
    srs = _proj4_to_srs(proj4_str)
    gtiff.SetProjection(srs.ExportToWkt())
    gtiff_band = gtiff.GetRasterBand(1)

    # Clip data to datatype, otherwise let it go and see what happens
    if etype == gdal.GDT_UInt16:
        data = uint16_filter(data)
    elif etype == gdal.GDT_Byte:
        data = ubyte_filter(data)
    if log_level <= logging.DEBUG:
        log.debug("Data min: %f, max: %f" % (data.min(),data.max()))

    # Write the data
    if gtiff_band.WriteArray(data) != 0:
        log.error("Could not write band 1 data to geotiff '%s'" % (output_filename,))
        raise ValueError("Could not write band 1 data to geotiff '%s'" % (output_filename,))
    # Garbage collection/destructor should close the file properly

# Meet the interface requirement for backends (part 2)
def backend(sat, instrument, kind, band, data_kind, data,
        start_time=None, end_time=None, grid_name=None,
        proj4_str=None, grid_origin_x=None, grid_origin_y=None,
        pixel_size_x=None, pixel_size_y=None,
        output_filename=None, etype=None,
        rotate_x=0, rotate_y=0, rescale_config=None):
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
        - etype (not part of the backend interface):
            Specify the GDAL data type of the produced geotiff. Default 16bit
            unsigned integers.

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
        - rescale_config:
            Rescaling configuration file to be used in scaling the data

    Unused keywords:
        None
    """
    if etype is None:
        etype = gdal.GDT_UInt16

    # Use predefined rescaling configurations if we weren't told what to do
    if rescale_config is None:
        if etype == gdal.GDT_UInt16:
            rescale_config = DEFAULT_16BIT_RCONFIG
        elif etype == gdal.GDT_Byte:
            rescale_config = DEFAULT_8BIT_RCONFIG
    # Load the rescaling configuration, uses the default otherwise
    if rescale_config is not None:
        load_config(rescale_config)

    # Create the filename if it wasn't provided
    if output_filename is None:
        # don't include band if its not applicable
        kindband = "%s%s" % (kind,band or "")
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        if end_time: timestamp += "_" + end_time.strftime("%Y%m%d_%H%M%S")
        output_filename = DEF_FN_FORMAT % dict(
                sat=sat,
                instrument=instrument,
                kindband=kindband,
                timestamp=timestamp,
                grid_name=grid_name
                )

    # Rescale the data based on the configuration that was loaded earlier
    rescale(sat, instrument, kind, band, data_kind, data, config=rescale_config)

    # Create the geotiff
    geotransform = (grid_origin_x, pixel_size_x, rotate_x, grid_origin_y, rotate_y, pixel_size_y)
    create_geotiff(data, output_filename, proj4_str, geotransform, etype=etype)

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

def main():
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
    parser.add_argument('--bits', type=_bits_to_etype, default=16, dest="etype",
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
    kwargs["rescale_config"] = args.rescale_config

    print "Input Filename: ",args.input_filename
    W = Workspace('.')
    data = getattr(W, args.input_filename.split('.')[0]).copy()
    # XXX Remove this once scaling is added to the backend
    #from polar2grid.rescale import sqrt_scale
    #data = sqrt_scale(data)
    arg_list.append(data)
    print "Output Filename: ",args.output_filename

    return backend(*arg_list, output_filename=args.output_filename, etype=args.etype, **kwargs)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sys.exit(main())

