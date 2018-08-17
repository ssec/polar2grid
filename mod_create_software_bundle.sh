#!/usr/bin/env bash
# Create a software bundle
# Usage: ./create_software_bundle.sh <bundle directory> [ShellB3 URL]
# Creates a software bundle directory and a tarball of that directory

#SHELLB3_DEFAULT="ftp://ftp.ssec.wisc.edu/pub/shellb3/ShellB3-Linux-x86_64-20140212-r840-core-cspp.tar.gz"
#SHELLB3_DEFAULT="ftp://ftp.ssec.wisc.edu/pub/ssec/davidh/cspp_common_py27.tar.gz"
BASE_P2G_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PY_DIR="$BASE_P2G_DIR"
BUNDLE_SCRIPTS_DIR="$BASE_P2G_DIR"/swbundle
VCREFL_DIR="$BASE_P2G_DIR"/viirs_crefl
MCREFL_DIR="$BASE_P2G_DIR"/modis_crefl
CACHE_DIR="/tmp"

oops() {
    echo "OOPS: $*"
    echo "FAILURE"
    exit 1
}

cached_download() {
    fn=`basename $1`
    cache_path="${CACHE_DIR}/$fn"
    pushd $CACHE_DIR
    if [ ! -f $cache_path ]; then
        wget $1 || oops "Could not download $1"
    fi
    popd
    cp $cache_path . || oops "Could not copy cached download ${cache_path}"
}

