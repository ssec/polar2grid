#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
#     input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    October 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Connect various polar2grid components together to go from satellite data to output imagery format.

:author:       David Hoese (davidh)
:author:       Ray Garcia (rayg)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import pkg_resources
from polar2grid.remap import Remapper, add_remap_argument_groups

import sys
import logging

### Return Status Values ###
STATUS_SUCCESS = 0
# Python looks like it always returns 1 if an exception was found so that's our unknown failure value
# not sure why we failed, not an expected failure
STATUS_UNKNOWN_FAIL = 1
# the frontend failed
STATUS_FRONTEND_FAIL = 2
# the backend failed
STATUS_BACKEND_FAIL = 4
# something with remapping failed
STATUS_REMAP_FAIL = 8
# grid determination or grid jobs creation failed
STATUS_GDETER_FAIL = 16
# composition failed
STATUS_COMP_FAIL = 32

P2G_FRONTEND_CLS_EP = "polar2grid.frontend_class"
P2G_FRONTEND_ARGS_EP = "polar2grid.frontend_arguments"
P2G_BACKEND_CLS_EP = "polar2grid.backend_class"
P2G_BACKEND_ARGS_EP = "polar2grid.backend_arguments"

FRONTENDS = {frontend_ep.name: frontend_ep.dist for frontend_ep in pkg_resources.iter_entry_points(P2G_FRONTEND_CLS_EP)}
BACKENDS = {backend_ep.name: backend_ep.dist for backend_ep in pkg_resources.iter_entry_points(P2G_BACKEND_CLS_EP)}


def get_frontend_argument_func(name):
    return pkg_resources.load_entry_point(FRONTENDS[name], P2G_FRONTEND_ARGS_EP, name)


def get_frontend_class(name):
    return pkg_resources.load_entry_point(FRONTENDS[name], P2G_FRONTEND_CLS_EP, name)


def get_backend_argument_func(name):
    return pkg_resources.load_entry_point(BACKENDS[name], P2G_BACKEND_ARGS_EP, name)


def get_backend_class(name):
    return pkg_resources.load_entry_point(BACKENDS[name], P2G_BACKEND_CLS_EP, name)


