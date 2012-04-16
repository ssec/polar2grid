from numpy import *
from matplotlib import pyplot as plt
from core import Workspace; W=Workspace('.')
result=W.result
plt.imshow(result)
plt.bone()
plt.savefig("plot_result.png")
