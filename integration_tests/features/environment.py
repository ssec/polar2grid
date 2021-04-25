import os
import shutil
import sys
import tempfile


def before_all(context):
    context.html_dst = context.config.userdata.get("html_dst", None)
    if context.html_dst is not None:
        context.html_dst = os.path.join(context.html_dst, "test_status")
    context.datapath = context.config.userdata["datapath"]
    if not context.datapath.startswith(os.sep):
        context.datapath = os.path.join(os.getcwd(), context.datapath)
    p2g_home = os.environ.get("POLAR2GRID_HOME")
    context.p2g_path = os.path.join(p2g_home, "bin") if p2g_home is not None else ""
    tmpdir = tempfile.gettempdir()
    context.base_temp_dir = os.path.join(tmpdir, "p2g_integration_tests")

    # remove any previous test results
    if os.path.isdir(context.base_temp_dir):
        shutil.rmtree(context.base_temp_dir, ignore_errors=True)
    os.mkdir(context.base_temp_dir)


def after_all(context):
    if context.failed:
        sys.exit(1)
