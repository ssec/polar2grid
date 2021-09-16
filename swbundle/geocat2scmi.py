#!/usr/bin/env python3
# encoding: utf-8
"""Convert GEOCAT Level 1 and 2 products to AWIPS SCMI format.

Run with the following command from the Polar2Grid Software Bundle:

    source /path/to/polar2grid/bin/env.sh
    python geocat2scmi.py ...

Use `-h` flag for help and usage information.

FUTURE: This script will be included in the functionality of the CSPP Geo2Grid package

"""

import os
import sys
import logging


def add_scene_argument_groups(parser):
    group_1 = parser.add_argument_group(title="Scene Initialization")
    group_1.add_argument("reader", help="Name of reader used to read provided files")
    group_1.add_argument("-f", "--filenames", nargs="+", help="Input files to read")
    group_2 = parser.add_argument_group(title="Scene Load")
    group_2.add_argument("-d", "--datasets", nargs="+", help="Names of datasets to load from input files")
    return group_1, group_2


def main():
    from satpy import Scene
    from satpy.writers.scmi import add_backend_argument_groups as add_writer_argument_groups
    import argparse

    parser = argparse.ArgumentParser(description="Convert GEOCAT Level 1 and 2 to AWIPS SCMI files")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="count",
        default=0,
        help="each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)",
    )
    parser.add_argument("-l", "--log", dest="log_fn", default=None, help="specify the log filename")
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
    scn.load(load_args["datasets"])
    writer_args = {}
    writer_args.update(writer_init_args)
    writer_args.update(writer_call_args)
    scn.save_datasets(writer="scmi", **writer_args)


if __name__ == "__main__":
    sys.exit(main())
