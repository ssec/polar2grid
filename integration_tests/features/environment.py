import sys
    
def before_all(context):
    context.numFailed = 0
    context.data_path = "/data/test_data/old_polar2grid_data/polar2grid_test"
    context.p2g_path = "/data/dist/polar2grid-swbundle-2.2.1b0/bin"    

def after_feature(context, feature):
    if context.failed:
        context.numFailed += 1

def after_all(context):
    if context.numFailed > 0:
        sys.exit(1)

