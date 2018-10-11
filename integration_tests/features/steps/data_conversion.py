from behave import given, when, then, step
import os
import tempfile
import subprocess
import shutil
import glob


@given(u'input data from {source}')
def step_impl(context, source):
    new_source = ""
    
    for f in source.split(" "):
        f = os.path.join(context.data_path, f) 
        new_source += f + " "

        if "*" in os.path.basename(f):
            assert glob.glob(f), "Input files {} do  not exist".format(f)
            assert os.path.exists(os.path.dirname(f)), "Input folder {} does not exist".format(os.path.dirname(f))
        else:
            assert os.path.exists(f), "Input {} does not exist".format(f)

    context.source = new_source

@when(u'{script} {command} runs') 
def step_impl(context, script, command):
    context.script = script
    context.command = "{} {} {}".format(os.path.join(context.p2g_path, script), command, context.source)

    # creating new data in temporary directory to compare
    orig_dir = os.getcwd()
    try:
        context.temp_dir = tempfile.mkdtemp()
        os.chdir(context.temp_dir)
        exit_status = subprocess.call(context.command, shell=True)        
        assert exit_status == 0, "{} ran unsuccessfully".format(command)
    finally:
        os.chdir(orig_dir)
    
    assert os.path.exists(context.temp_dir), "Temporary directory not created"
    assert os.listdir(context.temp_dir), "No files were created"

@then(u'the output matches with the files in {output}')
def step_impl(context, output):
    orig_dir = os.getcwd()
    try:
        os.chdir(context.data_path)
        if "gtiff" in context.command or context.script == "geo2grid.sh":
            context.compare_command = "{} {} {}".format(os.path.join(context.data_path, "scripts/p2g_py3_compare_geotiff.sh"), output, context.temp_dir)
        else: 
            context.compare_command = "{} {} {}".format(os.path.join(context.data_path, "scripts/p2g_py3_compare_netcdf.sh"), output, context.temp_dir)
        exit_status = subprocess.call(context.compare_command, shell=True)
        assert exit_status == 0, "Files did not match with the correct output"
    finally:
        os.chdir(orig_dir)
        shutil.rmtree(context.temp_dir)
