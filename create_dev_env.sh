#!/usr/bin/env bash
# Install polar2grid software in a standalone environment that can be used for development
# Usage: ./create_dev_env.sh <base directory>
# Creates a development environment into the provided base directory. This script assumes it is being run from a git
# source repository clone.
# NOTE: ShellB3 is only x86_64 RHEL5+ compatible

SHELLB3_DEFAULT="ftp://ftp.ssec.wisc.edu/pub/shellb3/ShellB3-Linux-x86_64-20140212-r840-core-cspp.tar.gz"
BASE_REPOS_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PY_DIR="$BASE_REPOS_DIR"/py
VCREFL_DIR="$BASE_REPOS_DIR"/viirs_crefl
MCREFL_DIR="$BASE_REPOS_DIR"/modis_crefl
MS2GT_DIR="$BASE_REPOS_DIR"/ms2gt/src/fornav
DEBUG=true

oops() {
    echo "OOPS: $*"
    echo "FAILURE"
    exit 1
}

debug() {
    if ${DEBUG}; then
        echo "DEBUG: $*"
    fi
}

# Parameter
if [ $# -eq 1 ]; then
    DEV_DIR=$(realpath "$1")
else
    echo "ERROR: Invalid Arguments"
    echo "Usage: ./create_dev_env.sh <base directory>"
    exit 1
fi
echo "Creating development environment directory: $DEV_DIR"
mkdir -p ${DEV_DIR}
cd ${DEV_DIR}

echo "###################################################################################################"
USE_SHELLB3=false
SHELLB3_URL="$SHELLB3_DEFAULT"
echo "Do you want to use ShellB3 (RHEL5+ only) as your python environment (enter choice number)?"
select yn in "Yes" "No"; do
    case ${yn} in
        Yes ) USE_SHELLB3=true; break;;
        No ) break;;
    esac
done

if ${USE_SHELLB3}; then
    echo "###################################################################################################"
    echo "Use default ShellB3 (`basename ${SHELLB3_DEFAULT}`)?"
    select yn in "Yes" "No"; do
        case ${yn} in
            Yes ) break;;
            No ) read -p "Alternate ShellB3 URL/Location: " SHELLB3_URL; break;;
        esac
    done
fi

# Ask if they want the optional VIIRS CREFL software
BUILD_VIIRS_CREFL=false
echo "###################################################################################################"
echo "Attempt to build and install VIIRS CREFL (required for creating true color images from VIIRS SDRs)?"
select yn in "Yes" "No"; do
    case ${yn} in
        Yes ) BUILD_VIIRS_CREFL=true; break;;
        No ) break;;
    esac
done

# Ask if they want the optional MODIS CREFL software
BUILD_MODIS_CREFL=false
echo "###################################################################################################"
echo "Attempt to build and install MODIS CREFL (required for creating true color images from MODIS SDRs)?"
select yn in "Yes" "No"; do
    case ${yn} in
        Yes ) BUILD_MODIS_CREFL=true; break;;
        No ) break;;
    esac
done

if ${USE_SHELLB3}; then
    echo "###################################################################################################"

    debug "ShellB3 URL is: $SHELLB3_URL"
    if [ "${SHELLB3_URL:(-7)}" == ".tar.gz" ]; then
        DOWNLOADED=false
        if [ "${SHELLB3_URL:0:3}" == "ftp" ] || [ "${SHELLB3_URL:0:4}" == "http" ]; then
            echo "Downloading ShellB3: $SHELLB3_URL"
            wget ${SHELLB3_URL} || oops "Could not download ShellB3"
            SHELLB3_URL="$DEV_DIR/$(basename "$SHELLB3_URL")"
            echo "Downloaded ShellB3 tarball to $SHELLB3_URL"
            DOWNLOADED=true
        fi

        # Extract it if we need to (either from a local tarball or downloaded tarball)
        echo "Extracting ShellB3 tarball..."
        tar -xzf "$SHELLB3_URL" || oops "Could not extract ShellB3"

        if ${DOWNLOADED}; then
            echo "Removing downloaded ShellB3 tarball"
            rm -r "$(basename "$SHELLB3_URL")"
        fi

        # Update ShellB3 URL
        SHELLB3_URL="$DEV_DIR/ShellB3"
    elif [ -d "$SHELLB3_URL" ]; then
        # If we have a local directory then just add it to the PATH so we can use it
        echo "Will attempt to use local environment: $SHELLB3_URL"
    else
        echo "Could not recognize ShellB3. Use .tar.gz or an existing ShellB3 directory"
        exit 2
    fi

    debug "ShellB3 URL (before python check): $SHELLB3_URL"
    if [ ! -f "$SHELLB3_URL/bin/python" ]; then
        # needed for package install
        echo "Couldn't find python interpreter in local $SHELLB3_URL/bin/python"
        exit 2
    fi

    echo "Temporarily modifying PATH to install python packages..."
    export PATH="$SHELLB3_URL/bin":$PATH
    debug "PATH is $PATH"
