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
THIS_SCRIPT_HOME="$( cd -P "$( dirname "$(readlink -f "${BASH_SOURCE[0]}")" )" && cd .. && pwd )"
P2G_CONDA_BASE="${THIS_SCRIPT_HOME}/libexec/python_runtime"
P2G_METADATA="${P2G_CONDA_BASE}/lib/python*/site-packages/polar2grid-*.dist-info/METADATA"
METADATA_CHECKSUM=$(${P2G_CONDA_BASE}/bin/openssl sha256 $P2G_METADATA)


oops() {
    echo "ERROR: $*"
    exit 1
}

# conda-unpack replaces the prefix stored in its _prefix_records with the
# environment's current location. Once it has run, the files contain the current
# location instead, so store that in conda-unpack too. Otherwise an initialized
# bundle that is copied or re-archived (ex. after validating a release) is never
# relocated again: conda-unpack would look for a prefix that no file contains.
_record_conda_unpack_prefix() {
    "${P2G_CONDA_BASE}/bin/python" -I - "${P2G_CONDA_BASE}/bin/conda-unpack" "${P2G_CONDA_BASE}" <<'PYTHON'
import ast
import os
import shutil
import sys
import tempfile

script, new_prefix = sys.argv[1:]
with open(script, encoding="utf-8") as script_file:
    old_source = new_source = script_file.read()
# Read the records without running conda-unpack, which imports modules from its own
# directory. The text replacement below already relies on the list being a literal.
records_node = next(
    (
        node.value
        for node in ast.parse(old_source).body
        if isinstance(node, ast.Assign)
        and [getattr(target, "id", None) for target in node.targets] == ["_prefix_records"]
    ),
    None,
)
if records_node is None:
    sys.exit("Unexpected conda-unpack format; could not find _prefix_records")
records = ast.literal_eval(records_node)
for old_prefix in {placeholder for _, placeholder, _ in records} - {new_prefix}:
    # Each record is the repr of a (path, placeholder, mode) tuple
    old_entry = ", %r, " % (old_prefix,)
    num_records = sum(placeholder == old_prefix for _, placeholder, _ in records)
    if new_source.count(old_entry) != num_records:
        sys.exit("Unexpected conda-unpack format; could not replace prefix %r" % (old_prefix,))
    new_source = new_source.replace(old_entry, ", %r, " % (new_prefix,))
if new_source != old_source:
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(script))
    with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
        tmp_file.write(new_source)
    shutil.copymode(script, tmp_path)
    os.replace(tmp_path, script)
PYTHON
}


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
    # Check if we already ran conda-unpack in this location. The marker only
    # decides whether to run; conda-unpack itself records which prefix to replace.
    install_signal="${P2G_CONDA_BASE}/.installed"
    if [[ "$(head -n 1 "${install_signal}" 2>/dev/null)" != "${P2G_CONDA_BASE}" ]]; then
        echo "Running one-time initialization of environment..."
        # Run by full path so the prefix conda-unpack writes (derived from its own
        # location) is exactly the P2G_CONDA_BASE recorded below.
        "${P2G_CONDA_BASE}/bin/conda-unpack" || oops "Unable to perform one-time initialization. If this installation "\
        "(tarball extraction) was done by another user, that user should run 'geo2grid.sh -h' first."
        _record_conda_unpack_prefix || oops "Unable to record the environment location for future relocation."
        echo "${P2G_CONDA_BASE}" > "${install_signal}"
    fi

    # Add bundle scripts so they have priority over Python package-installed scripts
    export PATH="${POLAR2GRID_HOME}/bin:${PATH}"

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
