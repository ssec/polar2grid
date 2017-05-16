#!/usr/bin/env python
# encoding: utf-8
"""Simple script to find the nearest point to a longitude and latitude
in a data set defined by some binary files.

:author:       Eva Schiffer (evas)
:contact:      eva.schiffer@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

import numpy as numpy
from polar2grid.core import SwathScene


def _find_nearest_data_pt (lonToFind, latToFind, lonData, latData, dataValues):
    """
    given a matched set of data and navigation, find the data point that's
    nearest to the longitude and latitude given, ignoring fill data
    
    returns the data point and lon/lat found
    """
    
    # calculate the arc distance in km assuming the world is a sphere (we can move to a better model if we need to)
    latDataR = numpy.radians(numpy.array(latData, dtype=numpy.float64))
    latPtR   = numpy.radians(latToFind)
    lonDiff  = numpy.radians(numpy.abs(numpy.array(lonData, dtype=numpy.float64) - lonToFind))
    dist = numpy.arccos(  numpy.sin(latDataR) * numpy.sin(latPtR)
                        + numpy.cos(latDataR) * numpy.cos(latPtR) * numpy.cos(lonDiff))
    dist *= 6371.2
    
    # find the nearest point
    stackedInfo = numpy.array([dist.ravel(), lonData.ravel(), latData.ravel(), dataValues.ravel()])
    stackedTuples = [ ]
    for rowNum in range(stackedInfo.shape[1]) :
        stackedTuples.append((stackedInfo[0, rowNum], stackedInfo[1, rowNum], stackedInfo[2, rowNum], stackedInfo[3, rowNum]))
    stackedTuples.sort()
    
    nearestPt = stackedTuples[0]
    print ("nearest 5 pts found: " + str(stackedTuples[0:4]))
    
    return nearestPt[3], nearestPt[1], nearestPt[2]


def main():
    from argparse import ArgumentParser
    description = """
Plot binary files using matplotlib.
    """
    parser = ArgumentParser(description=description)
    parser.add_argument("scene_file", help="the data file to be sampled from")
    parser.add_argument("product_name", help="product in scene to inspect")
    parser.add_argument("lonVal", type=float, help="Specify the longitude to find a the point nearest")
    parser.add_argument("latVal", type=float, help="Specify the latitude  to find a the point nearest")

    args = parser.parse_args()
    
    # check what the user gave us on the command line
    if len(args.data_file) != 1 :
        print "Data file required for point selection. Skipping."
    elif args.latVal is None or args.lonVal is None:
        print "Longitude and latitude to find must be selected. Skipping."
    else:
        # if we got to here, we have the minimum we needed to try
        scene = SwathScene.load(args.scene_file)
        data = scene[args.product_name].get_data_array()
        swath_def = scene[args.product_name]["swath_definition"]
        lon_data = swath_def.get_longitude_array()
        lat_data = swath_def.get_longitude_array()

        value, lonPt, latPt = _find_nearest_data_pt(args.lonVal, args.latVal, lon_data, lat_data, data)
        
        print("Found data value %f at longitude %f and latitude %f" % (value, lonPt, latPt))

if __name__ == "__main__":
    import sys
    sys.exit(main())
