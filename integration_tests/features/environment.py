import sys, os   
 
def before_all(context):
    p2g_home = os.path.expandvars("$POLAR2GRID_HOME")
    context.data_path = "{}/../integration_tests/p2g_test_data".format(p2g_home)
    context.p2g_path = "{}/bin".format(p2g_home)

def after_all(context):
    if context.failed:
        sys.exit(1)

