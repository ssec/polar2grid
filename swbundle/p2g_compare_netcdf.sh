#!/usr/bin/env bash
### Verify simple test products with known products ###
# Should be renamed verify.sh in the corresponding test tarball
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

# Checks arguments
if [ $# -lt 2 ] || [[ $* =~ (^|[[:space:]])("-h"|"--help")($|[[:space:]]) ]]; then
    echo "Usage: p2g_compare_geotiff.sh verification_dir work_dir"
    print=0
    options=`python -m polar2grid.compare geotiff -h`
    while IFS= read line
    do
        if [[ "$line" =~ "optional" ]]; then
            print=1
        fi
        if [[ $print -eq 1 ]]; then
            echo "$line"
        fi
    done <<< "$options"
    if [[ $* =~ (^|[[:space:]])("-h"|"--help")($|[[:space:]]) ]]; then
        exit 0
    fi
    exit 1
fi

# Get primary and secondary directory names
VERIFY_BASE=$1
WORK_DIR=$2

oops() {
    echo "ERROR: $*"
    echo "FAILURE"
    exit 1
}

if [ ! -d $VERIFY_BASE ]; then
    oops "Verification directory $VERIFY_BASE does not exist"
fi

if [ ! -d $WORK_DIR ]; then
    oops "Working directory $WORK_DIR does not exist"
fi

# Run tests for each test data directory in the base directory
BAD_COUNT=0
for VFILE in $VERIFY_BASE/SSEC*; do
    WFILE=$WORK_DIR/`basename $VFILE`
    echo "INFO: Comparing $WFILE to known valid file"
    python -m polar2grid.compare netcdf "$VFILE" "$WFILE" `echo "${@:3}"`
    [ $? -eq 0 ] || BAD_COUNT=$(($BAD_COUNT + 1))
done

if [ $BAD_COUNT -ne 0 ]; then
    oops "$BAD_COUNT files were found to be unequal"
fi

# End of all tests
echo "All files passed"
echo "SUCCESS"

