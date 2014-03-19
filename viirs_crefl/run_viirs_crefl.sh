#!/bin/bash

# Run cviirs corrected reflectance code on VIIRS M-band and I-band SDR data
# Liam.Gumley@ssec.wisc.edu 2013-02-28
# Modified by David Hoese, david.hoese@ssec.wisc.edu

# Check arguments
if [ $# -ne 1 ]; then
  echo "Usage: run_viirs_crefl.bash SVM05_FILE"
  echo "where SVM05_FILE is the full path and name of the VIIRS M-band SVM05 HDF5 file."
  echo "All VIIRS M-band and I-band SDR HDF5 files and the corresponding GMTCO file must be in the same directory."
  exit 1
fi

# Check the input file
input_file=$1
if [ ! -r $input_file ]; then
  echo "Input file not found: "$input_file
  exit 1
fi

# Get the path and date of the SVM05 granule (e.g., '/data/viirs', 'npp_d20120625_t1830592_e1842598')
path=$(dirname $input_file)
date=$(basename $input_file | cut -d_ -f2-5)

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Set up preprocessing code
export PATH=$script_dir/bin:$PATH
# Set up corrected reflectance code
export ANCPATH=$script_dir


# Convert geolocation data to HDF4
gmtco_file=$(find $path -name GMTCO_${date}\*)
svm_file=NPP_VMAE_L1.hdf
h5SDS_transfer_rename $gmtco_file $svm_file Latitude Latitude
h5SDS_transfer_rename $gmtco_file $svm_file Longitude Longitude
h5SDS_transfer_rename $gmtco_file $svm_file SatelliteAzimuthAngle SenAziAng_Mod
h5SDS_transfer_rename $gmtco_file $svm_file SatelliteZenithAngle SenZenAng_Mod
h5SDS_transfer_rename $gmtco_file $svm_file SolarZenithAngle SolZenAng_Mod
h5SDS_transfer_rename $gmtco_file $svm_file SolarAzimuthAngle SolAziAng_Mod

# Convert VIIRS M-band SDR files to HDF4
# Note: VIIRS M-bands 5,7,3,4,8,10,11 corrrespond to MODIS bands 1,2,3,4,5,6,7
band_list='05 07 03 04 08 10 11'
for band in $band_list; do
  file=$(find $path -name SVM${band}_${date}\*)
  h5SDS_transfer_rename $file $svm_file Reflectance Reflectance_Mod_M$(echo $band | bc)
done

# Convert VIIRS I-band SDR files to HDF4
# Note: VIIRS I-bands 1,2,3 corrrespond to MODIS bands 1,2,6
svi_file=NPP_VIAE_L1.hdf
band_list='01 02 03'
for band in $band_list; do
  file=$(find $path -name SVI${band}_${date}\*)
  h5SDS_transfer_rename $file $svi_file Reflectance Reflectance_Img_I$(echo $band | bc)
done

# Run crefl for M-bands
cviirs --overwrite --verbose --1km --bands='1,2,3,4,5,6,7' --of=CREFLM_$date.hdf $svm_file
if [ $? -ne 0 ]; then
  echo "Error running VIIRS M-band corrected reflectance on input file "$svm_file
  exit 1
fi

# Run crefl for I-bands
cviirs --overwrite --verbose --500m  --bands='8,9,10' --of=CREFLI_$date.hdf $svm_file $svi_file
if [ $? -ne 0 ]; then
  echo "Error running VIIRS I-band corrected reflectance on input file "$svi_file
  exit 1
fi

# Clean up and exit
rm $svm_file $svi_file
exit 0

