from behave import given, when, then, step
import os
import tempfile
import subprocess
import shutil


@given(u'input data from {source}')
def step_impl(context, source):
    new_source = ""
    
    for f in source.split(" "):
        f = os.path.join(context.data_path, f) 
        new_source += f + " "

        if "*" in os.path.basename(f):
            assert os.path.exists(os.path.dirname(f)), "Input folder {} does not exist".format(os.path.dirname(f))
        else:
            assert os.path.exists(f), "Input folder {} does not exist.".format(f)

    context.source = new_source

@when(u'{command} runs') 
def step_impl(context, command):
    context.command = "{} {} {}".format(os.path.join(context.p2g_path, "polar2grid.sh"), command, context.source)

    orig_dir = os.getcwd()
    try:
        context.temp_dir = tempfile.mkdtemp(dir="/data/tmp")
        os.chdir(context.temp_dir)
        subprocess.call(context.command, shell=True)        
    finally:
        os.chdir(orig_dir)
    
    assert os.path.exists(context.temp_dir), "Temporary directory not created"
    assert os.listdir(context.temp_dir), "No files were created"

@then(u'the output matches with the files in {output}')
def step_impl(context, output):
    orig_dir = os.getcwd()
    assert os.path.exists(context.temp_dir)
    assert os.listdir(context.temp_dir)
    try:
        os.chdir(context.data_path)
        if "gtiff" in context.command:
            context.compare_command = "../polar2grid_test/viirs/p2g_compare_geotiff.sh " + output + " " + context.temp_dir
        else: 
            context.compare_command = "/data/users/kkolman/p2g_compare_netcdf.sh " + output + " " + context.temp_dir
        exit_status = subprocess.call(context.compare_command, shell=True)
        assert exit_status == 0, "Files did not match with the correct output"
    finally:
        os.chdir(orig_dir)
        shutil.rmtree(context.temp_dir)

