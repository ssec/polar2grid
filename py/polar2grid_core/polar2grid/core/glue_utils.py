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

import os
import sys
import logging
import argparse
from collections import defaultdict
from glob import glob

LOG = logging.getLogger(__name__)


def setup_logging(console_level=logging.INFO, log_filename="polar2grid.log"):
    """Setup the logger to the console to the logging level defined in the
    command line (default INFO).  Sets up a file logging for everything,
    regardless of command line level specified.  Adds extra logger for
    tracebacks to go to the log file if the exception is caught.  See
    `exc_handler` for more information.

    :Keywords:
        console_level : int
            Python logging level integer (ex. logging.INFO).
    """
    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.DEBUG)

    # Console output is minimal
    console = logging.StreamHandler(sys.stderr)
    console_format = "%(levelname)-8s : %(message)s"
    console.setFormatter(logging.Formatter(console_format))
    console.setLevel(console_level)
    root_logger.addHandler(console)

    # Log file messages have a lot more information
    if log_filename:
        file_handler = logging.FileHandler(log_filename)
        file_format = "[%(asctime)s] : PID %(process)6d : %(levelname)-8s : %(name)s : %(funcName)s : %(message)s"
        file_handler.setFormatter(logging.Formatter(file_format))
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)

        # Make a traceback logger specifically for adding tracebacks to log file
        traceback_log = logging.getLogger('traceback')
        traceback_log.propagate = False
        traceback_log.setLevel(logging.ERROR)
        traceback_log.addHandler(file_handler)


def rename_log_file(new_filename):
    """Rename the file handler for the root logger and the traceback logger.
    """
    # the traceback logger only has 1 handler so let's get that
    traceback_log = logging.getLogger('traceback')
    if not traceback_log.handlers:
        LOG.error("Tried to change the log filename, but no log file was configured")
        raise RuntimeError("Tried to change the log filename, but no log file was configured")

    h = traceback_log.handlers[0]
    fn = h.baseFilename
    h.stream.close()
    root_logger = logging.getLogger('')
    root_logger.removeHandler(h)
    traceback_log.removeHandler(h)

    # move the old file
    if os.path.isfile(new_filename):
        with open(new_filename, 'a') as new_file:
            with open(fn, 'r') as old_file:
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


def create_exc_handler(glue_name):
    def exc_handler(exc_type, exc_value, traceback):
        """An execption handler/hook that will only be called if an exception
        isn't called.  This will save us from print tracebacks or unrecognizable
        errors to the user's console.

        Note, however, that this doesn't effect code in a separate process as the
        exception never gets raised in the parent.
        """
        logging.getLogger(glue_name).error(exc_value)
        tb_log = logging.getLogger('traceback')
        if tb_log.handlers:
            tb_log.error(exc_value, exc_info=(exc_type, exc_value, traceback))
    return exc_handler


def _force_symlink(dst, linkname):
    """Create a symbolic link named `linkname` pointing to `dst`.  If the
    symbolic link already exists, remove it and create the new one.

    :Parameters:
        dst : str
            Filename to be pointed to.
        linkname : str
            Filename of the symbolic link being created or overwritten.
    """
    if os.path.exists(linkname):
        LOG.info("Removing old file %s" % linkname)
        os.remove(linkname)
    LOG.debug("Symlinking %s -> %s" % (linkname, dst))
    os.symlink(dst, linkname)


def _safe_remove(fn):
    """Remove the file `fn` if you can, if not log an error message,
    but continue on.

    :Parameters:
        fn : str
            Filename of the file to be removed.
    """
    try:
        LOG.info("Removing %s" % fn)
        os.remove(fn)
    except StandardError:
        LOG.error("Could not remove %s" % fn)


def remove_file_patterns(*args):
    """Remove as many of the possible files that were created from a previous
    run of a glue script, including temporary files, that may conflict with
    future processing.

    """
    for pat_list in args:
        for pat in pat_list:
            for f in glob(pat):
                _safe_remove(f)


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
        subgroup_titles = kwargs.pop("subgroup_titles", [])
        args = super(ArgumentParser, self).parse_args(*args, **kwargs)
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
            args.subgroup_args[subgroup_title] = subgroup_args

        return args


def create_basic_parser(*args, **kwargs):
    parser = ArgumentParser(*args, **kwargs)
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
                        help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument('-l', '--log', dest="log_fn", default=None,
                        help="specify the log filename")
    #parser.add_argument('--keep-intermediate', dest="keep_intermediate", default=False,
    parser.add_argument('--debug', dest="keep_intermediate", default=False,
                        action='store_true',
                        help="Keep intermediate files for future use.")
    # parser.add_argument('--debug', dest="debug_mode", default=False,
    #                     action='store_true',
    #                     help="Enter debug mode. Keeping intermediate files.")
    return parser
