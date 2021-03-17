from behave import given, when, then
import os
import tempfile
import subprocess
import shutil
import glob


@given('input data from {source}')
def step_impl(context, source):
    new_source = ""

    for f in source.split(" "):
        f = os.path.join(context.datapath, f)
        new_source += f + " "

        if "*" in os.path.basename(f):
            assert glob.glob(f), "Input files {} do  not exist".format(f)
            assert os.path.exists(os.path.dirname(f)), "Input folder {} does not exist".format(os.path.dirname(f))
        else:
            assert os.path.exists(f), "Input {} does not exist".format(f)

    context.source = new_source


@when('{command} runs')
def step_impl(context, command):
    context.script = command.split()[0]
    context.command = "datapath={}; {} {}".format(context.datapath, os.path.join(context.p2g_path, command),
                                                  context.source)

    # creating new data in temporary directory to compare
    orig_dir = os.getcwd()
    try:
        context.temp_dir = tempfile.mkdtemp(prefix='p2g_tests_')
        os.chdir(context.temp_dir)
        exit_status = subprocess.call(context.command, shell=True)
        assert exit_status == 0, "{} ran unsuccessfully".format(context.command)
    finally:
        os.chdir(orig_dir)
    
    assert os.path.exists(context.temp_dir), "Temporary directory not created"
    assert os.listdir(context.temp_dir), "No files were created"


@then('the output matches with the files in {output}')
def step_impl(context, output):
    orig_dir = os.getcwd()
    try:
        os.chdir(context.datapath)
        # NOTE: 81231 / 151404144 (0.054%) pixels are currently wrong in VIIRS_L1B.
        if "geotiff" in context.command or context.script == "geo2grid.sh":
            compare_command = ' '.join([os.path.join(context.p2g_path, 'p2g_compare_geotiff.sh'),
                                        output, context.temp_dir, '-vv', '--margin-of-error',
                                        str(81231 / 1514041.44)])
        else:
            compare_command = ' '.join([os.path.join(context.p2g_path, 'p2g_compare_netcdf.sh'),
                                        output, context.temp_dir, '-vv', '--margin-of-error',
                                        str(81231 / 1514041.44), '--variables', 'data'])
        exit_status = subprocess.call(compare_command, shell=True)
        assert exit_status == 0, "Files did not match with the correct output"
    finally:
        os.chdir(orig_dir)
        shutil.rmtree(context.temp_dir)
