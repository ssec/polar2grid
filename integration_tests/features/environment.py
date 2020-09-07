import sys, os


def before_all(context):
    context.datapath = context.config.userdata['datapath']
    if not context.datapath.startswith(os.sep):
        context.datapath = os.path.join(os.getcwd(), context.datapath)
    p2g_home = os.environ.get('POLAR2GRID_HOME')
    context.p2g_path = os.path.join(p2g_home, 'bin') if p2g_home is not None else ''


def after_all(context):
    if context.failed:
        sys.exit(1)
