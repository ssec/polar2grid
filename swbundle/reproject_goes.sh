#!/usr/bin/env bash
# encoding: utf-8
# Usage: reproject_goes.sh input1.tif input2.tif ...
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

if [[ $# -lt 1 ]]; then
    >&2 echo "Usage: reproject_goes.sh input1.tif input2.tif"
    exit 1
fi

INPUT_FILES="$@"
for fn in $INPUT_FILES; do
    new_fn=${fn/.tif/-y.tif}
    current_proj=`gdalinfo -proj4 $fn | grep -A 1 "PROJ.4 string is:" | tail -n 1`
    new_proj=${current_proj/+sweep=x/+sweep=y}
    echo "Reprojecting $fn to $new_proj..."
    gdalwarp -t_srs "$new_proj" -multi -wo "NUM_THREADS=4" -co "COMPRESS=DEFLATE" $fn $new_fn
done