def main(argv=sys.argv[1:]):
    # from argparse import ArgumentParser
    # init_parser = ArgumentParser(description="Extract swath data, remap it, and write it to a new file format")
    from polar2grid.core.script_utils import setup_logging, create_basic_parser, create_exc_handler, rename_log_file, ExtendAction
    from polar2grid.compositors import available_compositors, get_compositor_class, get_compositor_argument_func
    compositors = available_compositors()
    parser = create_basic_parser(description="Extract swath data, remap it, and write it to a new file format")
    parser.add_argument("frontend", choices=sorted(FRONTENDS.keys()),
                        help="Specify the swath extractor to use to read data (additional arguments are determined after this is specified)")
    parser.add_argument("backend", choices=sorted(BACKENDS.keys()),
                        help="Specify the backend to use to write data output (additional arguments are determined after this is specified)")
    # Hack: argparse doesn't let you use choices and nargs=* on a positional argument
    parser.add_argument("compositors", choices=sorted(compositors.keys()) + [[]], nargs="*",
                        help="Specify the compositors to apply to the provided scene (additional arguments are determined after this is specified)")
    # don't include the help flag
    argv_without_help = [x for x in argv if x not in ["-h", "--help"]]
    args, remaining_args = parser.parse_known_args(argv_without_help)
    glue_name = args.frontend + "2" + args.backend
    LOG = logging.getLogger(glue_name)

    # load the actual components we need
    farg_func = get_frontend_argument_func(args.frontend)
    fcls = get_frontend_class(args.frontend)
    barg_func = get_backend_argument_func(args.backend)
    bcls = get_backend_class(args.backend)

    # add_frontend_arguments(parser)
    subgroup_titles = []
    subgroup_titles += farg_func(parser)
    subgroup_titles += add_remap_argument_groups(parser)
    subgroup_titles += barg_func(parser)
    compositor_classes = {}
    for c in args.compositors:
        carg_func = get_compositor_argument_func(compositors, c)
        ccls = get_compositor_class(compositors, c)
        compositor_classes[c] = ccls

        # add_frontend_arguments(parser)
        subgroup_titles += carg_func(parser)

    parser.add_argument('-f', dest='data_files', nargs="+", default=[], action=ExtendAction,
                        help="List of files or directories to extract data from")
    parser.add_argument('-d', dest='data_files', nargs="+", default=[], action=ExtendAction,
                        help="Data directories to look for input data files (equivalent to -f)")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(argv, global_keywords=global_keywords, subgroup_titles=subgroup_titles)

    if not args.data_files:
        # FUTURE: When the -d flag is removed this won't be needed because -f will be required
        parser.print_usage()
        parser.exit(1, "ERROR: No data files provided (-f flag)\n")

    # Logs are renamed once data the provided start date is known
    rename_log = False
    if args.log_fn is None:
        rename_log = True
        args.log_fn = glue_name + "_fail.log"
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)
    LOG.debug("Starting script with arguments: %s", " ".join(sys.argv))

    # Keep track of things going wrong to tell the user what went wrong (we want to create as much as possible)
    status_to_return = STATUS_SUCCESS

    # Frontend
    try:
        LOG.info("Initializing swath extractor...")
        list_products = args.subgroup_args["Frontend Initialization"].pop("list_products")
        f = fcls(search_paths=args.data_files, **args.subgroup_args["Frontend Initialization"])
    except StandardError:
        LOG.debug("Frontend exception: ", exc_info=True)
        LOG.error("%s frontend failed to load and sort data files (see log for details)", args.frontend)
        return STATUS_FRONTEND_FAIL

    # Rename the log file
    if rename_log:
        rename_log_file(glue_name + f.begin_time.strftime("_%Y%m%d_%H%M%S.log"))

    if list_products:
        print("\n".join(sorted(f.available_product_names)))
        return STATUS_SUCCESS

    try:
        LOG.info("Initializing remapping...")
        remapper = Remapper(**args.subgroup_args["Remapping Initialization"])
        remap_kwargs = args.subgroup_args["Remapping"]
    except StandardError:
        LOG.debug("Remapping initialization exception: ", exc_info=True)
        LOG.error("Remapping initialization failed (see log for details)")
        return STATUS_REMAP_FAIL

    try:
        LOG.info("Initializing backend...")
        backend = bcls(**args.subgroup_args["Backend Initialization"])
    except StandardError:
        LOG.debug("Backend initialization exception: ", exc_info=True)
        LOG.error("Backend initialization failed (see log for details)")
        return STATUS_BACKEND_FAIL

    try:
        compositor_objects = {}
        for c, ccls in compositor_classes.items():
            compositor_objects[c] = ccls(**args.subgroup_args[c + " Initialization"])
    except StandardError:
        LOG.debug("Compositor initialization exception: ", exc_info=True)
        LOG.error("Compositor initialization failed (see log for details)")
        return STATUS_COMP_FAIL

    try:
        LOG.info("Extracting swaths from data files available...")
        scene = f.create_scene(**args.subgroup_args["Frontend Swath Extraction"])
        if not scene:
            LOG.error("No products were returned by the frontend")
            raise RuntimeError("No products were returned by the frontend")
        if args.keep_intermediate:
            filename = glue_name + "_swath_scene.json"
            LOG.info("Saving intermediate swath scene as '%s'", filename)
            scene.save(filename)
    except StandardError:
        LOG.debug("Frontend data extraction exception: ", exc_info=True)
        LOG.error("Frontend data extraction failed (see log for details)")
        return STATUS_FRONTEND_FAIL

    # What grids should we remap to (the user should tell us or the backend should have a good set of defaults)
    known_grids = backend.known_grids
    LOG.debug("Backend known grids: %r", known_grids)
    grids = remap_kwargs.pop("forced_grids", None)
    LOG.debug("Forced Grids: %r", grids)
    if not grids and not known_grids:
        # the user didn't ask for any grids and the backend doesn't have specific defaults
        LOG.error("No grids specified and no known defaults")
        return STATUS_GDETER_FAIL
    elif not grids:
        # the user didn't tell us what to do, so let's try everything the backend knows how to do
        grids = known_grids
    elif known_grids is not None:
        # the user told us what to do, let's make sure the backend can do it
        grids = list(set(grids) & set(known_grids))
        if not grids:
            LOG.error("%s backend doesn't know how to handle any of the grids specified", args.backend)
            return STATUS_GDETER_FAIL
    LOG.debug("Grids that will be mapped to: %r", grids)

    # Remap
    gridded_scenes = {}
    for grid_name in grids:
        try:
            LOG.info("Remapping to grid %s", grid_name)
            gridded_scene = remapper.remap_scene(scene, grid_name, **remap_kwargs)
            gridded_scenes[grid_name] = gridded_scene
            if args.keep_intermediate:
                filename = glue_name + "_gridded_scene_" + grid_name + ".json"
                LOG.debug("saving intermediate gridded scene as '%s'", filename)
                gridded_scene.save(filename)
        except StandardError:
            LOG.debug("Remapping data exception: ", exc_info=True)
            LOG.error("Remapping data failed")
            status_to_return |= STATUS_REMAP_FAIL
            if args.exit_on_error:
                return status_to_return
            continue

        # Composition
        for c, comp in compositor_objects.items():
            try:
                LOG.info("Running gridded scene through '%s' compositor", c)
                gridded_scene = comp.modify_scene(gridded_scene, **args.subgroup_args[c + " Modification"])
                if args.keep_intermediate:
                    filename = glue_name + "_gridded_scene_" + grid_name + ".json"
                    LOG.debug("Updating saved intermediate gridded scene (%s) after compositor", filename)
                    gridded_scene.save(filename)
            except StandardError:
                LOG.debug("Compositor Error: ", exc_info=True)
                LOG.error("Could not properly modify scene using compositor '%s'" % (c,))
                if args.exit_on_error:
                    raise RuntimeError("Could not properly modify scene using compositor '%s'" % (c,))

        # Backend
        try:
            LOG.info("Creating output from data mapped to grid %s", grid_name)
            backend.create_output_from_scene(gridded_scene, **args.subgroup_args["Backend Output Creation"])
        except StandardError:
            LOG.debug("Backend output creation exception: ", exc_info=True)
            LOG.error("Backend output creation failed (see log for details)")
            status_to_return |= STATUS_BACKEND_FAIL
            if args.exit_on_error:
                return status_to_return
            continue

        LOG.info("Processing data for grid %s complete", grid_name)

    return status_to_return

if __name__ == "__main__":
    sys.exit(main())