fi

echo "Will use this python executable for package installation: `which python`"

# Create a bin directory and start putting stuff in it
echo "###################################################################################################"
echo "Creating development 'bin' directory"
mkdir -p bin

# Compile ms2gt
echo "Building ms2gt"
cd "$MS2GT_DIR"
make clean
make || oops "Could not build fornav from source"
echo "Copying ms2gt to development bin directory"
cp fornav "$DEV_DIR/bin/"

# Install python packages
echo "Creating 'python' directory in development environment where python packages will be installed"
cd "$DEV_DIR"
mkdir -p python
cd "$PY_DIR"
echo "Installing python packages in development mode"
export PYTHONPATH="$DEV_DIR/python:$PYTHONPATH"
INSTALL_DIR="$DEV_DIR/python" make all_dev || oops "Couldn't install python packages in development mode"

# Checking that python packages were installed
echo "Running simple import test to make sure packages can be imported"
python -c "from polar2grid import glue" || oops "Couldn't import python package"
echo "Simple import test passed"

# Compile VIIRS CREFL code
VIIRS_CREFL_MSG=""
if ${BUILD_VIIRS_CREFL}; then
    echo "Building VIIRS CREFL"
    cd "$VCREFL_DIR"

    if [ -z "$LDFLAGS" ] && ${USE_SHELLB3}; then
        echo "Will use libaries from ShellB3 for linking VIIRS CREFL"
        export LDFLAGS="-I${SHELLB3_URL}/include -L${SHELLB3_URL}/lib"
        export LD_RUN_PATH="${SHELLB3_URL}/lib:${LD_RUN_PATH}"
    fi
    debug "LDFLAGS: $LDFLAGS"
    debug "CFLAGS: $CFLAGS"
    make clean
    make all_dynamic
    if [ $? -ne 0 ]; then
        echo "Could not compile VIIRS CREFL (CFLAGS and LDFLAGS should propagate to build commands if needed)"
        # don't fail here, this is an optional component anyway. Continue with the script even though this failed
        VIIRS_CREFL_MSG=" (except VIIRS CREFL)"
    else
        # fail if the install fails since that is the "simple" part, if this doesn't pass then something is wrong
        echo "CREFL compiled successfully, now installing"
        PREFIX="$DEV_DIR" make install || oops "Could not install VIIRS CREFL files into development environment"
    fi
fi

if ${BUILD_MODIS_CREFL}; then
    echo "Building MODIS CREFL"
    cd "$MCREFL_DIR"

    if [ -z "$LDFLAGS" ] && ${USE_SHELLB3}; then
        echo "Will use libaries from ShellB3 for linking MODIS CREFL"
        export LDFLAGS="-I${SHELLB3_URL}/include -L${SHELLB3_URL}/lib"
        export LD_RUN_PATH="${SHELLB3_URL}/lib:${LD_RUN_PATH}"
    fi
    debug "LDFLAGS: $LDFLAGS"
    debug "CFLAGS: $CFLAGS"
    make clean
    make all_dynamic
    if [ $? -ne 0 ]; then
        echo "Could not compile MODIS CREFL (CFLAGS and LDFLAGS should propagate to build commands if needed)"
        # don't fail here, this is an optional component anyway. Continue with the script even though this failed
        MODIS_CREFL_MSG=" (except MODIS CREFL)"
    else
        # fail if the install fails since that is the "simple" part, if this doesn't pass then something is wrong
        echo "CREFL compiled successfully, now installing"
        PREFIX="$DEV_DIR" make install || oops "Could not install MODIS CREFL files into development environment"
    fi
fi

echo "###################################################################################################"
echo "Polar2Grid development environment was successfully installed$VIIRS_CREFL_MSG$MODIS_CREFL_MSG"
echo "Add the following lines to your .bash_profile or .bashrc file to use it:"
echo "    export PYTHONPATH=${DEV_DIR}/python:"'$PYTHONPATH'
if ${USE_SHELLB3}; then
    echo "    export PATH=${DEV_DIR}/bin:${SHELLB3_URL}/bin:"'$PATH'
else
    echo "    export PATH=${DEV_DIR}/bin:"'$PATH'
fi
