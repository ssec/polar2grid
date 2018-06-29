import os
import subprocess
from argparse import ArgumentParser
import logging
import filecmp
import sys
import shutil
import yaml

LOG = logging.getLogger(__name__)

def run_test(p2g_path, test, base_dir):
    source = os.path.join(base_dir, test["source_dir"])
    command = test["command"]
    expected_dir = os.path.join(base_dir, test["expected_dir"]) 

    p2g_path = os.path.join(p2g_path, command) + " "  + source

    orig_dir = os.getcwd()
    try: 
        # FIXME delete later
        if not os.path.isdir(expected_dir):
            os.makedirs(expected_dir) 
            os.chdir(expected_dir)
            subprocess.call(p2g_path, shell=True)
            os.chdir(orig_dir)
        
        if not os.path.isdir("./tmp"):
            os.makedirs("./tmp")
        os.chdir("./tmp")
        subprocess.call(p2g_path, shell=True)
        
        for dirpaths, dirs, files in os.walk(expected_dir):
            for f in files: 
                if os.path.isfile(f):
                    if filecmp.cmp(f, os.path.join(dirpaths, f)):
                        LOG.info("Files match")
                else:
                    raise Exception("files do not match")
    finally:
        os.chdir(orig_dir)
    
    shutil.rmtree("./tmp")    


def main():
    parser = ArgumentParser()
    parser.add_argument("p2g_dir", help="Path to polar2grid.sh directory")
    parser.add_argument("yaml", help="The YAML configuration file")
    args = parser.parse_args()
    
    p2g_path = args.p2g_dir
    yfilename = args.yaml
    
    stream = file(yfilename, "r")
    yfile = yaml.load(stream)

    for test in yfile["tests"]:
        run_test(p2g_path, test, yfile["base_test_dir"])
  

if __name__ == "__main__":
    sys.exit(main())

