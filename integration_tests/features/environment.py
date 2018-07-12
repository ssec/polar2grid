import sys
    
def before_all(context):
    context.data_path = "/data/users/kkolman/test_data"
    #context.data_path = "/data/users/kathys/test_data"
    #context.p2g_path = "/data/dist/polar2grid-swbundle-2.2.1b0/bin"    
    context.p2g_path = "POLAR2GRID_HOME/test_swbundle"    

def after_all(context):
    if context.failed:
        sys.exit(1)

