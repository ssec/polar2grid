#!/usr/bin/env python
# encoding: utf-8
"""
Read one or more contiguous in-order HDF4 VIIRS or MODIS corrected reflectance product
granules and aggregate them into one swath per band.  Return a dictionary of meta data.
Write out Swath binary files used by other polar2grid components.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from polar2grid.core import roles
from polar2grid.core.fbf import file_appender
from .guidebook import get_file_info,get_nav_info

import os
import sys
import logging

log = logging.getLogger(__name__)

class Frontend(roles.FrontendRole):
    def __init__(self):
        pass

    def get_file_infos(self, filepaths):
        file_infos = []
        # use a dictionary to sanity check that the same nav file isn't used
        # for multiple data files
        nav_infos = {}
        for fp in filepaths:
            file_info = get_file_info(fp)
            file_infos.append(fp)

            if file_info["nav_filepath"] in nav_infos:
                msg = "File '%s' uses a navigation file that was used previously: '%s'" % (fp,file_info["nav_filepath"])
                log.error(msg)
                raise ValueError(msg)
            nav_info = get_nav_info(file_info["nav_filepath"])
            nav_infos[file_info["nav_filepath"]] = nav_info
            file_info["nav_info"] = nav_info

    def create_binary_files(self, file_infos):
        pass

    def make_swaths(self, filepaths, cut_bad=False):
        """Create binary swath files and return a python dictionary
        of meta data.
        """
        file_infos = self.get_file_infos(filepaths)

        meta_data = self.create_binary_files(file_infos)

        return meta_data

def main():
    from argparse import ArgumentParser
    import json
    description = """Run crefl frontend on files provided, writing JSON-ified
    meta data dictionary to stdout.
    """
    parser = ArgumentParser(description=description)
    parser.add_argument('cref_files',
            help="crefl output files for one contiguous swath/pass")

    args = parser.parse_args()

    frontend = Frontend()
    meta_data = frontend.make_swaths(args.crefl_files)

    print json.dumps(meta_data)

if __name__ == "__main__":
    sys.exit(main())

