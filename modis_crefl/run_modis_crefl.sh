#!/bin/bash

# Run crefl corrected reflectance code on MODIS Level 1B 1km, 500m and 250m files. To create the 250m files, you are required to have the 1km, 500m and 250m
# l1b files available.
#
# Kathy.Strabala@ssec.wisc.edu September 2014

# Check arguments
if [ $# -ne 3 ]; then
  echo "Usage: run_modis_crefl.bash MODIS_1KM MODIS_500m MODIS_250m"
  echo "where"
  echo "MODIS_1KM is the 1km MODIS L1B file name"
  echo "MODIS_500m is the 500m MODIS L1B file name"
  echo "MODIS_250m is the 250m MODIS L1B file name"
  echo "Use either standard NASA or IMAPP input file naming conventions."
  echo "Three Output crefl files are created at 1000m, 500m and 250m resolutions."
  echo "Output files use IMAPP naming conventions."
  echo "Example output filename:  a1.YYDDD.HHMM.crefl.1000m.hdf"
  exit 1
fi

# Set up corrected reflectance code
export PATH=/data4/viirs/test/crefl/modis_crefl/crefl:$PATH
export ANCPATH=/data4/viirs/test/crefl/modis_crefl/crefl

# Check the input files
l1b1km_file=$1
if [ ! -r $l1b1km_file ]; then
  echo "Input 1km file not found: "$l1b1km_file
  exit 1
fi
l1b500m_file=$2
if [ ! -r $l1b500m_file ]; then
  echo "Input 500m file not found: "$l1b500m_file
  exit 1
fi
l1b250m_file=$3
if [ ! -r $l1b250m_file ]; then
  echo "Input 250m file not found: "$l1b250m_file
  exit 1
fi

# Get the path and date of the MODIS input files
path=$(dirname $l1b1km_file)

# Check naming conventions
F3=`basename $l1b1km_file | cut -c1-3`
F2=`basename $l1b1km_file | cut -c2`
if [[ "$F3" == "MOD" || "$F3" == "MYD" ]] ; then
  date1=`basename $l1b1km_file | cut -d. -f2-3`
  date=`echo $date1 | cut -c4-13`
  FIL1KM=$l1b1km_file
  FILHKM=$l1b500m_file
  FILQKM=$l1b250m_file
  if [[ "$F2" == "O" ]] ; then
     PREFIX="t1."
  else
     PREFIX="a1."
  fi
  LINK=0
elif [[ "$F2" == "1" ]] ; then
  date=`basename $l1b1km_file | cut -d. -f2-3`
  PREFIX=${F3}
  ln -fs $l1b1km_file MOD021KM.A20${date}.hdf
  ln -fs $l1b500m_file MOD02HKM.A20${date}.hdf
  ln -fs $l1b250m_file MOD02QKM.A20${date}.hdf
  FIL1KM=MOD021KM.A20${date}.hdf
  FILHKM=MOD02HKM.A20${date}.hdf
  FILQKM=MOD02QKM.A20${date}.hdf
  LINK=1
else
  echo "Satellite name incorrect" $SAT
  exit 1
fi


# Run crefl for 1KM Bands
crefl.1.7.1 --verbose --overwrite --1km --of=${PREFIX}$date.crefl.1000m.hdf --bands=1,2,3,4,5,6,7 $FIL1KM
if [ $? -ne 0 ]; then
  echo "Error running MODIS 1km corrected reflectance on input file "$FIL1KM
  exit 1
fi

# Run crefl for 500m Bands
crefl.1.7.1 --verbose --overwrite --500m --of=${PREFIX}$date.crefl.500m.hdf --bands=1,2,3,4,5,6,7 $FIL1KM $FILHKM
if [ $? -ne 0 ]; then
  echo "Error running MODIS 500m corrected reflectance on input file "$FILHKM
  exit 1
fi

# Run crefl for 250m Bands
crefl.1.7.1 --verbose --overwrite --of=${PREFIX}$date.crefl.250m.hdf --bands=1,2,3,4 $FIL1KM $FILHKM $FILQKM
if [ $? -ne 0 ]; then
  echo "Error running MODIS 250m corrected reflectance on input file "$FILQKM
  exit 1
fi

# Clean up and exit
if  [ $LINK -eq 1 ]; then
    unlink $FIL1KM
    unlink $FILHKM
    unlink $FILQKM
fi

exit 0
