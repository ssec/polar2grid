import sys
import traceback
from glob import glob
import numpy
import matplotlib
matplotlib.use('agg')
from matplotlib import pyplot as plt
from polar2grid.core import Workspace

DEFAULT_FILE_PATTERN = "result_*.real4.*.*"
DEFAULT_FILL_VALUE   = -999.0
DEFAULT_DPI          = 150

def exc_handler(exc_type, exc_value, traceback_object):
    print "Uncaught error creating png images"
    print "error type:  " + str(exc_type)
    print "error value: " + str(exc_value)
    print "traceback:"
    traceback.print_tb(traceback_object, file=sys.stdout)

def main(file_pattern=DEFAULT_FILE_PATTERN, fill=DEFAULT_FILL_VALUE, dpi=DEFAULT_DPI):
    W=Workspace('.')
    
    for fn in glob(file_pattern):
        print "Plotting for %s" % fn
        plt.figure()
        fbf_attr = fn.split(".")[0]
        result = numpy.array(getattr(W, fbf_attr))
        result = numpy.ma.masked_equal(result, fill)
        print result.min(),result.max()
        plt.imshow(result)
        plt.bone()
        plt.colorbar()
        plt.savefig(("plot_result.%s.png" % fbf_attr), dpi=dpi)
        plt.close()

if __name__ == "__main__":
    
    import optparse
    usage = "python %prog [options] [ base directory | '.' ]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--pat', dest="base_pat", default=DEFAULT_FILE_PATTERN, type='string',
            help="Specify the glob pattern of flat binary files to look for. Defaults to '%s'" % DEFAULT_FILE_PATTERN)
    parser.add_option('--dpi', dest="dpi", default=DEFAULT_DPI, type='int',
            help="The DPI to save figures at. Defaults to %d" % DEFAULT_DPI)
    parser.add_option('--fill', dest="fill_value", default=DEFAULT_FILL_VALUE, type='float',
            help="The value used for fill data. Defaults to %d" % DEFAULT_FILL_VALUE)
    options,args = parser.parse_args()
    sys.excepthook=exc_handler
    
    sys.exit(main(file_pattern=options.base_pat, fill=options.fill_value, dpi=options.dpi))
