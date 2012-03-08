from numpy import *
from matplotlib import pyplot as plt
from netCDF4 import Dataset
nc = Dataset("./awips.nc", "r")
data = nc.variables["image"][:]
data = data.astype(uint8) # How AWIPS reads it
print data.min(), data.max()
plt.imshow(data)
plt.bone()
plt.colorbar()
plt.savefig("plot_ncdata.png")
