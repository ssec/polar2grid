#!/usr/bin/env python
# encoding: utf-8
"""Simple script to plot remapped binary files
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

def main(fill=-999.0):
    W=Workspace('.')

    for fn in glob("result_*.real4.*.*"):
        print "Plotting for %s" % fn
        plt.figure()
        fbf_attr = fn.split(".")[0]
        result = getattr(W, fbf_attr)
        result = numpy.ma.masked_where(result == FILL, result)
        print result.min(),result.max()
        plt.imshow(result)
        plt.bone()
        plt.colorbar()
        plt.savefig("plot_result.%s.png" % fbf_attr)
        plt.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        FILL = float(sys.argv[1])
    else:
        FILL = -999.0

    sys.exit(main(fill=FILL))
