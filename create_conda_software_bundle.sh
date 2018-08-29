#!/usr/bin/env bash
# Create a software bundle from a conda environment
# Usage: ./create_conda_software_bundle.sh <bundle directory>
# Creates a software bundle directory and a tarball of that directory

#SHELLB3_DEFAULT="ftp://ftp.ssec.wisc.edu/pub/shellb3/ShellB3-Linux-x86_64-20140212-r840-core-cspp.tar.gz"
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

# This assumes that the current conda environment is already active
which conda || oops "Conda environment must be available"
if [ $# -eq 1 ]; then
    SB_NAME=$1
else
    echo "ERROR: Invalid Arguments"
    echo "Usage: ./create_conda_software_bundle.sh <bundle name>"
    exit 1
fi

pip install -U --no-deps . || oops "Couldn't install current polar2grid package"

SB_TARBALL="${SB_NAME}.tar.gz"
conda-pack -o $SB_TARBALL || oops "Couldn't create conda-packed tarball"
mkdir -p ${SB_NAME} || oops "Couldn't make output directory"
tar -xzf ${SB_TARBALL} -C ${SB_NAME} || oops "Couldn't untar conda-packed tarball"
cd ${SB_NAME} || oops "Couldn't change to software bundle directory"

echo "Copying user grid directory to software bundle"
cp -r ${BUNDLE_SCRIPTS_DIR}/grid_configs .
cp -r ${BUNDLE_SCRIPTS_DIR}/colormaps .
cp -r ${BUNDLE_SCRIPTS_DIR}/rescale_configs .

mkdir -p gshhg_data || oops "Could not make GSHHG data directory"
pushd gshhg_data
echo "Downloading GSHHG shapefiles"
cached_download http://www.soest.hawaii.edu/pwessel/gshhg/gshhg-shp-2.3.6.zip
unzip gshhg-shp-2.3.6.zip || oops "Could not unpack GSHHG shapefiles"
rm gshhg-shp-2.3.6.zip || oops "Could not delete the GSHHG zip file"
popd

# Create the VIIRS CREFL utilities
echo "Getting prebuilt VIIRS CREFL binaries..."
cd "$VCREFL_DIR"
make clean
make prebuilt || oops "Couldn't get prebuilt VIIRS CREFL binaries"
chmod a+x cviirs
chmod a+x h5SDS_transfer_rename
mv cviirs "$SB_NAME"/bin/
mv h5SDS_transfer_rename "$SB_NAME"/bin/
mv CMGDEM.hdf "$SB_NAME"/bin/
cp run_viirs_crefl.sh "$SB_NAME"/bin/
chmod a+x "$SB_NAME"/bin/run_viirs_crefl.sh

# Create the MODIS CREFL utilities
echo "Getting prebuilt MODIS CREFL binaries..."
cd "$MCREFL_DIR"
make clean
make prebuilt || oops "Couldn't get prebuilt MODIS CREFL binaries"
chmod a+x crefl
mv crefl "$SB_NAME"/bin/
mv tbase.hdf "$SB_NAME"/bin/
cp run_modis_crefl.sh "$SB_NAME"/bin/
chmod a+x "$SB_NAME"/bin/run_modis_crefl.sh

echo "Copying bash scripts to software bundle bin"
cd "$SB_NAME"
cp -P ${BUNDLE_SCRIPTS_DIR}/*.sh ${BUNDLE_SCRIPTS_DIR}/*.txt bin/ || echo "Couldn't copy scripts to bin/ directory"

# Copy the release notes to the tarball
cp $BASE_P2G_DIR/NEWS.rst $SB_NAME/RELEASE_NOTES.txt || oops "Couldn't copy release notes to destination directory"

# Create a wmsupload.sh script
cd $SB_NAME/bin
wget http://realearth.ssec.wisc.edu/upload/re_upload -O wmsupload.sh || oops "Couldn't download and create wmsupload.sh script"
chmod u+x wmsupload.sh || oops "Couldn't make wmsupload.sh executable"

# Copy SatPy configurations
cp -r $BASE_P2G_DIR/etc $SB_NAME/ || oops "Couldn't copy configuration 'etc' directory"

# Download pyspectral data
echo "Downloading pyspectral data..."
$SB_NAME/bin/download_pyspectral_data.sh || oops "Couldn't download pyspectral data"

# Tar up the software bundle
echo "Creating software bundle tarball..."
cd "$SB_NAME"/..
rm -f ${SB_TARBALL}
tar -czf "$SB_TARBALL" "$(basename "$SB_NAME")"

echo "SUCCESS"
