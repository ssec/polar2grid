from numpy import *
from matplotlib import pyplot as plt
from keoni.fbf import Workspace; W=Workspace('.')
result=W.result[0]
plt.imshow(result)
plt.bone()
plt.savefig("plot_result.png")
