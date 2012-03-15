from keoni.map.graphics import mapshow
from matplotlib import pyplot as plt
from numpy import *
from keoni.fbf import Workspace; W=Workspace('.')
img=W.image[0]
lat=W.latitude[0]
lon=W.longitude[0]
discard = (img <= -999)
data=ma.masked_array(img, discard)
dlat=ma.masked_array(lat, discard)
dlon=ma.masked_array(lon, discard)
mapshow(dlon, dlat, data)
plt.savefig("map_img.png")
