import sys, os   
 
def before_all(context):
    p2g_home = os.path.expandvars("$POLAR2GRID_HOME")
    #context.data_path = "{}/../integration_tests/p2g_test_data".format(p2g_home)
    #context.data_path = "/data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data"
    if config.userdata["datapath"].startswith("/"):
        context.data_path = config.userdata["datapath"]
    else:
        context.data_path = os.path.join(os.getcwd(), config.userdata["datapath"])
    print(context.data_path)
    context.p2g_path = "{}/bin".format(p2g_home)

def after_all(context):
    if context.failed:
        sys.exit(1)
