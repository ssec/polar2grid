from numpy import *
from matplotlib import pyplot as plt
from core import Workspace; W=Workspace('.')
from glob import glob
for img_name in glob("image_*") + glob("prescale_DNB*"):
    print "Plotting for %s" % img_name
    # Create a new figure everytime so things don't get shared
    plt.figure()

    # Get the data and mask it
    img_name = img_name.split(".")[0]
    img=getattr(W, img_name)
    discard = (img <= -999)
    data=ma.masked_array(img, discard)

    # Plot the data
    print data.min(),data.max()
    plt.imshow(data)

    # Add a colorbar and force the colormap
    plt.colorbar()
    #plt.spectral()
    plt.bone()

    plt.savefig("plot_%s.png" % img_name)
