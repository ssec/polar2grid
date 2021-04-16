from behave import given, when, then
import os
import tempfile
import subprocess
import shutil
import glob


@given("input data from {source}")
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


@when("{command} runs")
def step_impl(context, command):
    context.script = command.split()[0]
    context.command = "datapath={}; /usr/bin/time {} {}".format(
        context.datapath, os.path.join(context.p2g_path, command), context.source
    )

    # creating new data in temporary directory to compare
    orig_dir = os.getcwd()
    try:
        context.temp_dir = tempfile.mkdtemp(prefix="p2g_tests_")
        os.chdir(context.temp_dir)
        exit_status = subprocess.call(context.command, shell=True)
        assert exit_status == 0, "{} ran unsuccessfully".format(context.command)
    finally:
        os.chdir(orig_dir)

    assert os.path.exists(context.temp_dir), "Temporary directory not created"
    assert os.listdir(context.temp_dir), "No files were created"


@then("the output matches with the files in {output}")
def step_impl(context, output):
    orig_dir = os.getcwd()
    try:
        os.chdir(context.datapath)
        # NOTE: 81231 / 151404144 (0.054%) pixels are currently wrong in VIIRS_L1B.
        compare_command = " ".join(
            [
                os.path.join(context.p2g_path, "p2g_compare.sh"),
                output,
                context.temp_dir,
                "-vv",
                "--margin-of-error",
                str(81231 / 1514041.44),
            ]
        )
        exit_status = subprocess.call(compare_command, shell=True)
        assert exit_status == 0, "Files did not match with the correct output"
    finally:
        os.chdir(orig_dir)
        shutil.rmtree(context.temp_dir)


@when("{command} runs with --list-products")
def step_impl(context, command):
    context.script = command.split()[0]
    context.command = "datapath={}; /usr/bin/time {} {} --list-products".format(
        context.datapath, os.path.join(context.p2g_path, command), context.source
    )

    # creating new data in temporary directory to compare
    orig_dir = os.getcwd()
    try:
        context.temp_dir = tempfile.mkdtemp(prefix="p2g_tests_")
        os.chdir(context.temp_dir)
        output = subprocess.check_output(context.command, shell=True)
        context.output = output.decode("utf-8")
    finally:
        os.chdir(orig_dir)

    assert os.path.exists(context.temp_dir), "Temporary directory not created"
    assert os.listdir(context.temp_dir), "No files were created"


@then("the printed output includes the products in {output}")
def step_impl(context, output):
    names_to_check = output.split(",")
    output = context.output
    for product_name in names_to_check:
        num_products_in_output = output.count(product_name + "\n")
        assert num_products_in_output != 0, f"Missing {product_name} in command output"
        assert num_products_in_output == 1, f"Too many of {product_name} in command output"
