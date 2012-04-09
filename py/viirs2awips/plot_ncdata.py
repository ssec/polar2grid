from numpy import *
from matplotlib import pyplot as plt
from netCDF4 import Dataset
from glob import glob
for nc_name in glob("SSEC_AWIPS_VIIRS*"):
    print "Drawing for NC name %s" % nc_name
    # Get the data and mask it
    nc = Dataset(nc_name, "r")
    data = nc.variables["image"][:]
    data = data.astype(uint8) # How AWIPS reads it

    # Create a new figure everytime so things don't get shared
    plt.figure()

    # Plot the data
    print data.min(), data.max()
    plt.imshow(data)

    # Add a colorbar and force the colormap
    plt.colorbar()
    #plt.spectral()
    plt.bone()

    plt.savefig("plot_ncdata.%s.png" % nc_name)
