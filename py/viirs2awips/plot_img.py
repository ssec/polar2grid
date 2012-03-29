from numpy import *
from matplotlib import pyplot as plt
from keoni.fbf import Workspace; W=Workspace('.')
from glob import glob
for img_name in glob("image_*"):
    print "Plotting for %s" % img_name
    img=getattr(W, img_name.split(".")[0])[0]
    discard = (img <= -999)
    data=ma.masked_array(img, discard)
    plt.imshow(data)
    plt.bone()
    plt.savefig("plot_img.png")
