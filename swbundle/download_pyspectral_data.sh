#!/usr/bin/env bash
# encoding: utf-8
# Copyright (C) 2018 Space Science and Engineering Center (SSEC),
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

export POLAR2GRID_HOME="$( cd -P "$( dirname "$(readlink -f "${BASH_SOURCE[0]}")" )" && cd .. && pwd )"

# Setup necessary environments
# __SWBUNDLE_ENVIRONMENT_INJECTION__

set -e

ORIG_PSP_DATA_ROOT=${PSP_DATA_ROOT}
if [ -n "${PSP_DATA_CACHE_ROOT}" ]; then
  echo "Using pyspectral data cache root: ${PSP_DATA_CACHE_ROOT}"
  export PSP_DATA_ROOT=${PSP_DATA_CACHE_ROOT}
fi

# Call the python module to do the processing, passing all arguments
python3 -c "from pyspectral.rayleigh import check_and_download; import logging; logging.basicConfig(level=logging.DEBUG); check_and_download()"
python3 -c "from pyspectral.rsr_reader import check_and_download; import logging; logging.basicConfig(level=logging.DEBUG); check_and_download()"

if [ -n "${PSP_DATA_CACHE_ROOT}" ]; then
  mkdir -p "${ORIG_PSP_DATA_ROOT}"
  cp -r ${PSP_DATA_CACHE_ROOT}/* "${ORIG_PSP_DATA_ROOT}/"
  export PSP_DATA_ROOT=${ORIG_PSP_DATA_ROOT}
fi
