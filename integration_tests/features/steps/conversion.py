from behave import given, when, then, step
import os
import tempfile
import filecmp
import subprocess
import shutil
import logging

path = "/data/test_data/old_polar2grid_data/polar2grid_test"
p2g_path = "/data/dist/polar2grid-swbundle-2.2.1b0/bin"

@given(u'input data from {folder}')
def step_impl(context, folder):
    context.folder_path = os.path.join(path, folder)    
    assert os.path.exists(context.folder_path), "Input folder does not exist."

@when(u'{command} runs') 
def step_impl(context, command):
    context.command = "{} {} {}".format(os.path.join(p2g_path, "polar2grid.sh"), command, context.folder_path)

    orig_dir = os.getcwd()
    try:
        context.temp_dir = tempfile.mkdtemp()
        os.chdir(context.temp_dir)
        subprocess.call(context.command, shell=True)        
    finally:
        os.chdir(orig_dir)
    
    assert os.path.exists(context.temp_dir), "Temporary directory not created"
    assert os.listdir(context.temp_dir), "No files were created"

@then(u'the output matches with the files in {expected}')
def step_impl(context, expected):
    orig_dir = os.getcwd()
    assert os.path.exists(context.temp_dir)
    assert os.listdir(context.temp_dir)
    try:
        os.chdir(os.path.join(context.folder_path, ".."))
        context.compare_command = "./p2g_compare_geotiff.sh " + "./output "  + context.temp_dir
        exit_status = subprocess.call(context.compare_command, shell=True)
        assert exit_status == 1
    finally:
        os.chdir(orig_dir)
        shutil.rmtree(context.temp_dir)

