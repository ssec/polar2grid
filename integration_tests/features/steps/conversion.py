from behave import given, when, then, step
import os
import tempfile
import subprocess
import shutil


@given(u'input data from {source}')
def step_impl(context, source):
    context.source = os.path.join(context.data_path, source)    
    assert os.path.exists(context.source), "Input folder does not exist."

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
    try:
        if "gtiff" in context.command:
            context.compare_command = "../polar2grid_test/viirs/p2g_compare_geotiff.sh " + output + " " + context.temp_dir
        else: 
            context.compare_command = "../polar2grid_test/viirs/p2g_compare_netcdf.sh " + output + " " + context.temp_dir
        exit_status = subprocess.call(context.compare_command, shell=True)
        assert exit_status == 0, "Files did not match with the correct output"
    finally:
        shutil.rmtree(context.temp_dir)

