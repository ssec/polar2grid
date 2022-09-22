#!/usr/bin/env bash
# encoding: utf-8
# Usage: gtiff2kmz.sh input.tif [output.kmz]
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

# Call the python module to do the processing, passing all arguments
# Similar, but not as nice of an image:
# ${P2G_SHELLB3_DIR}/bin/gdal_translate -of KMLSUPEROVERLAY -co FORMAT=JPEG $@

if [ $# -eq 1 ]; then
    input_fn=$1
    tile_dir=${input_fn/.tif/}
    output_fn=${input_fn/.tif/.kmz}
elif [ $# -eq 2 ]; then
    input_fn=$1
    output_fn=$2
    tile_dir=${input_fn/.tif/}
else
    echo "Usage: gtiff2kmz.sh input.tif [output.kmz]"
    exit 1
fi

if [ $input_fn = "-h" ] || [ $input_fn = "--help" ] || [ $output_fn = "-h" ] || [ $output_fn = "--help" ]; then
    echo "Usage: gtiff2kmz.sh input.tif [output.kmz]"
    exit 1
fi

# Create a tiled KML directory
echo "Creating temporary tiled KML directory..."
gdal2tiles.py -p geodetic $input_fn $tile_dir || { echo "ERROR: Could not create tiled KML"; exit 1; }

# Zip the KML directory in to a KMZ file
echo "Zipping KML directory in to a KMZ..."
cd $tile_dir
zip -r ../$output_fn * || { echo "ERROR: Could not create zipped KMZ"; exit 1; }
cd ..

echo "Removing temporary tiled KML directory"
rm -r $tile_dir

echo "Done"
