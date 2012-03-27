from numpy import *
from matplotlib import pyplot as plt
from netCDF4 import Dataset
from glob import glob
for nc_name in glob("SSEC_AWIPS_VIIRS*"):
    print "Drawing for NC name %s" % nc_name
    nc = Dataset(nc_name, "r")
    data = nc.variables["image"][:]
    data = data.astype(uint8) # How AWIPS reads it
    print data.min(), data.max()
    plt.imshow(data)
    #plt.colorbar()
    plt.bone()
    #plt.spectral()
    plt.savefig("plot_ncdata.%s.png" % nc_name)
