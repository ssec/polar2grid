import sys, os


def before_all(context):
    datapath = context.config.userdata.get('datapath')
    os.environ['DATAPATH'] = datapath if datapath is not None else os.environ['DATAPATH']
    if not os.environ['DATAPATH'].startswith(os.sep):
        os.environ['DATAPATH'] = os.path.join(os.getcwd(), os.environ['DATAPATH'])
    p2g_home = os.environ.get('POLAR2GRID_HOME')
    context.p2g_path = os.path.join(p2g_home, 'bin') if p2g_home is not None else ''


def after_all(context):
    if context.failed:
        sys.exit(1)
