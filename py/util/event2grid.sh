#!/usr/bin/env bash
#Script to chain together the process of retrieving data from PEATE (via dibs), processing that data (via CREFL and polar2grid), and pushing that data to FTP.
#Usage: event2grid.sh event_name_id /base/data/directory/ /base/work/directory <dibs and polar2grid command line options>

EVENT_ID=$1
BASE_DATA_DIR=$2
BASE_WORK_DIR=$3
DIBS_FLAGS=$4
P2G_FLAGS=$5

EXIT_NO_DATA=1
EXIT_SUCCESS=0

export PYTHONPATH=/data1/users/davidh/event2grid_env/python:$PYTHONPATH
DIBS_VIIRS=/data1/users/davidh/event2grid_env/polar2grid/py/util/dibs_viirs.py
CREFL_RUN=/data1/users/davidh/event2grid_env/viirs_crefl/run_viirs_crefl.bash
CREFL2GTIFF=/data1/users/davidh/event2grid_env/bin/crefl2gtiff.sh
FTP_BASE_PATH=/pub/ssec/davidh/event2grid

# This event's download directory
EVENT_DL_DIR=$BASE_DATA_DIR/$EVENT_ID
mkdir -p $EVENT_DL_DIR
EVENT_WORK_DIR=$BASE_WORK_DIR/$EVENT_ID
mkdir -p $EVENT_WORK_DIR

# Turn on debugging
set -x

# Have dibs get what we need
echo "Calling dibs to download any data..."
cd $EVENT_DL_DIR
python $DIBS_VIIRS $EVENT_ID -vvv $DIBS_FLAGS
echo "Calling dibs to sort data into passes..."
python $DIBS_VIIRS $EVENT_ID -vvv --pass

# Get a list of passes we should process
for pass_dir in `ls -d $EVENT_DL_DIR/*.pass`; do
    # Get the name of the pass (without the state information)
    pass_dirname=$(basename $pass_dir)
    pass_dirname=${pass_dirname%.pass}
    ftp_data_path=$FTP_BASE_PATH/$EVENT_ID
    echo "Processing pass $pass_dir"

    # Move the pass directory to processing so we know we are done with it
    data_dir=${pass_dir%.pass}.processing
    mv $pass_dir $data_dir

    # FIXME: Make sure all of the necessary files made it or at least log what is missing

    # Create the working directory that CREFL files and Polar2Grid files will be created in
    work_dir=$EVENT_WORK_DIR/$pass_dirname
    mkdir -p $work_dir
    cd $work_dir
    
    # Process the CREFL files
    # FIXME: This will need to be determined by whether or not CREFL is desired (maybe rewrite it in python to polar2grid wink,wink)
    echo "Creating CREFL output..."
    for m05_file in `ls $data_dir/SVM05*.h5`; do
        #Is this a Day Granule?
        attr="/Data_Products/VIIRS-M5-SDR/VIIRS-M5-SDR_Gran_0/N_Day_Night_Flag"
        light=`h5dump -a ${attr} ${m05_file} | grep ":" | gawk -F\" '{ print $2 }'`
        echo "Granule Regime is :"  $light

        if [[ "${light}" == "Day" ]]; then
            $CREFL_RUN $m05_file
        else
            echo "No day data in $m05_file, won't create CREFL output"
            exit 1
        fi
    done
    echo "Linking navigation files to work directory..."
    # This has to be done so polar2grid has access to both data and geolocation files
    for gl_file in `ls $data_dir/G*TCO*.h5`; do
        ln -s $gl_file .
    done

    # Remap using polar2grid (working dir has the crefl files)
    $CREFL2GTIFF -vvv $P2G_FLAGS -d $work_dir

    # FIXME: This only sends true colors
    for gtiff_file in `ls $work_dir/*true_color*.tif`; do
        # FTP to a location
        echo "Pushing $gtiff_file to FTP server ($ftp_data_path)"
        ncftpput -m -u ftp -p david.hoese@ssec.wisc.edu ftp.ssec.wisc.edu $ftp_data_path $gtiff_file
    done
done

echo "Done with $EVENT_ID"
