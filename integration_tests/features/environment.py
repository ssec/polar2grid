import sys, os   
 
def before_all(context):
    p2g_home = os.path.expandvars("$POLAR2GRID_HOME")
    #context.data_path = "{}/../integration_tests/p2g_test_data".format(p2g_home)
    #context.data_path = "/data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data"
    if context.config.userdata["datapath"].startswith(os.sep):
        context.data_path = context.config.userdata["datapath"]
    else:
        context.data_path = os.path.join(os.getcwd(), context.config.userdata["datapath"])
    context.p2g_path = "{}/bin".format(p2g_home)

def after_all(context):
    if context.failed:
        sys.exit(1)
