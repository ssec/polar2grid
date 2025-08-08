#!/usr/bin/env python3
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
# Written by David Hoese    September 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Helper functions and classes used by multiple polar2grid scripts.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Sept 2014
:license:      GNU GPLv3


"""

__docformat__ = "restructuredtext en"

import argparse
import logging
import os
import sys
from collections import defaultdict

LOG = logging.getLogger(__name__)


# class SatPyWarningFilter(logging.Formatter):
#     def format(self, record):
#         if record.name.startswith('satpy') and record.levelno == logging.WARNING:
#             record.levelno = logging.DEBUG
#             record.levelname = 'DEBUG'
#         return super(SatPyWarningFilter, self).format(record)


class SatPyWarningFilter(logging.Filter):
    def filter(self, record):
        is_satpy = record.name.startswith("satpy")
        is_msg = "The following datasets were not created and may require resampling" in record.msg
        return 0 if is_satpy and is_msg else 1


class ThirdPartyFilter(logging.Filter):
    def __init__(self, ignored_packages, level=logging.WARNING, name=""):
        self.ignored_packages = ignored_packages
        self.level_filter = level
        super(ThirdPartyFilter, self).__init__(name)

    def filter(self, record):
        for pkg in self.ignored_packages:
            if record.name.startswith(pkg) and record.levelno < self.level_filter:
                return 0
        return 1


def setup_logging(console_level=logging.INFO, log_filename="polar2grid.log", log_numpy=True):
    """Set up the logger to the console to the logging level defined in the command line (default INFO).

    Sets up a file logging for everything,
    regardless of command line level specified.  Adds extra logger for
    tracebacks to go to the log file if the exception is caught.  See
    `exc_handler` for more information.

    :param console_level: Python logging level integer (ex. logging.INFO).
    :param log_filename: Log messages to console and specified log_filename (None for no file log)
    :param log_numpy: Tell numpy to log invalid values encountered
    """
    # set the root logger to DEBUG so that handlers can have all possible messages to filter
    root_logger = logging.getLogger("")
    root_logger.setLevel(min(console_level, logging.DEBUG))

    # Console output is minimal
    console = logging.StreamHandler(sys.stderr)
    console_format = "%(levelname)-8s : %(message)s"
    console.setFormatter(logging.Formatter(console_format))
    console.setLevel(console_level)
    console.addFilter(SatPyWarningFilter())
    if console_level > logging.DEBUG:
        # if we are only showing INFO/WARNING/ERROR messages for P2G then
        # filter out messages from these packages
        console.addFilter(
            ThirdPartyFilter(["satpy", "pyresample", "pyspectral", "trollimage", "pyorbital", "trollsift"])
        )
    root_logger.addHandler(console)

    # Log file messages have a lot more information
    if log_filename:
        file_handler = logging.FileHandler(log_filename)
        file_format = "[%(asctime)s] : %(levelname)-8s : %(name)s : %(funcName)s : %(message)s"
        file_handler.setFormatter(logging.Formatter(file_format))
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)

        # Make a traceback logger specifically for adding tracebacks to log file
        traceback_log = logging.getLogger("traceback")
        traceback_log.propagate = False
        traceback_log.setLevel(logging.ERROR)
        traceback_log.addHandler(file_handler)

    if log_numpy:
        import numpy

        class TempLog(object):
            def write(self, msg):
                logging.getLogger("numpy").debug(msg)

        numpy.seterr(invalid="log")
        numpy.seterrcall(TempLog())


def rename_log_file(new_filename):
    """Rename the file handler for the root logger and the traceback logger."""
    # the traceback logger only has 1 handler so let's get that
    traceback_log = logging.getLogger("traceback")
    if not traceback_log.handlers:
        LOG.error("Tried to change the log filename, but no log file was configured")
        raise RuntimeError("Tried to change the log filename, but no log file was configured")

    h = traceback_log.handlers[0]
    fn = h.baseFilename
    h.stream.close()
    root_logger = logging.getLogger("")
    root_logger.removeHandler(h)
    traceback_log.removeHandler(h)

    # move the old file
    if os.path.isfile(new_filename):
        with open(new_filename, "a") as new_file:
            with open(fn, "r") as old_file:
                new_file.write(old_file.read())
        os.remove(fn)
    else:
        os.rename(fn, new_filename)

    # create the new handler
    file_handler = logging.FileHandler(new_filename)
    file_format = "[%(asctime)s] : PID %(process)6d : %(levelname)-8s : %(name)s : %(funcName)s : %(message)s"
    file_handler.setFormatter(logging.Formatter(file_format))
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    traceback_log.addHandler(file_handler)

    LOG.debug("Log renamed from '%s' to '%s'", fn, new_filename)


def create_exc_handler(glue_name):
    def exc_handler(exc_type, exc_value, traceback):
        """Handle logging/printing an exception if it occurs.

        This will save us from print tracebacks or unrecognizable errors to the user's console.

        Note, however, that this doesn't effect code in a separate process as the
        exception never gets raised in the parent.
        """
        logging.getLogger(glue_name).error(
            "Unexpected error. Enable debug messages (-vvv) or see log file for details."
        )
        logging.getLogger(glue_name).debug("Unexpected error exception: ", exc_info=(exc_type, exc_value, traceback))
        tb_log = logging.getLogger("traceback")
        if tb_log.handlers:
            tb_log.error(exc_value, exc_info=(exc_type, exc_value, traceback))

    return exc_handler


class NumpyDtypeList(list):
    """Magic list to allow dtype objects to match string versions of themselves."""

    def __contains__(self, item):
        if super(NumpyDtypeList, self).__contains__(item):
            return True
        try:
            return super(NumpyDtypeList, self).__contains__(item().dtype.name)
        except AttributeError:
            return False


class ExtendAction(argparse.Action):
    """Similar to the 'append' action, but expects multiple elements instead of just one."""

    def __call__(self, parser, namespace, values, option_string=None):
        current_values = getattr(namespace, self.dest, []) or []
        current_values.extend(values)
        setattr(namespace, self.dest, current_values)


class ExtendConstAction(argparse.Action):
    """Similar to the 'append' action, but expects multiple elements instead of just one."""

    def __init__(self, option_strings, dest, nargs=0, **kwargs):
        if nargs:
            raise ValueError("nargs is not allowed")
        super(ExtendConstAction, self).__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        current_values = getattr(namespace, self.dest, []) or []
        current_values.extend(self.const)
        setattr(namespace, self.dest, current_values)


class BooleanFilterAction(argparse.BooleanOptionalAction):
    """Action to add or not add a filter string to a list of filters."""

    def __init__(self, option_strings, dest, const: str, **kwargs):
        super().__init__(option_strings, dest, **kwargs)
        self.const = const

    def __call__(self, parser, namespace, values, option_string=None):
        if option_string in self.option_strings:
            prev = getattr(namespace, self.dest, None)
            if prev is None:
                prev = []
                setattr(namespace, self.dest, prev)

            should_include = not option_string.startswith("--no-")
            has_const = self.const in prev
            # modify list inplace
            if should_include and not has_const:
                prev.append(self.const)
            elif not should_include and has_const:
                prev.remove(self.const)


class ArgumentParser(argparse.ArgumentParser):
    def _get_group_actions(self, group):
        """Get all the options/actions in a group including those from subgroups of the provided group.

        .. note::

            This does not group the subgroup options as their own dictionaries.

        """
        these_actions = [action for action in group._group_actions]
        # get actions if this group has even more subgroups
        for subgroup in group._action_groups:
            these_actions += self._get_group_actions(subgroup)

        return these_actions

    def parse_args(self, *args, **kwargs):
        """Parse arguments to support custom polar2grid 'subgroup' behavior.

        :param subgroup_titles: Groups and their arguments that will be put
                                in a separate dictionary in the 'subgroup_args' attribute
        :param global_keywords: Keywords/arguments that should be added to all subgroup dictionaries
        """
        subgroup_titles = kwargs.pop("subgroup_titles", [])
        global_keywords = kwargs.pop("global_keywords", [])
        args = super(ArgumentParser, self).parse_args(*args, **kwargs)
        args.global_kwargs = {kw: getattr(args, kw) for kw in global_keywords}
        # a dictionary that holds arguments from the specified subgroups (defaultdict for easier user by caller)
        args.subgroup_args = defaultdict(dict)
        for subgroup_title in subgroup_titles:
            try:
                subgroup = [x for x in self._action_groups if x.title == subgroup_title][0]
            except IndexError:
                # we don't have any loggers configured at this point
                print("WARNING: Couldn't find argument group '%s' in configured parser" % (subgroup_title,))
                continue

            subgroup_args = {}
            for action in self._get_group_actions(subgroup):
                if hasattr(args, action.dest):
                    subgroup_args[action.dest] = getattr(args, action.dest)
                    delattr(args, action.dest)

            # Add 'global' arguments
            for kw in global_keywords:
                if hasattr(args, kw):
                    subgroup_args[kw] = getattr(args, kw)

            args.subgroup_args[subgroup_title] = subgroup_args

        return args


def create_basic_parser(*args, **kwargs):
    parser = ArgumentParser(*args, **kwargs)
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="count",
        default=0,
        help="each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG-TRACE (default INFO)",
    )
    parser.add_argument("-l", "--log", dest="log_fn", default=None, help="specify the log filename")
    parser.add_argument(
        "--debug",
        dest="keep_intermediate",
        default=False,
        action="store_true",
        help="Keep intermediate files for future use.",
    )
    parser.add_argument(
        "--overwrite",
        dest="overwrite_existing",
        action="store_true",
        help="Overwrite intermediate or output files if they exist already",
    )
    parser.add_argument(
        "--exit-on-error",
        dest="exit_on_error",
        action="store_true",
        help="exit on first error including non-fatal errors",
    )
    return parser
