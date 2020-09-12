#!/usr/bin/env bash
# encoding: utf-8
# Copyright (C) 2019 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    December 2014
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ] ; do SOURCE="$(readlink "$SOURCE")"; done
export POLAR2GRID_HOME="$( cd -P "$( dirname "$SOURCE" )" && cd .. && pwd )"

# Setup necessary environments
# __SWBUNDLE_ENVIRONMENT_INJECTION__

get_num_bands() {
    gdalinfo $1 2>/dev/null | grep -P 'Band \d' | wc -l
}

has_colortable() {
    gdalinfo $1 2>/dev/null | grep "ColorInterp=Palette" | wc -l
}

to_rgba() {
    num_bands=$(get_num_bands $1)
    has_ct=$(has_colortable $1)

    if [[ ${has_ct} -eq 1 ]]; then
        gdal_translate -expand rgba $1 $2
    elif [[ ${num_bands} -eq 1 ]]; then
        # L
        gdal_translate -b 1 -b 1 -b 1 -b mask,1 -colorinterp red,green,blue,alpha $1 $2
    elif [[ $num_bands -eq 2 ]]; then
        # LA
        gdal_translate -b 1 -b 1 -b 1 -b 2 -colorinterp red,green,blue,alpha $1 $2
#    elif [[ $num_bands -eq 3 ]]; then
#        # RGB
#        gdal_translate -b 1 -b 1 -b 1 -colorinterp red,green,blue $1 $2
    else
        # RGB or RGBA or hope for the best
        ln -s $1 $2
    fi
}

oops() {
    >&2 echo "OOPS: $*"
    >&2 echo "FAILURE"
    exit 1
}

cleanup() {
    >&2 echo "Removing intermediate RGBA images \"$IN1_RGB_FN\""
    >&2 echo "Removing intermediate RGBA images \"$IN2_RGB_FN\""
    rm -f "$IN1_RGB_FN" 2>/dev/null
    rm -f "$IN2_RGB_FN" 2>/dev/null
}
trap cleanup 0 ERR

if [[ $# -ne 3 ]]; then
    echo "Usage: overlay.sh background.tif foreground.tif out.tif"
    exit 1
fi

IN1=$1
IN2=$2
OUT=$3

IN1_RGB_FN=${IN1/.tif/.__rgba__.tif}
IN2_RGB_FN=${IN2/.tif/.__rgba__.tif}
to_rgba ${IN1} ${IN1_RGB_FN} || oops "Could not create RGBA version of ${IN1}"
to_rgba ${IN2} ${IN2_RGB_FN} || oops "Could not create RGBA version of ${IN2}"
gdal_merge.py -o ${OUT} $IN1_RGB_FN $IN2_RGB_FN || oops "Could not create merged image"
>&2 echo "SUCCESS"
