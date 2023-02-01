"""Various behavior test steps."""
import glob
import os
import re
import shutil
import subprocess
import tempfile

from behave import given, then, when

DTYPE_REGEX = re.compile(r"--dtype (P?<dtype>\S+) ")


@given("input data from {source}")
def step_impl_input_data(context, source):
    new_source = ""

    for f in source.split(" "):
        f = os.path.join(context.datapath, f)
        new_source += f + " "

        if "*" in os.path.basename(f):
            assert glob.glob(f), "Input files {} do  not exist".format(f)
            assert os.path.exists(os.path.dirname(f)), "Input folder {} does not exist".format(os.path.dirname(f))
        else:
            assert os.path.exists(f), "Input {} does not exist".format(f)

    context.source = new_source.rstrip()


@given("an empty working directory")
def step_impl_empty_work_dir(context):
    context.temp_dir = tempfile.mkdtemp(prefix=os.path.join(context.base_temp_dir, "p2g_tests_"))


@given("input data is copied to the working directory")
def step_impl_copy_input_data(context):
    new_source = ""
    for input_dir in context.source.split(" "):
        for input_filename in os.listdir(input_dir):
            new_path = os.path.join(context.temp_dir, os.path.basename(input_filename))
            new_source += new_path + " "
            shutil.copy(os.path.join(input_dir, input_filename), new_path)

    context.source = new_source.rstrip()


@when("{command} runs")
def step_impl_run_command(context, command):
    context.script = command.split()[0]
    context.command = "datapath={}; /usr/bin/time {} {}".format(
        context.datapath, os.path.join(context.p2g_path, os.path.expandvars(command)), context.source
    )

    # creating new data in temporary directory to compare
    orig_dir = os.getcwd()
    temp_dir = getattr(context, "temp_dir", orig_dir)
    try:
        os.chdir(temp_dir)
        exit_status = subprocess.call(context.command, shell=True)
        assert exit_status == 0, "{} ran unsuccessfully".format(context.command)
    finally:
        os.chdir(orig_dir)


@then("the same filenames as in {output} were produced")
def step_impl_match_output_filenames(context, output):
    for exp_filename in os.listdir(os.path.join(context.datapath, output)):
        assert os.path.isfile(os.path.join(context.temp_dir, exp_filename))


@then("the output matches with the files in {output}")
def step_impl_match_output_files(context, output):
    orig_dir = os.getcwd()
    dtype = _get_dtype_from_command(context.command)
    try:
        os.chdir(context.datapath)
        # NOTE: 81231 / 151404144 (0.054%) pixels are currently wrong in VIIRS_L1B.
        compare_command = [
            "python3",
            "-m",
            "polar2grid.compare",
            output,
            context.temp_dir,
            "-vv",
            "--dtype",
            dtype or "float32",
            "--margin-of-error",
            str(81231 / 1514041.44),
        ]
        if context.html_dst:
            html_path = _html_output_filename(context, output)
            compare_command.extend(["--html", html_path])
        exit_status = subprocess.call(" ".join(compare_command), shell=True)
        assert exit_status == 0, "Files did not match with the correct output"
    finally:
        os.chdir(orig_dir)


def _html_output_filename(context, output_dir: str) -> str:
    html_fn = os.path.join(context.html_dst, "{}.html".format(output_dir))
    return os.path.join(context.temp_dir, html_fn)


@when("{command} runs with --list-products")
def step_impl_run_list_products(context, command):
    context.script = command.split()[0]
    context.command = "datapath={}; /usr/bin/time {} {} --list-products".format(
        context.datapath, os.path.join(context.p2g_path, command), context.source
    )

    # creating new data in temporary directory to compare
    orig_dir = os.getcwd()
    try:
        context.temp_dir = tempfile.mkdtemp(prefix=os.path.join(context.base_temp_dir, "p2g_tests_"))
        os.chdir(context.temp_dir)
        output = subprocess.check_output(context.command, shell=True)
        context.output = output.decode("utf-8")
    finally:
        os.chdir(orig_dir)

    assert os.path.exists(context.temp_dir), "Temporary directory not created"
    assert os.listdir(context.temp_dir), "No files were created"


@then("the printed output includes the products in {output}")
def step_impl_compare_output(context, output):
    orig_dir = os.getcwd()
    names_to_check = output.split(",")
    output = context.output
    try:
        for product_name in names_to_check:
            num_products_in_output = output.count(f"\n{product_name}\n")
            assert num_products_in_output != 0, f"Missing {product_name} in command output"
            assert num_products_in_output == 1, f"Too many of {product_name} in command output"
    finally:
        os.chdir(orig_dir)


def _get_dtype_from_command(cmd_str):
    match_res = DTYPE_REGEX.match(cmd_str)
    if match_res is None:
        return None
    return match_res.match_dict()["dtype"]
