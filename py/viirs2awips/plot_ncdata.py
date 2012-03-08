from numpy import *
from matplotlib import pyplot as plt
from netCDF4 import Dataset
nc = Dataset("./awips.nc", "r")
data = nc.variables["image"][:]
data = data.astype(uint8) # How AWIPS reads it
print data.min(), data.max()
plt.imshow(data)
plt.colorbar()
plt.bone()
#plt.spectral()
plt.savefig("plot_ncdata.png")
