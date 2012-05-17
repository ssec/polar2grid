from numpy import *
from matplotlib import pyplot as plt
from netCDF4 import Dataset
from glob import glob
import sys

def exc_handler(exc_type, exc_value, traceback):
    print "Uncaught error creating png images"

def main(vmin=0, vmax=255):
    for nc_name in glob("SSEC_AWIPS_VIIRS*"):
        print "Drawing for NC name %s" % nc_name
        # Get the data and mask it
        nc = Dataset(nc_name, "r")
        data_var = nc.variables["image"]
        data_var.set_auto_maskandscale(False)
        data = data_var[:]
        data = data.astype(uint8) # How AWIPS reads it

        # Create a new figure everytime so things don't get shared
        plt.figure()

        # Plot the data
        print data.min(), data.max()
        plt.imshow(data, vmin=vmin, vmax=vmax)

        # Add a colorbar and force the colormap
        plt.colorbar()
        #plt.spectral()
        plt.bone()

        plt.savefig("plot_ncdata.%s.png" % nc_name)
        plt.close()

if __name__ == "__main__":
    import optparse
    usage = "python %prog [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--vmin', dest="vmin", default=None,
            help="Specify minimum brightness value")
    parser.add_option('--vmax', dest="vmax", default=None,
            help="Specify maximum brightness value")
    options,args = parser.parse_args()
    sys.exceptionhook=exc_handler

    if options.vmin is None:
        vmin = None
    else:
        vmin = int(options.vmin)

    if options.vmax is None:
        vmax = None
    else:
        vmax = int(options.vmax)

    sys.exit(main(vmin=vmin, vmax=vmax))
