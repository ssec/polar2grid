#!/usr/bin/env bash

EVENT_SCRIPT_DIR=/home/davidh/event2grid_jobs
BASE_DOWNLOAD_DIR=/data1/tmp/event2grid_download
BASE_WORK_DIR=/data1/tmp/event2grid_work

# Run event2grid.py
now=`date +%Y%m%d_%H%M`
python create_event.py $@

if [ $? -eq 0 ]; then
    # If the user did --help or -h then the python script still exited normally, we need to check if the file exists
    # FIXME: Have a better way to get the script name
    script_fp=`ls /home/davidh/event2grid_jobs/????????_??????_????????_??????_$now??_$USER.sh 2>/dev/null`
    echo "Checking for job script $script_fp"
    if [ -f $script_fp ]; then
        echo "New script successfully created, running for the first time..."
        script_fn=`basename $script_fp`
        event_id=`expr "$script_fn" : '\([^\.]*\)'`
        event_log=$BASE_WORK_DIR/$event_id.log
        bash $script_fp &>>$event_log &
    else
        echo "Event job script not created"
    fi
fi


