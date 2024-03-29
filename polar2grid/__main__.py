#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2021 Space Science and Engineering Center (SSEC),
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
#     Written by David Hoese    January 2021
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""Simple wrapper around the Polar2Grid and Geo2Grid glue scripts."""

import os
import sys


def p2g_main(argv=sys.argv[1:]):
    from polar2grid.glue import main

    os.environ["USE_POLAR2GRID_DEFAULTS"] = "1"
    return main(argv=argv)


def g2g_main(argv=sys.argv[1:]):
    from polar2grid.glue import main

    os.environ["USE_POLAR2GRID_DEFAULTS"] = "0"
    return main(argv=argv)


if __name__ == "__main__":
    from polar2grid.glue import main

    sys.exit(main())
