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
