"""polar2grid backend to take polar-orbitting satellite data arrays
and place it into a geotiff.
"""

from osgeo import gdal
import osr

import os
import sys
import logging

log = logging.getLogger(__name__)

gtiff_driver = gdal.GetDriverByName("GTIFF")

DEF_FN_FORMAT = "%(sat)s_%(instrument)s_%(kindband)s_%(st)s_%(grid_name)s.tif"

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

# XXX: Needs a real name
# Meet the interface requirement for backends (part 1)
def can_handle(sat, instrument, kind, band, grid_names):
    """Function for script using the backend to verify that the
    backend will be able to handle the data that will be processed.

    For the geotiff backend it can handle any kind or band, along with the
    assumption that grids are provided via proj4 string.
    """
    return True

# Meet the interface requirement for backends (part 2)
def create_geotiff(data, output_filename, proj4_str, geotransform,
        etype=gdal.GDT_UInt16):
    """Function that creates a geotiff from the information provided.
    """
    log.info("Creating geotiff '%s'" % (output_filename,))
    gtiff = gtiff_driver.Create(output_filename,
            data.shape[1], data.shape[0],
            bands=1, eType=etype)
    gtiff.SetGeoTransform(geotransform)
    srs = _proj4_to_srs(proj4_str)
    gtiff.SetProjection(srs.ExportToWkt())
    gtiff_band = gtiff.GetRasterBand(1)
    if gtiff_band.WriteArray(data) != 0:
        log.error("Could not write band 1 data to geotiff '%s'" % (output_filename,))
        raise ValueError("Could not write band 1 data to geotiff '%s'" % (output_filename,))
    # Garbage collection/destructor should close the file properly

def backend(sat, instrument, kind, band, data_kind, start_time, grid_name,
        proj4_str, grid_origin_x, grid_origin_y, pixel_size_x, pixel_size_y,
        data, output_filename=None, etype=gdal.GDT_UInt16, rotate_x=0, rotate_y=0):
    """Function to be called from a connecting script to interpret the
    information provided and create a geotiff.
    """
    if output_filename is None:
        if band in [None, "", "NA"]:
            kindband = kind
        else:
            kindband = kind + band
        output_filename = DEF_FN_FORMAT % dict(
                sat=sat,
                instrument=instrument,
                kindband=kindband,
                st=start_time.strftime("%Y%m%d_%H%M%S"),
                grid_name=grid_name
                )

    geotransform = (grid_origin_x, pixel_size_x, rotate_x, grid_origin_y, rotate_y, pixel_size_y)
    create_geotiff(data, output_filename, proj4_str, geotransform, etype=etype)

def _type_dt(datestring):
    from datetime import datetime
    return datetime.strptime(datestring, "%Y%m%d_%H%M%S")

def _type_datakind(kind_str):
    from ifg.core import K_REFLECTANCE,K_RADIANCE,K_BTEMP,K_FOG
    kind_str = kind_str.lower()
    if kind_str in ["reflectance"]:
        return K_REFLECTANCE
    elif kind_str in ["radiance"]:
        return K_RADIANCE
    elif kind_str in ["btemp","brightness temperature"]:
        return K_BTEMP
    elif kind_str in ["fog"]:
        return K_FOG
    raise ValueError("Unknown data kind '%s'" % kind_str)

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
    parser.add_argument('start_time', type=_type_dt,
            help="Start time of the first scan line, YYYYMMDD_HHMMSS")
    parser.add_argument('grid_name',
            help="""name of the grid as it appears in grids.conf or any
custom name if proj4_str is provided""")
    parser.add_argument('-p', '--proj4_str', default=None, dest='proj4_str',
            help="Proj4 string of the data, empty if 'grid_name' in grids.conf")
    parser.add_argument('geotransform', type=float, nargs=6,
            help="six numbers representing a GDAL GeoTransform, (xorigin, xpixelsize, 0, yorigin, 0, ypixelsize)")
    parser.add_argument('input_filename',
            help="name of the flat binary file to convert into a geotiff")
    parser.add_argument('output_filename', default=None, nargs='?',
            help="name of the output geotiff, uses default naming scheme if not entered")
    parser.add_argument('--bits', type=int, default=16,
            help="number of bits in the geotiff, usually unsigned")
    parser.add_argument('--rescale-config', default=None,
            help="alternative rescale configuration file")
    args = parser.parse_args()

    arg_list = []
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
    print "Converted Start Time: %s" % args.start_time.isoformat()
    arg_list.append(args.start_time)
    print "Grid Name: ",args.grid_name
    arg_list.append(args.grid_name)

    # Get the proj4 string from the config file
    if args.proj4_str is None:
        raise NotImplementedError("Getting projection information from grids.conf is not implemented yet")
    print "Projection String: ",args.proj4_str
    arg_list.append(args.proj4_str)
    print "GeoTransform: %r" % args.geotransform
    arg_list.append(tuple(args.geotransform))

    print "Input Filename: ",args.input_filename
    W = Workspace('.')
    data = getattr(W, args.input_filename.split('.')[0]).copy()
    # XXX Remove this once scaling is added to the backend
    #from polar2grid.rescale import sqrt_scale
    #data = sqrt_scale(data)
    arg_list.append(data)
    print "Output Filename: ",args.output_filename

    if args.bits == 8:
        etype=gdal.GDT_Byte
    elif args.bits == 16:
        etype=gdal.GDT_UInt16
    else:
        print "Don't know how to handle %d bits" % args.bits
        print "Defaulting to 16"
        etype=gdal.GDT_UInt16

    return backend(*arg_list, output_filename=args.output_filename, etype=etype)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sys.exit(main())

