Using Geo2Grid to Create Animations
-----------------------------------

The advantage of Geostionary Satellites is the temporal resolution of the 
observations.  Geo2Grid offers an easy interface to creating animations from
Geo2Grid GeoTIFF files.  

Create a series of GOES-16 ABI GeoTIFF files from a time sequence of data. In
the bash shell script example below, we use the ABI Full Disk Band 1 files to search for all
files we have available from 19 December 2019. The files for this day are all 
located in the same directory.  I then create true and natural color 
images from all time periods that are available.

.. code-block:: bash

	#!/bin/bash -x

	# Set GEO2GRID environment variables 

	export GEO2GRID_HOME=/home/g2g/geo2grid_v_1_0_0
	export PATH=$PATH:$GEO2GRID_HOME/bin

	# Get input list of files/times based upon ABI Band 1 files

	ls -1 /data/abi16/20181219/OR_ABI-L1b-RadC-M3C01_G16_s2018353*.nc > file_list.txt

	sort_list=$(cat file_list.txt | sort)

        # Make images for each time period available
	for file in ${sort_list} ; do

       		echo ${file}
         	datetime=`basename $file | cut -c27-38`
        	echo "datetime :"$datetime

                # Cut out a box with lat/lon bounds of 23N, 105 to 37N 75W
        	geo2grid.sh -r abi_l1b -w geotiff --ll-bbox -105 23 -75 37 --num-workers 8 -p true_color natural_color -f /data/abi16/20181219/*${datetime}*.nc

	done

	exit 0

