import sys, os
import tempfile
from distutils.dir_util import copy_tree
from glob import glob

 
def before_all(context):
    print('????????????????????????????????????????????????????????????????????????????????????????????????????????')
    os.listdir('/var/lib/jenkins/workspace/polar2grid_tests')
    print('????????????????????????????????????????????????????????????????????????????????????????????????????????')
    context.p2g_tar = tempfile.mkdtemp()
    copy_tree(glob('/var/lib/jenkins/workspace/polar2grid_tests/polar2grid-swbundle-*')[0], context.p2g_tar)
    p2g_home = os.path.expandvars("$POLAR2GRID_HOME")
    if context.config.userdata["datapath"].startswith(os.sep):
        context.data_path = context.config.userdata["datapath"]
    else:
        context.data_path = os.path.join(os.getcwd(), context.config.userdata["datapath"])
    context.p2g_path = "{}/bin".format(p2g_home)

def after_all(context):
    if context.failed:
        sys.exit(1)
