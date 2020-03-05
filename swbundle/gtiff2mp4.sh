#!/usr/bin/env bash
# encoding: utf-8
# Usage: gtiff2mp4.sh output.mp4 input1.tif input2.tif ...
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
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
#     Written by David Hoese    November 2018
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu

if [ -z "$POLAR2GRID_HOME" ]; then
  export POLAR2GRID_HOME="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
fi

# Setup necessary environments
source $POLAR2GRID_HOME/bin/env.sh
set -e

if [ $# -lt 2 ]; then
    >&2 echo "Usage: gtiff2mp4.sh output.mp4 input1.tif input2.tif"
    exit 1
fi

TMP_FRAME_DIR="gtiff2mp4_tmp"
OUTPUT_FILENAME="$1"
shift
INPUT_FILES=( "$@" )
MAX_IMG_SIZE=${MAX_IMG_SIZE:-4096}

gdal_size() {
    if [[ -z "$1" ]]; then
        echo "Missing arguments. Syntax:"
        echo "  gdal_pixelsize_gdalwarp_tr <input_raster>"
        return
    fi;
    EXTENT=$(gdalinfo "$1" |\
        grep "Size is" |\
        sed "s/Size is //g; s/,/ /g" |\
        tr "\n" " " |\
        tr -d "[(,])-");
    echo -n "$EXTENT"
}

get_new_image_width() {
    img_width=$1
    img_height=$2
    if [[ $img_width -ge $img_height ]]; then
        if [[ $img_width -ge $MAX_IMG_SIZE ]]; then
            echo $MAX_IMG_SIZE
        else
            echo $img_width
        fi
    else
        if [[ $img_height -gt $MAX_IMG_SIZE ]]; then
            # use ratio to get width
            echo $(( $MAX_IMG_SIZE * $img_width / $img_height ))
        else
            echo $img_width
        fi
    fi
}

cleanup() {
    >&2 echo "Removing temporary directory \"$TMP_FRAME_DIR\""
    rm -rf "$TMP_FRAME_DIR"
}
trap cleanup 0 ERR

echo "Creating temporary directory for sorting frames..."
mkdir -p "$TMP_FRAME_DIR"

echo "Creating video file from: "
printf '%s\n' ${INPUT_FILES[@]}
echo "Total number of input files: ${#INPUT_FILES[@]}"

FILE_EXT=${INPUT_FILES[0]##.}

x=1
echo "Preparing images for video conversion..."
for i in "${INPUT_FILES[@]}"; do
    counter=$(printf %03d $x)
    img_width_height=`gdal_size $i`
    img_width=`echo $img_width_height | cut -f1 -d' '`
    img_height=`echo $img_height | cut -f3 -d' '`
    new_width=`get_new_image_width $img_width $img_height`
    if [[ $new_width -eq $img_width ]]; then
        ln -s "../$i" "${TMP_FRAME_DIR}/${counter}.${FILE_EXT}"
    else
        echo "Scaling image to work with ffmpeg (New width=${new_width})"
        gdal_translate -outsize $new_width 0 $i "${TMP_FRAME_DIR}/${counter}.${FILE_EXT}"
    fi
    x=$(($x+1))
done

echo "Generating animation..."
INPUT_PARAMS=${INPUT_PARAMS:--framerate 24 -f image2}
OUTPUT_PARAMS=${OUTPUT_PARAMS:--c:v libx264 -crf 25 -vf "format=yuv420p,scale=trunc(iw/2)*2:trunc(ih/2)*2"}
ffmpeg -y $INPUT_PARAMS -i "${TMP_FRAME_DIR}/%03d.${FILE_EXT}" $OUTPUT_PARAMS $OUTPUT_FILENAME


echo "Done"
