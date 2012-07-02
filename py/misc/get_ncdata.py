"""Simple script to take an AWIPS NetCDF file and save the data inside
as a flat binary file.
"""
import numpy
from glob import glob
from netCDF4 import Dataset


for fn in glob("SSEC_AWIPS_*"):
    band_name = "sv" + fn.split("SV")[1][:3].lower()
    nc = Dataset(fn, "r")
    img_var = nc.variables["image"]
    img_var.set_auto_maskandscale(False)
    img_data = img_var[:,:].astype(numpy.uint8)
    out_fn = "%s.uint1.%s.%s" % (band_name, img_data.shape[1],img_data.shape[0])
    print "Saving %s..." % out_fn
    img_data.tofile(out_fn)

