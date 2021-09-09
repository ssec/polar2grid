Using Geo2Grid to Create Animations
-----------------------------------

The advantage of Geostationary Satellites is the temporal resolution of the
observations.  Geo2Grid offers an easy interface to creating animations from
Geo2Grid GeoTIFF files.  The following example demonstrates how
Geo2Grid software can be used to create an animation of 
files from a latitude/longitude subset of GOES-16 ABI CONUS GeoTIFF images 
located over the Southeastern United States.

Create a series of GOES-16 ABI GeoTIFF files from a time sequence of data. In
the bash shell script example below, I use the ABI CONUS Band 1 files to 
search for all files we have available from 4 January 2019. The files for 
this day are all located in the same directory.  I then create true and 
natural color images from all time periods that are available. 

.. code-block:: bash

	#!/bin/bash

	# Set GEO2GRID environment variables 

	export GEO2GRID_HOME=/home/g2g/geo2grid_v_1_0_2
	export PATH=$PATH:$GEO2GRID_HOME/bin

	# Get input list of files/times based upon ABI Band 1 files

	ls -1 /data/abi16/20190104/OR_ABI-L1b-RadC-M3C01_G16_s2019004*.nc > file_list.txt

	sort_list=$(cat file_list.txt | sort)

        # Make images for each time period available
	for file in ${sort_list} ; do

       		echo ${file}
                # get date/time for geo2grid file search
         	datetime=`basename $file | cut -c27-38`
        	echo "datetime :"$datetime

                # Cut out a box with lat/lon bounds of 23N, 105W to 37N 75W
                geo2grid.sh -r abi_l1b -w geotiff --ll-bbox -105 23 -75 37 --num-workers 8 -p true_color natural_color -f /data/abi16/20190104/*${datetime}*.nc

	done

	exit 0

This script created 120 GeoTIFF images for my time period 10:00 UTC through 20:00 UTC, 
with a time step of every 5 minutes. 

To create a 120 image animation, I use the Geo2Grid utility script
``gtiff2mp4.sh``.

.. code-block:: bash

    gtiff2mp4.sh my_true_color_animation.mp4  *true_color*.tif

The script wraps the ``ffmpeg`` video software, and combines all of the
``*true_color*.tif`` files found in the directory into an animation
based upon defaults that make the output animations most compatible
with modern video players. The output frame rate is 24 frames per 
second. The images will automatically be resized if they are
large in order to ensure a smooth animation. I chose an output
filename of ``my_true_color_animation.mp4``. The software can also
create animations from input ``.png`` files.

The figure below is the last image in the 120 loop sequence.  The
output MP4 animation is available for viewing at `this site <ftp://ftp.ssec.wisc.edu/pub/CSPP/g2g_examples/abi/my_true_color_animation.mp4>`_.

.. figure:: ../_static/example_images/GOES-16_ABI_RadC_true_color_20190104_195718_GOES-East.png
    :width: 100%
    :align: center

    The last GOES-16 ABI image from the 120 frame loop created with data from 4 January 2019.  The image observations are from 19:57 UTC.
