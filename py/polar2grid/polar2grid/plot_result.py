from glob import glob
from matplotlib import pyplot as plt
from polar2grid.core import Workspace; W=Workspace('.')

for fn in glob("result_*.real4.*.*"):
    plt.figure()
    fbf_attr = fn.split(".")[0]
    result = getattr(W, fbf_attr)
    plt.imshow(result)
    plt.bone()
    plt.colorbar()
    plt.savefig("plot_result.%s.png" % fbf_attr)
    plt.close()

