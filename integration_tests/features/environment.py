#import logging

#def before_all(context):
#    logging.basicConfig(filemode='w', filename="/data/users/kkolman/integration_tests/polar2grid/integration_tests/behave.log", level=logging.INFO, format='%(levelname)s: %(message)s')
#    context.logger = logging.getLogger(__name__)

import sys
    
def before_all(context):
    context.numFailed = 0

def after_feature(context, feature):
    if context.failed:
        context.numFailed += 1

def after_all(context):
    if context.numFailed > 0:
        sys.exit(1)


