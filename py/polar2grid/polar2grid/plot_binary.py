#!/usr/bin/env python
# encoding: utf-8
"""Simple script to plot flat binary files
onto a png file using matplotlib.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

from glob import glob
import numpy
import matplotlib
matplotlib.use('agg')
from matplotlib import pyplot as plt
from polar2grid.core import Workspace

def plot_binary(bf, workspace='.', fill_value=-999.0):
    W=Workspace(workspace)

    plt.figure()
    fbf_attr = bf.split(".")[0]
    result = getattr(W, fbf_attr)
    result = numpy.ma.masked_where(result == fill_value, result)
    print result.min(),result.max()
    plt.imshow(result)
    plt.bone()
    plt.colorbar()
    plt.savefig("plot_binary.%s.png" % fbf_attr)
    plt.close()

def main():
    from argparse import ArgumentParser
    description = """
Plot binary files using matplotlib.
    """
    parser = ArgumentParser(description=description)
    parser.add_argument("-f", dest="fill_value", default=-999.0, type=float,
            help="Specify the fill_value of the input file(s)")
    parser.add_argument("-p", dest="pattern",
            help="filename pattern to search the current directory for")
    parser.add_argument("binary_files", nargs="*",
            help="list of flat binary files to be plotted in the current directory")
    args = parser.parse_args()

    workspace = '.'
    binary_files = args.binary_files
    if not args.binary_files and not args.pattern:
        args.pattern = "result_*.real4.*.*"
    if args.pattern:
        workspace = os.path.split(args.pattern)[0]
        binary_files = [ os.path.split(x)[1] for x in glob(args.pattern) ]

    for bf in binary_files:
        print "Plotting '%s'" % (bf,)
        try:
            plot_binary(bf, workspace='.', fill_value=args.fill_value)
        except StandardError as e:
            print "Could not plot '%s'" % (bf,)
            if hasattr(e, "msg"): print e,e.msg
            else: print e

if __name__ == "__main__":
    import sys

    sys.exit(main())

