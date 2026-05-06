Using Geo2Grid to Create Animations
-----------------------------------

The advantage of Geostationary Satellites is the temporal resolution of the
observations. Geo2Grid offers an easy interface for creating animations from
Geo2Grid GeoTIFF and PNG files. The following example demonstrates how
Geo2Grid software can be used to create an animation of
files from a latitude/longitude subset of GOES-19 ABI Mesoscale Sector images
centered over Hurricane Melissa in October 2025.

Create a series of GOES-19 ABI GeoTIFF files from a time sequence of data. In
the bash shell script example below, I use the ABI MESO Sector 1, Band 1 
files to search for files that are available from October 28, 2025, 
limiting the search to files with an hour prefix of 15, 16, 17, or 18. These files
were produced at 1 minute resolution. I then create true color images 
from all time periods that are available.

.. code-block:: bash

	#!/bin/bash

        # Example script for using Geo2Grid Version 1.3 to create an MP4 animation.

	# Set GEO2GRID environment variables

	export GEO2GRID_HOME=/home/g2g/geo2grid_v_1_3
	export PATH=$PATH:$GEO2GRID_HOME/bin

	# Get input list of available files/times based upon ABI Band 1 files

	ls -1 /data/abi19/20251028/OR_ABI-L1b-RadM1-M6C01_G19_s2025301{15,16,17,18}*.nc > file_list.txt

	sort_list=$(cat file_list.txt | sort)

        # Make images for each time period available
        for file in ${sort_list} ; do

           echo ${file}
           # get date/time for geo2grid file search
           datetime=`basename $file | cut -c27-39`
           echo "datetime :"$datetime

           # Cut out a box with lat/lon bounds of 80W, 16N to 74W 20N 
           geo2grid.sh -r abi_l1b -w geotiff --num-workers 8 --ll-bbox -80 16 -74 20  -p true_color -f /data/abi19/20251028/*${datetime}*.nc

	done

        exit 0

This script creates 239 GeoTIFF images for my time range, 15:00 through 18:59 UTC,
with a time step of every 1 minute.

Upon completion of the script, I add overlays to all of the GeoTIFF images using the ``add_coastlines.sh`` 
utility script.  

.. code-block:: bash

    add_coastlines.sh *.tif --add-coastlines --coastlines-resolution f --coastlines-level 6 --coastlines-outline black  --cache-dir $HOME/

I store the overlays using the ``--cache-dir`` option, which greatly improves the execution time of this command
by reusing the overlay for all images with the same image grid and decorations. The result of executing this
script is the creation of a PNG file that includes overlays for each GeoTIFF.

To create an MP4 animation from the PNG images, I use the Geo2Grid utility script
``gtiff2mp4.sh``.

.. code-block:: bash

    gtiff2mp4.sh GOES19_ABI_Hurricane_Melissa.mp4  *true_color*.png

The script wraps the ``ffmpeg`` video software, and combines all of the
``*true_color*.png`` files found in the directory into an animation
based upon defaults that make the output animations most compatible
with modern video players. The output frame rate is 24 frames per
second. The images will automatically be resized if they are
large in order to ensure a smooth animation. I chose an output
filename of ``GOES19_ABI_Hurricane_Melissa.mp4``. The software can also
create animations from input ``.tif`` files.

The figure below is the first image in the 239 loop sequence.  The
output MP4 animation is available for viewing at `this site <https://bin.ssec.wisc.edu/pub/CSPP/g2g_examples/abi/GOES19_ABI_Hurricane_Melissa.mp4>`_.

.. figure:: ../_static/example_images/GOES-19_ABI_RadM1_true_color_20251028_150027_GOES-East.png
    :width: 100%
    :align: center

    The first GOES-19 ABI image from the 239 frame loop created with data from 28 October 2025 showing the movement of Hurricane Melissa toward Jamaica.  The image observations are from 15:00 UTC.
