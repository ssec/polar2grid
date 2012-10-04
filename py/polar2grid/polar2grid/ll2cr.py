"""Python replacement for ms2gt's ll2cr using pyproj and
proj4 strings.
"""
import pyproj
import numpy

import os
import sys
import logging
import math

log = logging.getLogger(__name__)

def ll2cr(lon_arr, lat_arr, proj4_str,
        xres=None, yres=None,
        origin_lon=None, origin_lat=None,
        grid_width=None, grid_height=None,
        dtype=None, fill_in=-999.0, fill_out=-1e30):
    """Similar to GDAL, y pixel resolution should be negative for downward
    images.

    origin_lon,origin_lat are the grids origins
    """

    if lat_arr.shape != lon_arr.shape:
        log.error("Longitude and latitude arrays must be the same shape (%r vs %r)" % (lat_arr.shape, lon_arr.shape))
        raise ValueError("Longitude and latitude arrays must be the same shape (%r vs %r)" % (lat_arr.shape, lon_arr.shape))

    if (xres is None and yres is not None) or \
            (yres is None and xres is not None):
        log.error("xres and yres must both be specified or neither")
        raise ValueError("xres and yres must both be specified or neither")

    # XXX: For initial testing, always provide pixel size and origin location
    if xres is None:
        calc_res = True
        raise NotImplementedError("Need resolutions")
    else:
        calc_res = False

    if (origin_lon is None and origin_lat is not None) or \
            (origin_lat is None and origin_lon is not None):
        log.error("origin_lon and origin_lat must both be specified or neither")
        raise ValueError("origin_lon and origin_lat must both be specified or neither")

    if (grid_width is None and grid_height is not None) or \
            (grid_width is not None and grid_height is None):
        log.error("grid_width and grid_height must both be specified or neither")
        raise ValueError("grid_width and grid_height must both be specified or neither")
    #else:
    #    calc_origin = False

    # Handle EPSG codes
    if proj4_str[:4].lower() == "epsg":
        tformer = pyproj.Proj(init=proj4_str)
    else:
        tformer = pyproj.Proj(proj4_str)

    if dtype is None:
        dtype = lat_arr.dtype

    # TODO: Figure out filenames
    # cols then rows in FBF filenames
    rows_fn = "rows.real4.%d.%d" % lat_arr.shape[::-1]
    rows_arr = numpy.memmap(rows_fn, dtype=dtype, mode="w+", shape=lat_arr.shape)
    cols_fn = "cols.real4.%d.%d" % lat_arr.shape[::-1]
    cols_arr = numpy.memmap(cols_fn, dtype=dtype, mode="w+", shape=lat_arr.shape)

    good_mask = (lon_arr != -999) & (lat_arr != -999)
    if origin_lon is None:
        #calc_origin = True
        origin_lon = lon_arr[good_mask].min()
        print "Data left longitude: ",origin_lon
        #origin_lon -= 10
        #print "Grid left longitude: ",origin_lon
        origin_lat = lat_arr[good_mask].max()
        print "Data upper latitude: ",origin_lat
        #origin_lat += 5
        #print "Grid upper latitude: ",origin_lat
    grid_origin_x,grid_origin_y = tformer(origin_lon, origin_lat)
    print grid_origin_x,grid_origin_y

    if grid_width is None:
        xmax = lon_arr[good_mask].max()
        print "Data right longitude: ",xmax
        #xmax += 10
        #print "Grid right longitude: ",xmax
        ymin = lat_arr[good_mask].min()
        print "Data lower latitude: ",ymin
        #ymin -= 4
        #print "Grid lower latitude: ",ymin
        #corner_x,corner_y = tformer(xmax,ymin)
        corner_x1,corner_y1 = tformer(xmax,ymin)
        print "corners 1: ",corner_x1,corner_y1
        corner_x2,corner_y2 = tformer(origin_lon,ymin)
        print "corners 2: ",corner_x2,corner_y2
        corner_x3,corner_y3 = tformer(xmax,origin_lat)
        print "corners 3: ",corner_x3,corner_y3
        grid_origin_x = min(corner_x1,corner_x2,corner_x3,grid_origin_x)
        corner_x = max(corner_x1,corner_x2,corner_x3,grid_origin_x)
        grid_origin_y = max(corner_y1,corner_y2,corner_y3,grid_origin_y)
        corner_y = min(corner_y1,corner_y2,corner_y3,grid_origin_y)
        print "corners: ",corner_x,corner_y

        grid_width = (corner_x - grid_origin_x) / xres
        grid_height = (corner_y - grid_origin_y) / yres
        #print "Grid width/height estimates (%f, %f)" % (grid_width, grid_height)
        #if grid_width % 1 != 0 or grid_height % 1 != 0:
        #    grid_width = math.ceil(grid_width) if grid_width > 0 else math.floor(grid_width)
        #    grid_height = math.ceil(grid_height) if grid_height > 0 else math.floor(grid_height)
        #    xres = float(corner_x - grid_origin_x) / grid_width
        #    yres = float(corner_y - grid_origin_y) / grid_height
        #    log.warning("Changing xres and yres to (%f, %f) to fit integer size" % (xres,yres))
        print "Grid width/height (%d, %d)" % (grid_width,grid_height)
        
    #if not calc_origin:
    #if calc_origin or calc_res:
    #    x_buffer = numpy.zeros(lat_arr.shape)
    #    y_buffer = numpy.zeros(lat_arr.shape)
    #    bad_mask = numpy.zeros(lat_arr.shape[1])
    good_mask = numpy.zeros(lat_arr.shape[1], dtype=numpy.bool)
    #grid_width = 5120
    #grid_height = 5120
    #grid_width = lat_arr.shape[1]
    #grid_height = lat_arr.shape[0]
    #print tformer(0, 0, inverse=True)
    print "Real upper-left corner (%f,%f)" % tformer(grid_origin_x, grid_origin_y, inverse=True)
    print "Real lower-right corner (%f,%f)" % tformer(grid_origin_x+xres*grid_width, grid_origin_y+yres*grid_height, inverse=True)
    ll2cr_info = {}
    ll2cr_info["grid_origin_x"] = grid_origin_x
    ll2cr_info["grid_origin_y"] = grid_origin_y
    ll2cr_info["grid_width"] = grid_width
    ll2cr_info["grid_height"] = grid_height
    ll2cr_info["pixel_size_x"] = xres
    ll2cr_info["pixel_size_y"] = yres
    #print tformer(xres*(grid_width+0.5), yres*(grid_height+0.5), inverse=True)
    #print grid_origin_x,grid_origin_y,tformer(-122.0,59.0)
    #print xres,yres,origin_lon,origin_lat,grid_width,grid_height

    # Do calculations for each row in the source file
    # Go per row to save on memory
    for idx in range(lon_arr.shape[0]):
        x_tmp,y_tmp = tformer(lon_arr[idx], lat_arr[idx])
        #if calc_origin:
        #    origin_lon = min(x_tmp[x_tmp != fill_in].min(), origin_lon)
        #    origin_lat = max(y_tmp[y_tmp != fill_in].max(), origin_lat)
        #if calc_res and idx == 0:
        #    xres = abs(x_tmp[idx,x_tmp != fill_in].max() - x_tmp[idx,x_tmp != fill_in].min())
        #    yres = y_tmp[idx,y_tmp != fill_in].max()
        #elif calc_res and idx == lon_arr.shape[0] - 1:
        #    xres = xres/lat_arr.shape[1]
        #    yres = abs(y_tmp[idx,y_tmp != fill_in].min() - yres)/lat_arr.shape[0]

        #if calc_origin or calc_res:
        #    # bad_mask is True for good values
        #    bad_mask[:] = (lon_arr[idx] != fill_in) & (lat_arr[idx] != fill_in)
        #    x_buffer[idx,bad_mask] = x_tmp[bad_mask]
        #    y_buffer[idx,bad_mask] = y_tmp[bad_mask]
        #    x_buffer[idx,not bad_mask] = fill_out
        #    y_buffer[idx,not bad_mask] = fill_out
        #else:
        numpy.subtract(x_tmp, grid_origin_x, x_tmp)
        numpy.divide(x_tmp, xres, x_tmp)
        numpy.subtract(y_tmp, grid_origin_y, y_tmp)
        numpy.divide(y_tmp, yres, y_tmp)

        #if idx == 0 or idx == 1535:
        #    print lon_arr[idx,:10]
        #    print lon_arr[idx,-10:]
        #    print lat_arr[idx,:10]
        #    print lat_arr[idx,-10:]
        #    print x_tmp[:10]
        #    print x_tmp[-10:]
        #    print y_tmp[:10]
        #    print y_tmp[-10:]
        #    print grid_width + 0.5, grid_height + 0.5

        # good_mask here is True for good values
        #print numpy.nonzero((lon_arr[idx] != fill_in) & (lat_arr[idx] != fill_in))
        good_mask[:] =  ~( ((lon_arr[idx] == fill_in) | (lat_arr[idx] == fill_in)) | \
                ( (x_tmp < -0.5) | (x_tmp > (grid_width + 0.5)) ) | \
                ( (y_tmp < -0.5) | (y_tmp > (grid_height + 0.5)) ) )
        cols_arr[idx,good_mask] = x_tmp[good_mask]
        cols_arr[idx,~good_mask] = fill_out
        rows_arr[idx,good_mask] = y_tmp[good_mask]
        rows_arr[idx,~good_mask] = fill_out

    log.info("row and column calculation complete")

    #if calc_origin or calc_res:
    #    # TODO finish calculations
    #    bad_mask = cols_arr != fill_out
    #    cols_arr[bad_mask] = (x_buffer[bad_mask] - grid_origin_x)/xres
    #    rows_arr[bad_mask] = (y_buffer[bad_mask] - grid_origin_y)/yres
    return ll2cr_info

