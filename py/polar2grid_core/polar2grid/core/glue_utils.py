#!/usr/bin/env python
# encoding: utf-8
"""Functions used by multiple glue scripts.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3

Copyright (C) 2013 Space Science and Engineering Center (SSEC),
 University of Wisconsin-Madison.

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

    Written by David Hoese    January 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

import os
import sys
import logging
from glob import glob

log = logging.getLogger(__name__)

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
    file_handler = logging.FileHandler(log_filename)
    file_format = "[%(asctime)s] : %(levelname)-8s : %(name)s : %(funcName)s : %(message)s"
    file_handler.setFormatter(logging.Formatter(file_format))
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # Make a traceback logger specifically for adding tracebacks to log file
    traceback_log = logging.getLogger('traceback')
    traceback_log.propagate = False
    traceback_log.setLevel(logging.ERROR)
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
        logging.getLogger('traceback').error(exc_value, exc_info=(exc_type,exc_value,traceback))
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
        log.info("Removing old file %s" % linkname)
        os.remove(linkname)
    log.debug("Symlinking %s -> %s" % (linkname,dst))
    os.symlink(dst, linkname)

def _safe_remove(fn):
    """Remove the file `fn` if you can, if not log an error message,
    but continue on.

    :Parameters:
        fn : str
            Filename of the file to be removed.
    """
    try:
        log.info("Removing %s" % fn)
        os.remove(fn)
    except StandardError:
        log.error("Could not remove %s" % fn)


def remove_file_patterns(*args):
    """Remove as many of the possible files that were created from a previous
    run of a glue script, including temporary files, that may conflict with
    future processing.

    """
    for pat_list in args:
        for pat in pat_list:
            for f in glob(pat):
                _safe_remove(f)
