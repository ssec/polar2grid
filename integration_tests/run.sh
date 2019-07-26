#!/bin/bash
# Script for jenkins to run tests on polar2grid.

set -exf
export PATH="/usr/local/texlive/2019/bin/x86_64-linux":$PATH
cd "$WORKSPACE"
# Activate conda for bash.
/data/users/davidh/miniconda3/bin/conda init bash
# Restart the shell to enable conda.
source ~/.bashrc
conda env update -n jenkins_p2g_env -f build_environment.yml --prune
conda activate jenkins_p2g_env

# Handle release vs test naming.
end="`date +"%Y%m%d-%H%M%S"`"
prefix="$(cut -d'-' -f1 <<<"$GIT_TAG_NAME")"
version="$(cut -d'-' -f2 <<<"$GIT_TAG_NAME")"
# If the tag is correct, make a version release.
if [[ ("$prefix" = p2g || "$prefix" = g2g) && ! -z "$version" && "$prefix" != "$version" ]]; then
    end="$version"
fi
if [[ "$prefix" = "g2g" ]]; then
    prefix=geo
else
    prefix=polar
fi
tarball_name=${prefix}2grid-swbundle-$end

./create_conda_software_bundle.sh $WORKSPACE/$tarball_name
export POLAR2GRID_HOME="$WORKSPACE/$tarball_name"
cd "$WORKSPACE/integration_tests"
behave --no-logcapture --no-color --no-capture -D datapath=/data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data

# Only ran by Jenkins if build was successful and correct version tag was added.
# Save software bundle.
rm -rf /tmp/${prefix}2grid-*
mkdir /tmp/${prefix}2grid-$end
cp -r "$WORKSPACE/$tarball_name" /tmp/${prefix}2grid-$end
# Make docs.
conda update -n jenkins_p2g_env sphinx
pip install sphinx-argparse
cd "$WORKSPACE"/doc
make latexpdf POLAR2GRID_DOC=$prefix
cp -r "$WORKSPACE"/doc/build/latex /tmp/${prefix}2grid-$end
# Clear out intermediate results and rebuild for HTML document.
make clean
# Needs to be second since Jenkins makes an html in workspace from the file generated by this command.
make html POLAR2GRID_DOC=$prefix
cp -r "$WORKSPACE"/doc/build/html /tmp/${prefix}2grid-$end
chmod a+rx /tmp/${prefix}2grid-$end
if [[ $end = "$version" ]]; then
    cp -r /tmp/${prefix}2grid-$end /data/tmp/${prefix}2grid-$end
fi