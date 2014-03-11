#!/usr/bin/env bash
# Search for jobs in the event script directory that need to be run

EVENT_SCRIPT_DIR=/home/davidh/event2grid_jobs
BASE_DOWNLOAD_DIR=/data1/tmp/event2grid_download
BASE_WORK_DIR=/data1/tmp/event2grid_work
CRON_RATE=3600
# We wait 12 hours extra for the PEATE to catch up with the newest data before a job is 'expired'
PEATE_DELAY=$((12 * 60 * 60))

function file_dt_to_epoch() {
    str=$1
    echo `date -d "${str:0:4}-${str:4:2}-${str:6:2} ${str:9:2}:${str:11:2}:${str:13:2}" +%s`
}

function get_start_time() {
    fn=$1
    echo `file_dt_to_epoch ${fn:0:15}`
}

function get_end_time() {
    fn=$1
    echo `file_dt_to_epoch ${fn:16:15}`
}

function get_creation_time() {
    fn=$1
    echo `file_dt_to_epoch ${fn:32:15}`
}

now=`date -u +%s`
echo "Starting event2grid job search `date -u`"
for script_fp in `ls $EVENT_SCRIPT_DIR/????????_??????_????????_??????_????????_??????_*.sh`; do
    script_fn=`basename $script_fp`
    start_time=`get_start_time $script_fn`
    end_time=`get_end_time $script_fn`
    creation_time=`get_creation_time $script_fn`
    event_id=`expr "$script_fn" : '\([^\.]*\)'`
    event_log=$BASE_WORK_DIR/$event_id.log

    echo "Found $event_id; Start=$start_time; End=$end_time; Creation=$creation_time"
    echo "Read log file for more info: $event_log"
    set -x

    # Is this event 'old'?
    if [ $(($now - $CRON_RATE)) -gt $(($end_time + $PEATE_DELAY)) ]; then
        # Has this event ever been processed, if not let's run it
        if [ ! -d $BASE_WORK_DIR/$event_id ]; then
            echo "Processing one time event $event_id..."
            bash $script_fp &>>$event_log &
        else
            # We have processed this old event, it's time to remove it
            echo "Removing old and already process event $script_fp"
            rm $script_fp
        fi
    elif [ $now -lt $start_time ]; then
        # This event is in the future
        echo "Skipping $event_id until its start time has occurred"
    else
        # This event is currently happening
        echo "Processing event $event_id..."
        bash $script_fp &>>$event_log &
    fi

    set +x
done

