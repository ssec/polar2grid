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

import sys

import logging
import os
import pkg_resources
from ConfigParser import SafeConfigParser, Error as ConfigParserError
from StringIO import StringIO
from pkg_resources import resource_string as get_resource_string

LOG = logging.getLogger(__name__)

DEFAULT_COMP_CONFIG = os.getenv("P2G_COMP_CONFIG", "polar2grid.compositors:compositors.ini")
P2G_COMP_CLS_EP = "polar2grid.compositor_class"
P2G_COMP_ARGS_EP = "polar2grid.compositor_arguments"


class CompositorManager(dict):
    def __init__(self, config_files=None, **kwargs):
        self.section_prefix = kwargs.get("section_prefix", "compositor:")
        self.config_files = config_files or (DEFAULT_COMP_CONFIG,)
        file_objs = set([f for f in self.config_files if not isinstance(f, (str, unicode))])
        filepaths = set([f for f in self.config_files if isinstance(f, (str, unicode))])

        self.config_parser = SafeConfigParser(kwargs, allow_no_value=True)
        if file_objs:
            for fp in file_objs:
                self.config_parser.readfp(fp)
        else:
            for fp in filepaths:
                fo = self.open_config_file(fp)
                try:
                    self.config_parser.readfp(fo, fp)
                except ConfigParserError:
                    LOG.warning("Could not parse config file: %s", fp)

        self.load_config()
        if not self:
            LOG.error("No valid configuration sections found with prefix '%s'", self.section_prefix)
            raise ValueError("No valid configuration sections found")

        self.find_compositor_classes()

    def open_config_file(self, config_file):
        """Load one configuration file into internal storage.

        If the config_file is a relative path string and can't be found it
        will be loaded from a package relative location. If it can't be found
        in the package an exception is raised.
        """
        # If we were provided a string filepath then open the file
        if isinstance(config_file, str):
            if not os.path.isabs(config_file):
                # Its not an absolute path, lets see if its relative path
                cwd_config = os.path.join(os.path.curdir, config_file)
                if os.path.exists(cwd_config):
                    config_file = cwd_config
                    config_file = open(config_file, 'r')
                else:
                    # they have specified a package provided file
                    LOG.debug("Loading package provided configuration file: '%s'" % (config_file,))
                    try:
                        parts = config_file.split(":")
                        mod_part, file_part = parts if len(parts) == 2 else ("", parts[0])
                        mod_part = mod_part or self.__module__
                        config_str = get_resource_string(mod_part, file_part)
                    except StandardError:
                        LOG.error("Configuration file '%s' was not found" % (config_file,))
                        raise
                    config_file = StringIO(config_str)
            else:
                config_file = open(config_file, 'r')
        return config_file

    def load_config(self):
        for section in self.config_parser.sections():
            if self.section_prefix and not section.startswith(self.section_prefix):
                continue

            compositor_name = ":".join(section.split(":")[1:])
            self[compositor_name] = dict((k, self.config_parser.get(section, k)) for k in self.config_parser.options(section))

            if "compositor_class" not in self[compositor_name]:
                raise RuntimeError("Invalid compositor configuration section for '%s'" % (compositor_name,))

    def find_compositor_classes(self):
        self.comp_classes = available_compositors()

    def load_compositor_class(self, name):
        return get_compositor_class(self.comp_classes, name)

    def get_compositor(self, name, **other_kwargs):
        if name not in self:
            return KeyError("Compositor '%s' does not exist in configuration file" % (name,))

        kwargs = self[name].copy()
        kwargs.update(other_kwargs)
        comp_cls_name = kwargs.pop("compositor_class")
        comp_cls = self.load_compositor_class(comp_cls_name)

        LOG.debug("Initializing compositor '%s' with %r", name, kwargs)
        return comp_cls(**kwargs)

    def create_compositor(self, name):
        pass


def available_compositors(entry_point=P2G_COMP_CLS_EP):
    """Don't load this unless it needs to be used (via main or via glue.py).
    """
    return {frontend_ep.name: frontend_ep.dist for frontend_ep in pkg_resources.iter_entry_points(entry_point)}


def get_compositor_class(compositors, name):
    """Get the named compositor's class object.

    :param compositors: dictionary returned by `available_compositors`
    :param name: name of the compositor as defined in the entry point
    """
    return pkg_resources.load_entry_point(compositors[name], P2G_COMP_CLS_EP, name)


def main(argv=sys.argv[1:]):
    from polar2grid.core import setup_logging, create_basic_parser, create_exc_handler
    from polar2grid.core import GriddedScene
    parser = create_basic_parser(description="Extract swath data, remap it, and write it to a new file format")
    parser.add_argument("--compositor-configs", nargs="*", default=None,
                        help="Specify alternative configuration file(s) for compositors")
    # don't include the help flag
    argv_without_help = [x for x in argv if x not in ["-h", "--help"]]
    args, remaining_args = parser.parse_known_args(argv_without_help)

    # Load compositor information (we can't know the compositor choices until we've loaded the configuration)
    compositor_manager = CompositorManager(config_files=args.compositor_configs)
    # Hack: argparse doesn't let you use choices and nargs=* on a positional argument
    parser.add_argument("compositors", choices=compositor_manager.keys() + [[]], nargs="*",
                        help="Specify the compositors to apply to the provided scene (additional arguments are determined after this is specified)")
    parser.add_argument("--scene", required=True, help="JSON SwathScene filename to be remapped")
    parser.add_argument("-o", dest="output_filename",
                        help="Specify the filename for the newly modified scene (default: original_fn + 'composite')")
    global_keywords = ("keep_intermediate", "overwrite_existing", "exit_on_error")
    args = parser.parse_args(argv, global_keywords=global_keywords)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)
    LOG.debug("Starting compositor script with arguments: %s", " ".join(sys.argv))

    # Compositor validation
    compositor_objects = {}
    for c in args.compositors:
        if c not in compositor_manager:
            LOG.error("Compositor '%s' is unknown" % (c,))
            raise RuntimeError("Compositor '%s' is unknown" % (c,))
        compositor_objects[c] = compositor_manager.get_compositor(c, **args.global_kwargs)

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