def main():
    from polar2grid.core import Workspace
    from optparse import OptionParser
    usage = """
    %prog [options] lon_file lat_file "quoted proj4 string (can be 'epsg:####')"

    Resolutions
    ===========

    If 'xres' is not specified it will be computed by the following formula:

        xres = abs(in_meters(lat[0,0]) - in_meters(lat[-1,0])) / num_lines

    Same for 'yres'.

    Grid Origin
    ===========

    If the latitude and longitude of the grid origin aren't specified, they
    will be calculated by taking the minimum longitude and maximum latitude
    (upper-left corner).  This will increase processing time and memory usage
    significantly as intermediate calculations must stored until the min and
    max can be calculated.

    """
    parser = OptionParser(usage=usage)
    parser.add_option("--xres", dest="xres", default=None,
            help="Specify the X resolution (pixel size) of the output grid (in meters)")
    parser.add_option("--yres", dest="yres", default=None,
            help="Specify the Y resolution (pixel size) of the output grid (in meters)")
    parser.add_option("--olon", dest="origin_lon", default=None,
            help="Specify the longitude of the grid's origin (upper-left corner)")
    parser.add_option("--olat", dest="origin_lat", default=None,
            help="Specify the latitude of the grid's origin (upper-left corner)")
    parser.add_option("--fill-in", dest="fill_in", default=-999.0,
            help="Specify the fill value that incoming latitude and" + \
                    "longitude arrays use to mark invalid data points")
    parser.add_option("--fill-out", dest="fill_out", default=-1e30,
            help="Specify the fill value that outgoing cols and rows" + \
                    "arrays will use to identify bad data")
    options,args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    fill_in = float(options.fill_in)
    fill_out = float(options.fill_out)
    xres = options.xres and float(options.xres)
    yres = options.yres and float(options.yres)
    origin_lon = options.origin_lon
    if origin_lon is not None: origin_lon = float(origin_lon)
    origin_lat = options.origin_lat
    if origin_lat is not None: origin_lat = float(origin_lat)

    if len(args) != 3:
        log.error("Expected 3 arguments, got %d" % (len(args),))
        raise ValueError("Expected 3 arguments, got %d" % (len(args),))

    lon_fn = os.path.realpath(args[0])
    lat_fn = os.path.realpath(args[1])
    proj4_str = args[2]

    w_dir,lat_var = os.path.split(lat_fn)
    lat_var = lat_var.split(".")[0]
    W = Workspace(w_dir)
    lat_arr = getattr(W, lat_var)
    w_dir,lon_var = os.path.split(lon_fn)
    lon_var = lon_var.split(".")[0]
    W = Workspace(w_dir)
    lon_arr = getattr(W, lon_var)

    return ll2cr(lon_arr, lat_arr, proj4_str,
            xres=xres, yres=yres,
            origin_lon=origin_lon, origin_lat=origin_lat,
            fill_in=fill_in, fill_out=fill_out)

if __name__ == "__main__":
    sys.exit(main())

