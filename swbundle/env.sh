#!/usr/bin/env bash
### SWBUNDLE ENVIRONMENT SETUP ###
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

# where are we?
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ] ; do SOURCE="$(readlink "$SOURCE")"; done
THIS_SCRIPT_HOME="$( cd -P "$( dirname "$SOURCE" )" && cd .. && pwd )"
P2G_CONDA_BASE="${THIS_SCRIPT_HOME}/libexec/python_runtime"
P2G_METADATA="${P2G_CONDA_BASE}/lib/python*/site-packages/polar2grid-*.dist-info/METADATA"
METADATA_CHECKSUM=$(openssl sha256 $P2G_METADATA)

# Only load the environment if it hasn't been done already
if [[ "${_POLAR2GRID_ENV_LOADED}" != "${METADATA_CHECKSUM}" ]]; then
    export POLAR2GRID_HOME="${THIS_SCRIPT_HOME}"

    # Don't let someone else's PYTHONPATH mess us up
    unset PYTHONPATH
    export PYTHONNOUSERSITE=1
    unset LD_PRELOAD
    unset DYLD_LIBRARY_PATH
    unset LD_LIBRARY_PATH

    source $P2G_CONDA_BASE/bin/activate
    # Check if we already ran conda-unpack
    install_signal="${P2G_CONDA_BASE}/.installed"
    if [[ "$(head -n 1 ${install_signal} 2>/dev/null)" != "${P2G_CONDA_BASE}" ]]; then
        echo "Running one-time initialization of environment..."
        conda-unpack
        echo "${P2G_CONDA_BASE}" > "${install_signal}"
    fi

    # Point gdal utilities to the proper data location
    export GDAL_DATA=$P2G_CONDA_BASE/share/gdal
    export SATPY_CONFIG_PATH=$POLAR2GRID_HOME/etc/polar2grid
    export SATPY_DATA_DIR=$POLAR2GRID_HOME/share/polar2grid/data
    export CREFL_ANCPATH=$POLAR2GRID_HOME/share/polar2grid/data
    export SATPY_DOWNLOAD_AUX=False
    export PSP_CONFIG_FILE=$POLAR2GRID_HOME/etc/polar2grid/pyspectral.yaml
    export PSP_DATA_ROOT=$POLAR2GRID_HOME/pyspectral_data
    export GSHHS_DATA_ROOT=$POLAR2GRID_HOME/gshhg_data

    export _POLAR2GRID_ENV_LOADED="${METADATA_CHECKSUM}"
fi

