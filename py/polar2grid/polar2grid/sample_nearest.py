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
from polar2grid.core import Workspace

import os

DEFAULT_FILL_VALUE = -999.0

def _load_data_from_file(file_name, workspace='.',
                fill_value=DEFAULT_FILL_VALUE):
    
    print("loading data from file " + str(file_name))
    
    W=Workspace(workspace)
    fbf_attr = file_name.split(".")[0]
    result = getattr(W, fbf_attr)
    result = numpy.ma.masked_where(result == fill_value, result)
    
    #print "loaded data range: "
    #print result.min(),result.max()
    
    return result

def _find_nearest_data_pt (lonToFind, latToFind, lonData, latData, dataValues,
                           fill_value=DEFAULT_FILL_VALUE) :
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
    parser.add_argument("-f", dest="fill_value", default=DEFAULT_FILL_VALUE, type=float,
            help="Specify the fill_value of the input file(s)")
    
    parser.add_argument("--lon", dest="lonVal", default=None, type=float,
            help="Specify the longitude to find a the point nearest")
    parser.add_argument("--lat", dest="latVal", default=None, type=float,
            help="Specify the latitude  to find a the point nearest")
    
    parser.add_argument("-laf", dest="latFile", default=None, type=str,
            help="Specify the binary file to load the latitude from")
    parser.add_argument("-lof", dest="lonFile", default=None, type=str,
            help="Specify the binary file to load the longitude from")
    
    parser.add_argument("data_file", nargs="*",
            help="the data file to be sampled from")
    
    args = parser.parse_args()
    
    # check what the user gave us on the command line
    if len(args.data_file) != 1 :
        print "Data file required for point selection. Skipping."
    elif args.latVal is None or args.lonVal is None :
        print "Longitude and latitude to find must be selected. Skipping."
    elif args.latFile is None or args.lonFile is None :
        print "Files to load latitude and longitude must be given. Skipping."
    else :
        
        # if we got to here, we have the minimum we needed to try
        data    = _load_data_from_file(args.data_file[0], fill_value=args.fill_value)
        latData = _load_data_from_file(args.latFile,      fill_value=args.fill_value)
        lonData = _load_data_from_file(args.lonFile,      fill_value=args.fill_value)
        
        value, lonPt, latPt = _find_nearest_data_pt (args.lonVal,
                                                     args.latVal,
                                                     lonData, latData, data,
                                                     fill_value=args.fill_value)
        
        print ("Found data value " + str(value) + " at longitude "
               + str(lonPt) + " and latitude " + str(latPt))

if __name__ == "__main__":
    import sys

    sys.exit(main())

