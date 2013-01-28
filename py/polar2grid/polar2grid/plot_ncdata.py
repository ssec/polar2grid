#!/usr/bin/env python
# encoding: utf-8
"""Simple script to plot AWIPS NetCDF files onto a png file using matplotlib.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

from numpy import *
import numpy as numpy
import matplotlib
matplotlib.use('agg')
from matplotlib import pyplot as plt
import matplotlib.cm as cm
from netCDF4 import Dataset
from glob import glob
import sys
import os

DEF_DIR = "."
DEF_PAT = "SSEC_AWIPS_*"

DEF_VMIN = 0
DEF_VMAX = 255
DEF_DPI  = 100

def _open_file_and_get_var_data (file_name, var_name, var_type=uint8) :
    """
    open a file and get the variable from it, converting it to var_type
    
    note: uint8 is the default type which converts AWIPS data to something
    more plotable.
    """
    
    dataset = Dataset(file_name, "r")
    data_var = dataset.variables[var_name]
    data_var.set_auto_maskandscale(False)
    data = data_var[:]
    data = data.astype(var_type)
    
    return data

def _plt_basic_imshow_fig (data, vmin, vmax, cmap=cm.bone, title="image") :
    """
    plot a basic imshow figure using the given data,
    bounds, and colormap
    """
    
    # Create a new figure everytime so things don't get shared
    figure = plt.figure()
    axes   = figure.add_subplot(111)

    # Plot the data
    print data.min(), data.max()
    plt.imshow(data, vmin=vmin, vmax=vmax, cmap=cmap)

    # Add a colorbar and force the colormap
    plt.colorbar()
    
    # Add the title
    axes.set_title(title)
    
    return figure

def exc_handler(exc_type, exc_value, traceback):
    print "Uncaught error creating png images"
    raise # this is wrong, but I need to see these errors, not silence them

def main(base_dir=DEF_DIR, base_pat=DEF_PAT, vmin=DEF_VMIN, vmax=DEF_VMAX, dpi_to_use=DEF_DPI):
    glob_pat = os.path.join(base_dir, base_pat)
    for nc_name in glob(glob_pat):
        nc_name = os.path.split(nc_name)[1]
        print "Drawing for NC name %s" % nc_name
        
        # Get the data from the file
        data = _open_file_and_get_var_data(nc_name, "image")
        
        # plot and save our figure
        figure = _plt_basic_imshow_fig(data, vmin, vmax, title="nc_name")
        figure.savefig("plot_ncdata.%s.png" % nc_name, dpi=dpi_to_use)
        plt.close()

def rough_compare (path1, path2, vmin=DEF_VMIN, vmax=DEF_VMAX, dpi_to_use=DEF_DPI):
    """
    very roughly compare the two data sets and draw some images
    """
    
    data1 = _open_file_and_get_var_data(path1, "image")
    data2 = _open_file_and_get_var_data(path2, "image")
    
    diff    = numpy.zeros(data1.shape, dtype=int32)
    diff[:] = data1[:]
    diff    = diff - data2
    
    # make a picture of the first data set
    fig = _plt_basic_imshow_fig(data1, vmin, vmax, title="data set 1", cmap=cm.Paired)
    fig.savefig("plot_ncdata.Set1.png", dpi=dpi_to_use)
    plt.close()
    
    # make a picture of the second data set
    fig = _plt_basic_imshow_fig(data2, vmin, vmax, title="data set 2", cmap=cm.Paired)
    fig.savefig("plot_ncdata.Set2.png", dpi=dpi_to_use)
    plt.close()
    
    # make a picture of the difference
    fig = _plt_basic_imshow_fig(diff, numpy.min(diff), numpy.max(diff), title="difference", cmap=cm.Spectral)
    fig.savefig("plot_ncdata.diff.png", dpi=dpi_to_use)
    plt.close()
    
    # make a picture of the difference in a more restricted range
    diff[diff >  10.0] =  10.0
    diff[diff < -10.0] = -10.0
    fig = _plt_basic_imshow_fig(diff, numpy.min(diff), numpy.max(diff), title="difference, restricted", cmap=cm.Spectral)
    fig.savefig("plot_ncdata.diff_r.png", dpi=dpi_to_use)
    plt.close()
    

if __name__ == "__main__":
    import optparse
    usage = "python %prog [options] [ base directory | '.' ]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--vmin', dest="vmin", default=None,
            help="Specify minimum brightness value. Defaults to minimum value of data.")
    parser.add_option('--vmax', dest="vmax", default=None,
            help="Specify maximum brightness value. Defaults to maximum value of data.")
    parser.add_option('--pat', dest="base_pat", default=DEF_PAT,
            help="Specify the glob pattern of NetCDF files to look for. Defaults to '%s'" % DEF_PAT)
    parser.add_option('--dpi', dest="dpi",   default=100, type='float',
            help="Specify the dpi for the resulting figure, higher dpi will result in larger figures and longer run times")
    parser.add_option('-c', dest="do_compare", default=False, action="store_true",
            help="Include this flag if you wish to compare two specific files")
    options,args = parser.parse_args()
    sys.excepthook=exc_handler
    
    files_temp = None
    if len(args) == 0:
        base_dir = DEF_DIR
    elif len(args) == 1:
        base_dir = args[0]
    elif len(args) == 2 :
        base_dir = DEF_DIR
        files_temp = (args[0], args[1])
    
    if options.vmin is None:
        vmin = None
    else:
        vmin = int(options.vmin)
    
    if options.vmax is None:
        vmax = None
    else:
        vmax = int(options.vmax)
    
    if files_temp is None :
        sys.exit(main(base_dir=base_dir, base_pat=options.base_pat, vmin=vmin, vmax=vmax, dpi_to_use=options.dpi))
    else :
        sys.exit(rough_compare(files_temp[0], files_temp[1], vmin=vmin, vmax=vmax, dpi_to_use=options.dpi))

