#!/usr/bin/env bash
### CREFL2GTIFF WRAPPER ###
#
# Copyright (C) 2013 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    January 2013
#     University of Wisconsin-Madison 
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu

oops() {
    echo "OOPS: $*"
    echo "FAILURE"
    exit 1
}

softlink_navigation_file() {
    svm05_file=$1
    for pat in GMTCO GITCO GMODO GIMGO; do
        geo_pat="${svm05_file/SVM05/$pat}"
        geo_pat="${geo_pat/_c*_*_*.h5/}"
        echo "Searching for geolocation with pattern: $geo_pat"
        for geo_file in "$geo_pat"*.h5; do
            if [ -f "$geo_file" ]; then
                echo "Linking $geo_file to current directory for polar2grid processing"
                ln -s $geo_file "$(basename "$geo_file")" || oops "Could not link geolocation file $geo_file"
            fi
        done
    done
}

if [ -z "$POLAR2GRID_HOME" ]; then 
  export POLAR2GRID_HOME="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
fi

# Setup necessary environments
source $POLAR2GRID_HOME/bin/polar2grid_env.sh

# If given VIIRS SDR files, run VIIRS CREFL first
PROCESS_FILE=0
PROCESS_DIR=0
PROCESS_DONE=0
PROCESSED_ANY=0
echo "Searching parameters for VIIRS SDR files for CREFL processing (if needed)"
for param in $@; do
    if [ $PROCESS_DONE -eq 1 ]; then
        # We have seen all of the files or directories that we need to preprocess so just read the rest of the parameters
        PASSED_PARAMS=(${PASSED_PARAMS[@]} $param)
    elif [ $PROCESS_FILE -eq 1 ]; then
        # Process a SVM05 file through VIIRS CREFL C binary
        if [ ${param:0:1} == "-" ]; then
            echo "Done processing files with CREFL"
            # We are seeing the next flag we are done
            PASSED_PARAMS=(${PASSED_PARAMS[@]} $param)
            PROCESS_DONE=1
            continue
        fi
        # can't do this in one line in bash
        param_fn="$(basename "$param")"
        if [ ${param_fn:0:5} == "SVM05" ]; then
            echo "Running CREFL on file $param"
            # we only care about SVM05 files
            $POLAR2GRID_HOME/bin/run_viirs_crefl.sh $param || oops "Could not create CREFL output for file $param"
            softlink_navigation_file $param
            PROCESSED_ANY=1
            continue
        fi
        # Else ignore any non-SVM05 files
    elif [ $PROCESS_DIR -eq 1 ]; then
        # Process all of the SVM05 files in the directory specified by the user
        if [ ! -d $param ]; then
            # The directory doesn't exists
            oops "Directory $param does not exist, can't create CREFL output"
        fi
        # Directory exists, let's process each SVM05 file
        echo "Searching directory $param for files to process..."
        for fn in "$param/SVM05"*; do
            # if we just got the pattern back that means we didn't find any SVM05 files
            if [ -f $fn ]; then
                echo "Running CREFL on $fn"
                $POLAR2GRID_HOME/bin/run_viirs_crefl.sh $fn || oops "Could not create CREFL output for file $fn"
                softlink_navigation_file $fn
                PROCESSED_ANY=1
            fi
        done
        PROCESS_DONE=1
    elif [ $param == "-f" ]; then
        echo "Found -f flag"
        PROCESS_FILE=1
    elif [ $param == "-d" ]; then
        echo "Found -d flag"
        PROCESS_DIR=1
    else
        PASSED_PARAMS=(${PASSED_PARAMS[@]} $param)
    fi
done

if [ $PROCESSED_ANY -eq 1 ]; then
    # Call the python module to do the processing, passing remaining arguments, but point it to the new crefl files
    $POLAR2GRID_HOME/ShellB3/bin/python -m polar2grid.crefl2gtiff -vv ${PASSED_PARAMS[@]} -f ./CREFL*
else
    # Call the python module to do the processing, passing all arguments
    $POLAR2GRID_HOME/ShellB3/bin/python -m polar2grid.crefl2gtiff -vv $@
fi
