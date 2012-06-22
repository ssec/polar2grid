from numpy import *
from matplotlib import pyplot as plt
from polar2grid.core import Workspace; W=Workspace('.')

import os
import sys
from glob import glob

if "-f" in sys.argv:
    fit = True
else:
    fit = False

for img_name in glob("image_*") + glob("prescale_DNB*"):
    print "Plotting for %s" % img_name

    # Get the data and mask it
    img_name = img_name.split(".")[0]
    img=getattr(W, img_name)
    discard = (img <= -999)
    data=ma.masked_array(img, discard)

    # Plot the data
    print data.min(),data.max()
    # Create a new figure everytime so things don't get shared
    if fit:
        fsize = (array(data.shape)/100.0)[::-1]
        plt.figure(figsize=fsize, dpi=100)
    else:
        plt.figure()
    plt.imshow(data)
    #plt.spectral()
    plt.bone()

    if fit:
        plt.subplots_adjust(left=0, top=1, bottom=0, right=1, wspace=0, hspace=0)
        plt.savefig("plot_%s.png" % img_name, dpi=100)
    else:
        # Add a colorbar and force the colormap
        plt.colorbar()
        plt.savefig("plot_%s.png" % img_name)

