Polar2Grid software bundle
==========================

Copyright (C) 2012-2022 Space Science and Engineering Center (SSEC), University of Wisconsin-Madison.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

This file is part of the polar2grid software package. Polar2grid takes
satellite observation data, remaps it, and writes it to a file format for
input into another program.
Documentation: http://www.ssec.wisc.edu/software/polar2grid/

    Written by David Hoese    February 2019
    University of Wisconsin-Madison
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

Original scripts and automation included as part of this package are
distributed under the GNU GENERAL PUBLIC LICENSE agreement version 3.
Binary executable files included as part of this software package are
copyrighted and licensed by their respective organizations, and
distributed consistent with their licensing terms.

Installation
============

1. Untar the tarball:
    # if you're reading this, this step is probably complete already
    tar -xzf polar2grid-swbundle-<version>.tar.gz
2. Add the following line to your .bash_profile or .bashrc:
    export POLAR2GRID_HOME=/path/to/untarred-swbundle-dir

To run a polar2grid script
==========================

The polar2grid script can be run directly from the bin directory:

    $POLAR2GRID_HOME/bin/polar2grid.sh ...

or

    $POLAR2GRID_HOME/bin/polar2grid.sh --help

for more help.

Polar2Grid Documentation: http://www.ssec.wisc.edu/software/polar2grid/
CSPP LEO Home Page: http://cimss.ssec.wisc.edu/cspp/
