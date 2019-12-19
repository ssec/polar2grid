#!/usr/bin/env bash
# Create a software bundle
# Usage: ./create_software_bundle.sh <bundle directory>
# Creates a software bundle directory and a tarball of that directory

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
    echo "Usage: ./create_software_bundle.sh <bundle name>"
    exit 1
fi

# get absolute path for bundle directory
SB_NAME=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")

echo "Creating Polar2Grid software bundle $SB_NAME"

# Create the software bundle directory
if [ -d "$SB_NAME" ]; then
    echo "ERROR: Software bundle directory already exists: $SB_NAME"
    exit 1
fi
echo "Creating software bundle output directory"
mkdir -p "$SB_NAME"
cd "$SB_NAME"

# Copy the grid directory
echo "Copying user grid directory to software bundle"
cp -r ${BUNDLE_SCRIPTS_DIR}/grid_configs .
cp -r ${BUNDLE_SCRIPTS_DIR}/colormaps .
cp -r ${BUNDLE_SCRIPTS_DIR}/rescale_configs .

#FIXME does not work currently
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

make clean

# Inject environment code into swbundle only.
for file in `echo *.sh`; do
    cp "$file" tmp.sh
    sed "s/# __SWBUNDLE_ENVIRONMENT_INJECTION__/source \$POLAR2GRID_HOME\/bin\/env.sh/g" tmp.sh > "$file"
done
rm tmp.sh

# Copy the release notes to the tarball
cp $BASE_P2G_DIR/NEWS.rst $SB_NAME/RELEASE_NOTES.txt || oops "Couldn't copy release notes to destination directory"

# Create a wmsupload.sh script
cd $SB_NAME/bin
wget http://realearth.ssec.wisc.edu/upload/re_upload -O wmsupload.sh || oops "Couldn't download and create wmsupload.sh script"
chmod u+x wmsupload.sh || oops "Couldn't make wmsupload.sh executable"

# FIXME need libproj?

# Copy SatPy configurations. Note: Contents are already in etc/satpy thanks to setup.py.
cp -r $BASE_P2G_DIR/etc $SB_NAME/ || oops "Couldn't copy configuration 'etc' directory"

# Tar up the software bundle
echo "Creating software bundle tarball..."
cd "$SB_NAME"/..
tar -czf "$(basename "$SB_NAME").tar.gz" "$(basename "$SB_NAME")"

echo "SUCCESS"
