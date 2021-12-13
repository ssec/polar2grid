#!/usr/bin/env bash
### Run simple png creator to verify glue script products ###
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

# Setup viirs2awips environment
if [ -z "$POLAR2GRID_HOME" ]; then
    oops "POLAR2GRID_HOME needs to be defined"
fi
# Setup necessary environments
# __SWBUNDLE_ENVIRONMENT_INJECTION__

# Generate NC product images
${P2G_SHELLB3_DIR}/bin/python -m polar2grid.plot_ncdata $@ || oops "Could not generate png images from NC files."

# End of all tests
echo "SUCCESS"