# Command line arguments
if [ $# -eq 1 ]; then
    SB_NAME=$1
else
    echo "ERROR: Invalid Arguments"
    echo "Usage: ./create_software_bundle.sh <bundle name> [ShellB3 URL]"
    exit 1
fi

# get absolute path for bundle directory
SB_NAME=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")

echo "Creating Polar2Grid software bundle $SB_NAME"
#echo "Using ShellB3 $SHELLB3_URL"

# Create the software bundle directory
if [ -d "$SB_NAME" ]; then
    echo "ERROR: Software bundle directory already exists: $SB_NAME"
    exit 1
fi
echo "Creating software bundle output directory"
mkdir -p "$SB_NAME"
cd "$SB_NAME"

## Get the ShellB3 install or copy it if it's already on the system
#if [ "${SHELLB3_URL:0:3}" == "ftp" ] || [ "${SHELLB3_URL:0:4}" == "http" ]; then
#    echo "Downloading ShellB3..."
#    cached_download $SHELLB3_URL
#    echo "Extracting ShellB3 tarball..."
#    tar -xf "$(basename "$SHELLB3_URL")" || oops "Could not extract ShellB3"
#    echo "Removing downloaded ShellB3 tarball"
#    rm -r "$(basename "$SHELLB3_URL")"
#elif [ "${SHELLB3_URL:(-7)}" == ".tar.gz" ] || [ "${SHELLB3_URL:(-7)}" == ".tar.xz" ]; then
#    echo "Extracting ShellB3 tarball from filesystem..."
#    tar -xf "$SHELLB3_URL" || oops "Could not extract ShellB3"
#else
#    echo "Copying ShellB3 directory from filesystem..."
#    cp -r "$SHELLB3_URL" ./ShellB3 || oops "Could not copy ShellB3 from filesystem"
#fi
#
# PATCH: ShellB3 includes some links it shouldn't
#if [ ! -d ${SB_NAME}/common/ShellB3 ]; then
#    mkdir -p common || oops "Couldn't make 'common' directory"
#    mv ShellB3 common/ || oops "Couldn't move ShellB3 to 'common' directory"
#fi
#SHELLB3_DIR="${SB_NAME}/common/ShellB3"
#rm -f "${SHELLB3_DIR}/README.txt"
#rm -f "${SHELLB3_DIR}/tests"
#
# Copy the grid directory
echo "Copying user grid directory to software bundle"
cp -r ${BUNDLE_SCRIPTS_DIR}/grid_configs .
cp -r ${BUNDLE_SCRIPTS_DIR}/colormaps .
cp -r ${BUNDLE_SCRIPTS_DIR}/rescale_configs .

# Download GSHHG Data shapefiles
#mkdir -p gshhg_data || oops "Could not make GSHHG data directory"
#pushd gshhg_data
#echo "Downloading GSHHG shapefiles"
#cached_download http://www.soest.hawaii.edu/pwessel/gshhg/gshhg-shp-2.3.6.zip
#unzip gshhg-shp-2.3.6.zip || oops "Could not unpack GSHHG shapefiles"
#rm gshhg-shp-2.3.6.zip || oops "Could not delete the GSHHG zip file"
#popd

# Create the 'bin' directory
echo "Creating software bundle bin directory..."
cd "$SB_NAME"
mkdir -p bin
cd bin

## Create the VIIRS CREFL utilities
echo "Getting prebuilt VIIRS CREFL binaries..."
cd "$VCREFL_DIR"
make clean
make prebuilt || oops "Couldn't get prebuilt VIIRS CREFL binaries"
chmod a+x cviirs
chmod a+x h5SDS_transfer_rename
mv cviirs "$SB_NAME"/bin
mv h5SDS_transfer_rename "$SB_NAME"/bin
mv CMGDEM.hdf "$SB_NAME"/bin
cp run_viirs_crefl.sh "$SB_NAME"/bin
chmod a+x "$SB_NAME"/bin/run_viirs_crefl.sh

# Create the MODIS CREFL utilities
echo "Getting prebuilt MODIS CREFL binaries..."
cd "$MCREFL_DIR"
make clean
make prebuilt || oops "Couldn't get prebuilt MODIS CREFL binaries"
chmod a+x crefl
mv crefl "$SB_NAME"/bin
mv tbase.hdf "$SB_NAME"/bin
cp run_modis_crefl.sh "$SB_NAME"/bin
chmod a+x "$SB_NAME"/bin/run_modis_crefl.sh

echo "Copying bash scripts to software bundle bin"
cd "$SB_NAME"
cp -P ${BUNDLE_SCRIPTS_DIR}/*.sh ${BUNDLE_SCRIPTS_DIR}/*.txt bin/

# Create python packages
#echo "Creating python packages..."
#export PATH=${SHELLB3_DIR}/bin:$PATH
#cd "$PY_DIR"

make clean

# Have to use 'python setup.py install' because using easy_install on source tarballs doesn't compile extensions for some reason
#CFLAGS="-fno-strict-aliasing -L${SHELLB3_DIR}/lib" INSTALL_DIR="${SHELLB3_DIR}" make all_sdist
#CFLAGS="-fno-strict-aliasing -L${SHELLB3_DIR}/lib" INSTALL_DIR="${SHELLB3_DIR}" make all_install2
#${SHELLB3_DIR}/bin/python setup.py install
#${SHELLB3_DIR}/bin/python -c 'import polar2grid' || oops "Couldn't install polar2grid"


# Copy the release notes to the tarball
cp $BASE_P2G_DIR/NEWS.rst $SB_NAME/RELEASE_NOTES.txt || oops "Couldn't copy release notes to destination directory"

# Create a wmsupload.sh script
cd $SB_NAME/bin
wget http://realearth.ssec.wisc.edu/upload/re_upload -O wmsupload.sh || oops "Couldn't download and create wmsupload.sh script"
chmod u+x wmsupload.sh || oops "Couldn't make wmsupload.sh executable"

# FIXME do I need this / need to include this somewhere else?
# FIXME: Hack to get libproj in to ShellB3 from the system (until it gets provided by ShellB3)
#cd "${SHELLB3_DIR}"/lib64/
#cp -P /usr/lib64/libproj* .

# Copy SatPy configurations
cp -r $BASE_P2G_DIR/etc $SB_NAME/ || oops "Couldn't copy configuration 'etc' directory"

#
## Temporary fix for including pytroll packages
#hacky_install() {
#    pkg_url=$1
#    ${SHELLB3_DIR}/bin/python -m pip install --no-deps --global-option=build_ext --global-option="-L${SHELLB3_DIR}/lib" --global-option="-R\$ORIGIN/../../../.." $pkg_url
#}
#${SHELLB3_DIR}/bin/python -m easy_install http://larch.ssec.wisc.edu/eggs/repos/polar2grid/configobj-5.0.6.tar.gz
#${SHELLB3_DIR}/bin/python -m easy_install http://larch.ssec.wisc.edu/eggs/repos/polar2grid/trollsift-0.1.1.tar.gz
#${SHELLB3_DIR}/bin/python -m easy_install http://larch.ssec.wisc.edu/eggs/repos/polar2grid/trollimage-0.4.0.tar.gz
##${SHELLB3_DIR}/bin/python -m easy_install http://larch.ssec.wisc.edu/eggs/repos/polar2grid/pyresample-1.6.1.tar.gz
#hacky_install http://larch.ssec.wisc.edu/eggs/repos/polar2grid/pyresample-1.7.0.tar.gz
#${SHELLB3_DIR}/bin/python -m easy_install http://larch.ssec.wisc.edu/eggs/repos/polar2grid/PyYAML-3.12.tar.gz
#${SHELLB3_DIR}/bin/python -m easy_install http://larch.ssec.wisc.edu/eggs/repos/polar2grid/pyorbital-1.0.1.tar.gz
#${SHELLB3_DIR}/bin/python -m easy_install --no-deps http://larch.ssec.wisc.edu/eggs/repos/polar2grid/satpy-0.7.5.tar.gz
## Pycoast
#${SHELLB3_DIR}/bin/python -m easy_install http://larch.ssec.wisc.edu/eggs/repos/polar2grid/pyshp-1.2.3.tar.gz
#hacky_install http://larch.ssec.wisc.edu/eggs/repos/polar2grid/aggdraw-1.3.0a.tar.gz
#${SHELLB3_DIR}/bin/python -m easy_install --no-deps http://larch.ssec.wisc.edu/eggs/repos/polar2grid/pycoast-0.7.0a0.tar.gz

# Tar up the software bundle
echo "Creating software bundle tarball..."
cd "$SB_NAME"/..
tar -czf "$(basename "$SB_NAME").tar.gz" "$(basename "$SB_NAME")"

echo "SUCCESS"
