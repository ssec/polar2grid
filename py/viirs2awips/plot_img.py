from numpy import *
from matplotlib import pyplot as plt
from keoni.fbf import Workspace; W=Workspace('.')
img=W.image[0]
discard = (img <= -999)
data=ma.masked_array(img, discard)
plt.imshow(data)
plt.bone()
plt.savefig("plot_img.png")
