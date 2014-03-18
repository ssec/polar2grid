#!/usr/bin/env bash
# Create a software bundle
# Usage: ./create_software_bundle.sh <bundle directory> [ShellB3 URL]

SHELLB3_DEFAULT="ftp://ftp.ssec.wisc.edu/pub/shellb3/ShellB3-Linux-x86_64-20140212-r840-core-cspp.tar.gz"
MS2GT_DOWNLOAD="http://www.ssec.wisc.edu/~davidh/polar2grid/ms2gt/ms2gt0.24a.tar.gz"
BASE_P2G_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
PY_DIR="$BASE_P2G_DIR"/py
BUNDLE_SCRIPTS_DIR="$BASE_P2G_DIR"/swbundle

oops() {
    echo "OOPS: $*"
    echo "FAILURE"
    exit 1
}

# Command line arguments
if [ $# -eq 1 ]; then
    SB_NAME=$1
    SHELLB3_URL=$SHELLB3_DEFAULT
elif [ $# -eq 2 ]; then
    SB_NAME=$1
    SHELLB3_URL=$2
else
    echo "ERROR: Invalid Arguments"
    echo "Usage: ./create_software_bundle.sh <bundle name> [ShellB3 URL]"
    exit 1
fi

# get absolute path for bundle directory
SB_NAME=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")

echo "Creating Polar2Grid software bundle $SB_NAME"
echo "Using ShellB3 $SHELLB3_URL"

# Create the software bundle directory
if [ -d "$SB_NAME" ]; then
    echo "ERROR: Software bundle directory already exists: $SB_NAME"
    exit 1
fi
echo "Creating software bundle output directory"
mkdir -p "$SB_NAME"
cd "$SB_NAME"

# Get the ShellB3 install or copy it if it's already on the system
if [ "${SHELLB3_URL:0:3}" == "ftp" ] || [ "${SHELLB3_URL:0:4}" == "http" ]; then
    echo "Downloading ShellB3..."
    wget $SHELLB3_URL || oops "Could not download ShellB3"
    echo "Extracting ShellB3 tarball..."
    tar -xzf "$(basename "$SHELLB3_URL")" || oops "Could not extract ShellB3"
    echo "Removing downloaded ShellB3 tarball"
    rm -r "$(basename "$SHELLB3_URL")"
elif [ ${SHELLB3_URL:(-6)} == ".tar.gz" ]; then
    echo "Extracting ShellB3 tarball from filesystem..."
    # FIXME: Test that this goes to the correct directory
    tar -xzf "$(basename "$SHELLB3_URL")" || oops "Could not extract ShellB3"
else
    echo "Copying ShellB3 directory from filesystem..."
    # FIXME: Test that this goes to the correct directory
    cp -r "$SHELLB3_URL" ./ShellB3 || oops "Could not copy ShellB3 from filesystem"
fi
# PATCH: ShellB3 includes some links it shouldn't
rm -f "ShellB3/README.txt"
rm -f "ShellB3/tests"

# Copy the grid directory
echo "Copying user grid directory to software bundle"
cp -r $BUNDLE_SCRIPTS_DIR/grid_configs .

# Create ms2gt binaries (use prebuilt milliCentOS5)
echo "Downloading ms2gt prebuilt binaries..."
wget $MS2GT_DOWNLOAD || oops "Could now download ms2gt"
echo "Extracting ms2gt binaries..."
tar -xzf "$(basename "$MS2GT_DOWNLOAD")"
echo "Removing downloaded ms2gt tarball"
rm -r "$(basename "$MS2GT_DOWNLOAD")"

# Create the 'bin' directory
echo "Copying bash scripts to software bundle bin"
mkdir bin
cp $BUNDLE_SCRIPTS_DIR/* bin/
echo "Linking to ms2gt binaries..."
ln -s ../ms2gt/bin/ll2cr bin/ll2cr
ln -s ../ms2gt/bin/fornav bin/fornav

# Create python packages
echo "Creating python packages..."
cd "$PY_DIR"
make clean_sdist
make all_sdist
#FIXME: Can this be done with pip? Let's get into this century of software development
# FIXME: Check exit status codes
echo "Installing python packages into ShellB3 environment..."
$SB_NAME/ShellB3/bin/python -m easy_install dist/*.tar.gz || oops "Could not install python packages"

# Tar up the software bundle
cd "$SB_NAME"
cd ..
tar -czf "$(basename "$SB_NAME").tar.gz" "$SB_NAME"

