#!/usr/bin/env bash
### Run simple python script to print out a valid polar2grid grid
### configuration line.
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
#     Written by David Hoese    April 2013
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu

if [ -z "$POLAR2GRID_HOME" ]; then
  export POLAR2GRID_HOME="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
fi

# Setup necessary environments
# __SWBUNDLE_ENVIRONMENT_INJECTION__

# Call the script
export PROG_NAME="p2g_grid_helper.sh"
python3 -m polar2grid.grids.config_helper "$@"
