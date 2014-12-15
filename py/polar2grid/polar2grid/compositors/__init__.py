#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
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
"""Compositors allow for optional filtering of gridded products.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Dec 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import os
import sys
import logging

import pkg_resources

LOG = logging.getLogger(__name__)

P2G_COMP_CLS_EP = "polar2grid.compositor_class"
P2G_COMP_ARGS_EP = "polar2grid.compositor_arguments"


def available_compositors(entry_point=P2G_COMP_CLS_EP):
    """Don't load this unless it needs to be used (via main or via glue.py).
    """
    return {frontend_ep.name: frontend_ep.dist for frontend_ep in pkg_resources.iter_entry_points(entry_point)}


def get_compositor_argument_func(compositors, name):
    """Get the function to add the specified compositor's arguments.

    :param compositors: dictionary returned by `available_compositors`
    :param name: name of the compositor as defined in the entry point
    """
    return pkg_resources.load_entry_point(compositors[name], P2G_COMP_ARGS_EP, name)


def get_compositor_class(compositors, name):
    """Get the named compositor's class object.

    :param compositors: dictionary returned by `available_compositors`
    :param name: name of the compositor as defined in the entry point
    """
    return pkg_resources.load_entry_point(compositors[name], P2G_COMP_CLS_EP, name)


def main(argv=sys.argv):
    from polar2grid.core.script_utils import setup_logging, create_basic_parser, create_exc_handler
    from polar2grid.core.meta import GriddedScene
    compositors = available_compositors()
    parser = create_basic_parser(description="Extract swath data, remap it, and write it to a new file format")
    parser.add_argument("compositors", choices=sorted(compositors.keys()), nargs="*",
                        help="Specify the compositors to apply to the provided scene (additional arguments are determined after this is specified)")
    # don't include the help flag
    argv_without_help = [x for x in argv if x not in ["-h", "--help"]]
    args, remaining_args = parser.parse_known_args(argv_without_help)

    # load the actual components we need
    subgroup_titles = []
    compositor_classes = {}
    for c in args.compositors:
        carg_func = get_compositor_argument_func(compositors, c)
        ccls = get_compositor_class(compositors, c)
        compositor_classes[c] = ccls

        # add_frontend_arguments(parser)
        subgroup_titles += carg_func(parser)

    parser.add_argument("--scene", required=True, help="JSON SwathScene filename to be remapped")
    parser.add_argument("-o", dest="output_filename",
                        help="Specify the filename for the newly modified scene (default: original_fn + 'composite')")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(argv, subgroup_titles=subgroup_titles, global_keywords=global_keywords)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)
    LOG.debug("Starting compositor script with arguments: %s", " ".join(sys.argv))

    compositor_objects = {}
    for c, ccls in compositor_classes.items():
        compositor_objects[c] = ccls(**args.subgroup_args[c + " Initialization"])

    scene = GriddedScene.load(args.scene)
    for c, comp in compositor_objects.items():
        try:
            scene = comp.modify_scene(scene, **args.subgroup_args[c + " Modification"])
        except StandardError:
            LOG.debug("Compositor Error: ", exc_info=True)
            LOG.error("Could not properly modify scene using compositor '%s'" % (c,))
            if args.exit_on_error:
                raise RuntimeError("Could not properly modify scene using compositor '%s'" % (c,))

    if args.output_filename is None:
        stem, ext = os.path.splitext(args.scene)
        args.output_filename = stem + "_composite" + ext
    scene.save(args.output_filename)

if __name__ == "__main__":
    sys.exit(main())