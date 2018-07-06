from behave import given, when, then, step
import os
import tempfile
import subprocess
import shutil


@given(u'input data from {folder}')
def step_impl(context, folder):
    context.folder = os.path.join(context.data_path, folder)
    context.folder_path = os.path.join(context.folder, "input")    
    assert os.path.exists(context.folder_path), "Input folder does not exist."

@when(u'{command} runs') 
def step_impl(context, command):
    context.command = "{} {} {}".format(os.path.join(context.p2g_path, "polar2grid.sh"), command, context.folder_path)

    orig_dir = os.getcwd()
    try:
        context.temp_dir = tempfile.mkdtemp()
        os.chdir(context.temp_dir)
        subprocess.call(context.command, shell=True)        
    finally:
        os.chdir(orig_dir)
    
    assert os.path.exists(context.temp_dir), "Temporary directory not created"
    assert os.listdir(context.temp_dir), "No files were created"

@then(u'the output matches with the verified files')
def step_impl(context):
    orig_dir = os.getcwd()
    print(orig_dir)
    try:
        print(context.folder)
        os.chdir(context.folder)
        context.compare_command = "./p2g_compare_geotiff.sh " + "./output "  + context.temp_dir
        exit_status = subprocess.call(context.compare_command, shell=True)
        assert exit_status == 0, "Files did not match with the correct output"
    finally:
        os.chdir(orig_dir)
        shutil.rmtree(context.temp_dir)

