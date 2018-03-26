#!/usr/bin/env python
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
"""Connect various satpy components together to go from satellite data to output imagery format.
"""

import os
import sys
import logging


def add_scene_argument_groups(parser):
    group_1 = parser.add_argument_group(title='Scene Initialization')
    group_1.add_argument('reader',
                         help='Name of reader used to read provided files')
    group_1.add_argument('-f', '--filenames', nargs='+',
                         help='Input files to read')
    group_2 = parser.add_argument_group(title='Scene Load')
    group_2.add_argument('-d', '--datasets', nargs='+',
                         help='Names of datasets to load from input files')
    return group_1, group_2


def main():
    from satpy import Scene
    from satpy.writers.scmi import add_backend_argument_groups as add_writer_argument_groups
    import argparse
    parser = argparse.ArgumentParser(description="Convert GEOCAT Level 1 and 2 to AWIPS SCMI files")
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
                        help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument('-l', '--log', dest="log_fn", default=None,
                        help="specify the log filename")
    subgroups = add_scene_argument_groups(parser)
    subgroups += add_writer_argument_groups(parser)
    args = parser.parse_args()

    scene_args = {ga.dest: getattr(args, ga.dest) for ga in subgroups[0]._group_actions}
    load_args = {ga.dest: getattr(args, ga.dest) for ga in subgroups[1]._group_actions}
    writer_init_args = {ga.dest: getattr(args, ga.dest) for ga in subgroups[2]._group_actions}
    writer_call_args = {ga.dest: getattr(args, ga.dest) for ga in subgroups[3]._group_actions}

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(3, args.verbosity)], filename=args.log_fn)

    scn = Scene(**scene_args)
    scn.load(load_args['datasets'])
    writer_args = {}
    writer_args.update(writer_init_args)
    writer_args.update(writer_call_args)
    scn.save_datasets(writer='scmi', **writer_args)


if __name__ == "__main__":
    sys.exit(main())
